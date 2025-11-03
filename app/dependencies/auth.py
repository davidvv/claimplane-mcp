"""Authentication dependencies for FastAPI endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Customer
from app.services.auth_service import AuthService


# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db)
) -> Customer:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials (Bearer token)
        session: Database session

    Returns:
        Customer instance of authenticated user

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    # Extract token
    token = credentials.credentials

    # Verify and decode token
    payload = AuthService.verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token
    try:
        user_id = UUID(payload.get("user_id"))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    stmt = select(Customer).where(Customer.id == user_id)
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return customer


async def get_current_active_user(
    current_user: Customer = Depends(get_current_user)
) -> Customer:
    """
    Get the current authenticated and active user.

    Args:
        current_user: Current user from get_current_user

    Returns:
        Customer instance if user is active

    Raises:
        HTTPException: 403 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return current_user


async def get_current_verified_user(
    current_user: Customer = Depends(get_current_active_user)
) -> Customer:
    """
    Get the current authenticated, active, and email-verified user.

    Args:
        current_user: Current user from get_current_active_user

    Returns:
        Customer instance if user is verified

    Raises:
        HTTPException: 403 if email is not verified
    """
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address."
        )

    return current_user


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control.

    Args:
        *allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function that checks user role

    Example:
        @app.get("/admin/dashboard", dependencies=[Depends(require_role("admin", "superadmin"))])
        async def admin_dashboard():
            ...
    """
    async def role_checker(
        current_user: Customer = Depends(get_current_active_user)
    ) -> Customer:
        """
        Check if current user has one of the required roles.

        Args:
            current_user: Current authenticated user

        Returns:
            Customer instance if user has required role

        Raises:
            HTTPException: 403 if user doesn't have required role
        """
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )

        return current_user

    return role_checker


# Convenience dependencies for common role checks
async def get_current_admin(
    current_user: Customer = Depends(require_role(Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN))
) -> Customer:
    """
    Get current user and verify they have admin or superadmin role.

    Args:
        current_user: Current user from role checker

    Returns:
        Customer instance with admin privileges
    """
    return current_user


async def get_current_superadmin(
    current_user: Customer = Depends(require_role(Customer.ROLE_SUPERADMIN))
) -> Customer:
    """
    Get current user and verify they have superadmin role.

    Args:
        current_user: Current user from role checker

    Returns:
        Customer instance with superadmin privileges
    """
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    session: AsyncSession = Depends(get_db)
) -> Optional[Customer]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work differently for authenticated vs unauthenticated users.

    Args:
        credentials: HTTP Authorization credentials (Bearer token) - optional
        session: Database session

    Returns:
        Customer instance if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        # Extract token
        token = credentials.credentials

        # Verify and decode token
        payload = AuthService.verify_access_token(token)

        if not payload:
            return None

        # Extract user ID from token
        user_id = UUID(payload.get("user_id"))

        # Fetch user from database
        stmt = select(Customer).where(Customer.id == user_id)
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()

        return customer

    except Exception:
        # If any error occurs, just return None (optional auth)
        return None
