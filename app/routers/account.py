"""Account management router for customer self-service (Phase 4)."""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models import Customer, AccountDeletionRequest, Claim, RefreshToken
from app.schemas.account_schemas import (
    EmailChangeRequest,
    PasswordChangeRequest,
    AccountDeletionRequestSchema,
    AccountInfoResponse,
    MessageResponse
)
from app.services.auth_service import AuthService
from app.tasks.account_tasks import (
    send_email_change_notification,
    send_password_change_notification,
    send_account_deletion_request_notification,
    send_account_deletion_admin_notification
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["Account Management"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


@router.get(
    "/info",
    response_model=AccountInfoResponse,
    summary="Get account information",
    description="Retrieve current account information including creation date and last login."
)
async def get_account_info(
    current_user: Customer = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """Get current user's account information."""
    # Count total claims
    result = await session.execute(
        select(func.count(Claim.id)).where(Claim.customer_id == current_user.id)
    )
    total_claims = result.scalar() or 0

    return AccountInfoResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone=current_user.phone,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
        is_email_verified=current_user.is_email_verified,
        total_claims=total_claims,
        has_password=current_user.password_hash is not None
    )


@router.put(
    "/email",
    response_model=MessageResponse,
    summary="Change email address",
    description="Update account email address. Requires current password for verification. "
                "Invalidates all existing tokens and requires re-login."
)
async def change_email(
    data: EmailChangeRequest,
    request: Request,
    current_user: Customer = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """Change user's email address."""
    # Verify current password
    if not AuthService.verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Check if new email is already taken
    result = await session.execute(
        select(Customer).where(Customer.email == data.new_email)
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already in use"
        )

    # Store old email for notification
    old_email = current_user.email

    # Update email
    current_user.email = data.new_email
    current_user.is_email_verified = False  # Require re-verification
    current_user.updated_at = datetime.now(timezone.utc)

    # Invalidate all refresh tokens (force re-login on all devices)
    await session.execute(
        select(RefreshToken)
        .where(RefreshToken.user_id == current_user.id)
        .where(RefreshToken.revoked_at.is_(None))
    )
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == current_user.id)
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.revoked_at = datetime.now(timezone.utc)

    await session.commit()

    # Send notification emails
    send_email_change_notification.delay(
        old_email=old_email,
        new_email=data.new_email,
        user_name=current_user.full_name
    )

    logger.info(f"User {current_user.id} changed email from {old_email} to {data.new_email}")

    return MessageResponse(
        message="Email address updated successfully. Please verify your new email and log in again."
    )


@router.put(
    "/password",
    response_model=MessageResponse,
    summary="Change password",
    description="Update account password. Requires current password for verification. "
                "Invalidates all refresh tokens and requires re-login on all devices."
)
async def change_password(
    data: PasswordChangeRequest,
    request: Request,
    current_user: Customer = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """Change user's password."""
    # Verify current password
    if not AuthService.verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Validate new password strength
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Hash new password
    new_password_hash = AuthService.hash_password(data.new_password)
    current_user.password_hash = new_password_hash
    current_user.updated_at = datetime.now(timezone.utc)

    # Invalidate all refresh tokens (force re-login on all devices)
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == current_user.id)
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.revoked_at = datetime.now(timezone.utc)

    await session.commit()

    # Send notification email
    send_password_change_notification.delay(
        email=current_user.email,
        user_name=current_user.full_name
    )

    logger.info(f"User {current_user.id} changed their password")

    return MessageResponse(
        message="Password updated successfully. Please log in again with your new password."
    )


@router.post(
    "/delete-request",
    response_model=MessageResponse,
    summary="Request account deletion",
    description="Submit a request to delete your account. Your account will be blacklisted "
                "immediately (preventing login), and admins will be notified to manually "
                "review and process the deletion. This allows for proper handling of open "
                "claims and GDPR compliance."
)
async def request_account_deletion(
    data: AccountDeletionRequestSchema,
    request: Request,
    current_user: Customer = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """Request account deletion (blacklist approach for GDPR compliance)."""
    # Check if there's already a pending deletion request
    result = await session.execute(
        select(AccountDeletionRequest)
        .where(AccountDeletionRequest.customer_id == current_user.id)
        .where(AccountDeletionRequest.status == AccountDeletionRequest.STATUS_PENDING)
    )
    existing_request = result.scalar_one_or_none()
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending account deletion request"
        )

    # Count claims
    result = await session.execute(
        select(func.count(Claim.id))
        .where(Claim.customer_id == current_user.id)
    )
    total_claims = result.scalar() or 0

    result = await session.execute(
        select(func.count(Claim.id))
        .where(Claim.customer_id == current_user.id)
        .where(Claim.status.in_([
            Claim.STATUS_SUBMITTED,
            Claim.STATUS_UNDER_REVIEW,
            Claim.STATUS_APPROVED
        ]))
    )
    open_claims = result.scalar() or 0

    # Blacklist the account immediately (prevents login)
    current_user.is_blacklisted = True
    current_user.blacklisted_at = datetime.now(timezone.utc)
    current_user.deletion_requested_at = datetime.now(timezone.utc)
    current_user.deletion_reason = data.reason

    # Create deletion request for admin review
    deletion_request = AccountDeletionRequest(
        customer_id=current_user.id,
        email=current_user.email,
        reason=data.reason,
        open_claims_count=open_claims,
        total_claims_count=total_claims,
        status=AccountDeletionRequest.STATUS_PENDING
    )
    session.add(deletion_request)

    # Invalidate all refresh tokens
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == current_user.id)
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.revoked_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(deletion_request)

    # Send notifications
    send_account_deletion_request_notification.delay(
        email=current_user.email,
        user_name=current_user.full_name,
        deletion_request_id=str(deletion_request.id)
    )

    send_account_deletion_admin_notification.delay(
        customer_email=current_user.email,
        customer_name=current_user.full_name,
        customer_id=str(current_user.id),
        reason=data.reason or "No reason provided",
        open_claims_count=open_claims,
        total_claims_count=total_claims,
        deletion_request_id=str(deletion_request.id)
    )

    logger.info(
        f"User {current_user.id} requested account deletion. "
        f"Open claims: {open_claims}, Total claims: {total_claims}"
    )

    return MessageResponse(
        message="Account deletion request submitted successfully. Your account has been "
                "deactivated and you can no longer log in. Our team will review your request "
                "and contact you if any open claims need to be resolved first."
    )
