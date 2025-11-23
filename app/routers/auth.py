"""Authentication router for user registration, login, and token management."""
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.database import get_db
from app.dependencies.auth import get_current_active_user, get_current_user
from app.models import Customer
from app.schemas.auth_schemas import (
    UserRegisterSchema,
    UserLoginSchema,
    TokenResponseSchema,
    RefreshTokenSchema,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema,
    PasswordChangeSchema,
    UserResponseSchema,
    AuthResponseSchema,
    MagicLinkRequestSchema,
)
from app.services.auth_service import AuthService
from app.tasks.claim_tasks import send_magic_link_login_email

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


@router.post(
    "/register",
    response_model=AuthResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password. Returns user info and authentication tokens."
)
async def register(
    data: UserRegisterSchema,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    - **email**: Valid email address (must be unique)
    - **password**: At least 12 characters with uppercase, lowercase, digit, and special character
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Optional phone number

    Returns user information and authentication tokens.
    """
    try:
        # Register user
        customer = await AuthService.register_user(
            session=session,
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone
        )

        # Get client info
        ip_address, user_agent = get_client_info(request)

        # Create access token
        access_token = AuthService.create_access_token(
            user_id=customer.id,
            email=customer.email,
            role=customer.role
        )

        # Create refresh token
        refresh_token_str, _ = await AuthService.create_refresh_token(
            session=session,
            user_id=customer.id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Commit transaction
        await session.commit()

        # Prepare response
        user_response = UserResponseSchema.model_validate(customer)
        token_response = TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=config.JWT_EXPIRATION_MINUTES * 60  # Convert to seconds
        )

        return AuthResponseSchema(user=user_response, tokens=token_response)

    except ValueError as e:
        await session.rollback()
        logger.error(f"Validation error during registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        # In development, show the actual error; in production, hide it
        is_development = os.getenv("ENVIRONMENT", "development") == "development"
        detail = str(e) if is_development else "An error occurred during registration"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.post(
    "/login",
    response_model=AuthResponseSchema,
    summary="Login with email and password",
    description="Authenticate with email and password. Returns user info and authentication tokens."
)
async def login(
    data: UserLoginSchema,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.

    - **email**: User's email address
    - **password**: User's password

    Returns user information and authentication tokens.
    """
    # Authenticate user
    customer = await AuthService.login_user(
        session=session,
        email=data.email,
        password=data.password
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get client info
    ip_address, user_agent = get_client_info(request)

    # Create access token
    access_token = AuthService.create_access_token(
        user_id=customer.id,
        email=customer.email,
        role=customer.role
    )

    # Create refresh token
    refresh_token_str, _ = await AuthService.create_refresh_token(
        session=session,
        user_id=customer.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    # Commit transaction (to save last_login_at update)
    await session.commit()

    # Prepare response
    user_response = UserResponseSchema.model_validate(customer)
    token_response = TokenResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        expires_in=config.JWT_EXPIRATION_MINUTES * 60  # Convert to seconds
    )

    return AuthResponseSchema(user=user_response, tokens=token_response)


@router.post(
    "/refresh",
    response_model=TokenResponseSchema,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token."
)
async def refresh_token(
    data: RefreshTokenSchema,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    Refresh access token.

    - **refresh_token**: Valid refresh token

    Returns new access and refresh tokens.
    """
    # Verify refresh token
    refresh_token_obj = await AuthService.verify_refresh_token(
        session=session,
        token=data.refresh_token
    )

    if not refresh_token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    from sqlalchemy import select
    stmt = select(Customer).where(Customer.id == refresh_token_obj.user_id)
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer or not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get client info
    ip_address, user_agent = get_client_info(request)

    # Create new access token
    access_token = AuthService.create_access_token(
        user_id=customer.id,
        email=customer.email,
        role=customer.role
    )

    # Create new refresh token
    new_refresh_token_str, _ = await AuthService.create_refresh_token(
        session=session,
        user_id=customer.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    # Revoke old refresh token (token rotation)
    await AuthService.revoke_refresh_token(
        session=session,
        token=data.refresh_token,
        replaced_by=new_refresh_token_str
    )

    # Commit transaction
    await session.commit()

    return TokenResponseSchema(
        access_token=access_token,
        refresh_token=new_refresh_token_str,
        token_type="bearer",
        expires_in=config.JWT_EXPIRATION_MINUTES * 60  # Convert to seconds
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke refresh token",
    description="Logout the current user and revoke their refresh token."
)
async def logout(
    data: RefreshTokenSchema,
    current_user: Customer = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Logout and revoke refresh token.

    - **refresh_token**: Refresh token to revoke

    Requires authentication (Bearer token in Authorization header).
    """
    # Revoke refresh token
    await AuthService.revoke_refresh_token(
        session=session,
        token=data.refresh_token
    )

    # Commit transaction
    await session.commit()

    return None


@router.post(
    "/magic-link/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request magic link login",
    description="Send a magic link to the user's email for passwordless login."
)
async def request_magic_link(
    data: MagicLinkRequestSchema,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    Request a magic link for passwordless login.

    Args:
        data: Email request data
        request: FastAPI request object
        session: Database session

    Returns:
        Success message (always returns success to prevent email enumeration)
    """
    from sqlalchemy import select

    # Always return success to prevent email enumeration
    # But only send email if user exists
    stmt = select(Customer).where(Customer.email == data.email)
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()

    if customer:
        # Get client info
        ip_address, user_agent = get_client_info(request)

        # Create magic link token (no claim_id for login-only magic links)
        magic_token, _ = await AuthService.create_magic_link_token(
            session=session,
            user_id=customer.id,
            claim_id=None,  # No claim associated
            ip_address=ip_address,
            user_agent=user_agent
        )

        await session.commit()

        # Send magic link email via Celery task
        try:
            send_magic_link_login_email.delay(
                customer_email=customer.email,
                customer_name=f"{customer.first_name} {customer.last_name}",
                magic_link_token=magic_token,
                ip_address=ip_address
            )
            logger.info(f"Magic link email task queued for user {customer.email}")
        except Exception as e:
            # Don't fail the request if email queueing fails
            logger.error(f"Failed to queue magic link email: {str(e)}")

    return {
        "message": "If an account exists with this email, a magic link has been sent"
    }


@router.post(
    "/magic-link/verify/{token}",
    response_model=AuthResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Verify magic link token",
    description="Verify a magic link token and return JWT tokens for authentication."
)
async def verify_magic_link(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    Verify magic link token and authenticate user.

    Args:
        token: Magic link token from email URL
        request: FastAPI request object
        session: Database session

    Returns:
        AuthResponseSchema with user info and JWT tokens

    Raises:
        HTTPException: 400 if token is invalid or expired
    """
    # Verify token
    result = await AuthService.verify_magic_link_token(
        session=session,
        token=token
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired magic link token"
        )

    customer, claim_id = result

    # Get client info
    ip_address, user_agent = get_client_info(request)

    # Generate JWT tokens (include claim_id if provided)
    access_token = AuthService.create_access_token(
        user_id=customer.id,
        email=customer.email,
        role=customer.role,
        claim_id=claim_id  # Pass claim_id for magic link access authorization
    )

    refresh_token_str, _ = await AuthService.create_refresh_token(
        session=session,
        user_id=customer.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    await session.commit()

    # Return auth response
    return AuthResponseSchema(
        user=UserResponseSchema.model_validate(customer),
        tokens=TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=config.JWT_EXPIRATION_MINUTES * 60
        )
    )


@router.post(
    "/password/reset-request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request password reset",
    description="Send a password reset email to the user."
)
async def request_password_reset(
    data: PasswordResetRequestSchema,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    Request password reset.

    - **email**: User's email address

    Sends a password reset email if the email exists. Always returns success
    to prevent email enumeration attacks.
    """
    # Get client info
    ip_address, user_agent = get_client_info(request)

    # Find user by email
    from sqlalchemy import select
    stmt = select(Customer).where(Customer.email == data.email)
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    # But only send email if user exists
    if customer:
        # Create password reset token
        token_str, _ = await AuthService.create_password_reset_token(
            session=session,
            user_id=customer.id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        await session.commit()

        # TODO: Send password reset email using email service
        # For now, we just create the token
        # In production, this would trigger an email with a reset link
        # email_service.send_password_reset_email(customer.email, token_str)

    return {
        "message": "If the email exists, a password reset link has been sent"
    }


@router.post(
    "/password/reset-confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset",
    description="Reset password using the reset token from email."
)
async def confirm_password_reset(
    data: PasswordResetConfirmSchema,
    session: AsyncSession = Depends(get_db)
):
    """
    Confirm password reset.

    - **token**: Password reset token from email
    - **new_password**: New password (at least 12 characters with requirements)

    Resets the password and invalidates all existing tokens.
    """
    try:
        # Reset password
        success = await AuthService.reset_password(
            session=session,
            token=data.token,
            new_password=data.new_password
        )

        if not success:
            raise ValueError("Password reset failed")

        # Commit transaction
        await session.commit()

        return {"message": "Password has been reset successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/password/change",
    status_code=status.HTTP_200_OK,
    summary="Change password (authenticated)",
    description="Change password for the currently authenticated user."
)
async def change_password(
    data: PasswordChangeSchema,
    current_user: Customer = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Change password for authenticated user.

    - **current_password**: User's current password
    - **new_password**: New password (at least 12 characters with requirements)

    Requires authentication. Invalidates all existing refresh tokens.
    """
    try:
        # Change password
        success = await AuthService.change_password(
            session=session,
            user_id=current_user.id,
            old_password=data.current_password,
            new_password=data.new_password
        )

        if not success:
            raise ValueError("Password change failed")

        # Commit transaction
        await session.commit()

        return {"message": "Password has been changed successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/me",
    response_model=UserResponseSchema,
    summary="Get current user info",
    description="Get information about the currently authenticated user."
)
async def get_current_user_info(
    current_user: Customer = Depends(get_current_active_user)
):
    """
    Get current user information.

    Requires authentication (Bearer token in Authorization header).
    """
    return UserResponseSchema.model_validate(current_user)


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Mark the current user's email as verified (placeholder for future email verification flow)."
)
async def verify_email(
    current_user: Customer = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Verify email address.

    Requires authentication (Bearer token in Authorization header).

    TODO: In production, this should require a verification token sent via email.
    For now, it's a simple endpoint to manually verify emails during testing.
    """
    # Verify email
    success = await AuthService.verify_email(
        session=session,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification failed"
        )

    # Commit transaction
    await session.commit()

    return {"message": "Email has been verified successfully"}
