"""Authentication service for JWT token management and user authentication."""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.models import Customer, RefreshToken, PasswordResetToken, MagicLinkToken
from app.services.password_service import PasswordService


class AuthService:
    """Service for handling authentication operations."""

    @staticmethod
    def create_access_token(user_id: UUID, email: str, role: str) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User's UUID
            email: User's email address
            role: User's role (customer, admin, superadmin)

        Returns:
            JWT access token string
        """
        expiration = datetime.utcnow() + timedelta(minutes=config.JWT_EXPIRATION_MINUTES)

        payload = {
            "user_id": str(user_id),
            "email": email,
            "role": role,
            "exp": expiration,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        return token

    @staticmethod
    async def create_refresh_token(
        session: AsyncSession,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Tuple[str, RefreshToken]:
        """
        Create a refresh token and store it in the database.

        Args:
            session: Database session
            user_id: User's UUID
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            device_id: Optional device identifier

        Returns:
            Tuple of (token_string, RefreshToken model instance)
        """
        # Generate secure random token
        token_string = secrets.token_urlsafe(64)

        # Calculate expiration
        expiration = datetime.utcnow() + timedelta(days=config.JWT_REFRESH_EXPIRATION_DAYS)

        # Create refresh token record
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token_string,
            expires_at=expiration,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id
        )

        session.add(refresh_token)
        await session.flush()

        return token_string, refresh_token

    @staticmethod
    def verify_access_token(token: str) -> Optional[dict]:
        """
        Verify and decode a JWT access token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])

            # Verify it's an access token
            if payload.get("type") != "access":
                return None

            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    async def verify_refresh_token(session: AsyncSession, token: str) -> Optional[RefreshToken]:
        """
        Verify a refresh token and return the token record if valid.

        Args:
            session: Database session
            token: Refresh token string

        Returns:
            RefreshToken instance if valid, None otherwise
        """
        # Find token in database
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        result = await session.execute(stmt)
        refresh_token = result.scalar_one_or_none()

        if not refresh_token:
            return None

        # Check if token is valid
        if not refresh_token.is_valid:
            return None

        return refresh_token

    @staticmethod
    async def revoke_refresh_token(
        session: AsyncSession,
        token: str,
        replaced_by: Optional[str] = None
    ) -> bool:
        """
        Revoke a refresh token.

        Args:
            session: Database session
            token: Refresh token string to revoke
            replaced_by: Optional new token that replaces this one

        Returns:
            True if token was revoked, False if token not found
        """
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        result = await session.execute(stmt)
        refresh_token = result.scalar_one_or_none()

        if not refresh_token:
            return False

        refresh_token.revoked_at = datetime.utcnow()
        if replaced_by:
            refresh_token.replaced_by_token = replaced_by

        await session.flush()
        return True

    @staticmethod
    async def revoke_all_user_tokens(session: AsyncSession, user_id: UUID) -> int:
        """
        Revoke all refresh tokens for a user.

        Args:
            session: Database session
            user_id: User's UUID

        Returns:
            Number of tokens revoked
        """
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at == None
        )
        result = await session.execute(stmt)
        tokens = result.scalars().all()

        count = 0
        for token in tokens:
            token.revoked_at = datetime.utcnow()
            count += 1

        await session.flush()
        return count

    @staticmethod
    async def create_password_reset_token(
        session: AsyncSession,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, PasswordResetToken]:
        """
        Create a password reset token.

        Args:
            session: Database session
            user_id: User's UUID
            ip_address: Optional client IP address
            user_agent: Optional client user agent

        Returns:
            Tuple of (token_string, PasswordResetToken instance)
        """
        # Generate secure random token
        token_string = secrets.token_urlsafe(64)

        # Calculate expiration (24 hours from now)
        expiration = datetime.utcnow() + timedelta(hours=24)

        # Create password reset token record
        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token_string,
            expires_at=expiration,
            ip_address=ip_address,
            user_agent=user_agent
        )

        session.add(reset_token)
        await session.flush()

        return token_string, reset_token

    @staticmethod
    async def verify_password_reset_token(
        session: AsyncSession,
        token: str
    ) -> Optional[PasswordResetToken]:
        """
        Verify a password reset token.

        Args:
            session: Database session
            token: Password reset token string

        Returns:
            PasswordResetToken instance if valid, None otherwise
        """
        stmt = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await session.execute(stmt)
        reset_token = result.scalar_one_or_none()

        if not reset_token:
            return None

        # Check if token is valid
        if not reset_token.is_valid:
            return None

        return reset_token

    @staticmethod
    async def use_password_reset_token(
        session: AsyncSession,
        token: str
    ) -> bool:
        """
        Mark a password reset token as used.

        Args:
            session: Database session
            token: Password reset token string

        Returns:
            True if token was marked as used, False if token not found
        """
        stmt = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await session.execute(stmt)
        reset_token = result.scalar_one_or_none()

        if not reset_token:
            return False

        reset_token.used_at = datetime.utcnow()
        await session.flush()
        return True

    @staticmethod
    async def register_user(
        session: AsyncSession,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        role: str = Customer.ROLE_CUSTOMER
    ) -> Customer:
        """
        Register a new user.

        Args:
            session: Database session
            email: User's email address
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            phone: Optional phone number
            role: User role (defaults to customer)

        Returns:
            Created Customer instance

        Raises:
            ValueError: If user already exists or validation fails
        """
        # Check if user already exists
        stmt = select(Customer).where(Customer.email == email)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password
        password_hash = PasswordService.hash_password(password)

        # Create customer
        customer = Customer(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role,
            is_active=True,
            is_email_verified=False  # Require email verification
        )

        session.add(customer)
        await session.flush()

        return customer

    @staticmethod
    async def login_user(
        session: AsyncSession,
        email: str,
        password: str
    ) -> Optional[Customer]:
        """
        Authenticate a user with email and password.

        Args:
            session: Database session
            email: User's email address
            password: Plain text password

        Returns:
            Customer instance if authentication successful, None otherwise
        """
        # Find user by email
        stmt = select(Customer).where(Customer.email == email)
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            return None

        # Check if user has a password (for migration compatibility)
        if not customer.password_hash:
            return None

        # Verify password
        if not PasswordService.verify_password(password, customer.password_hash):
            return None

        # Check if user is active
        if not customer.is_active:
            return None

        # Update last login timestamp
        customer.last_login_at = datetime.utcnow()
        await session.flush()

        return customer

    @staticmethod
    async def change_password(
        session: AsyncSession,
        user_id: UUID,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change a user's password (requires old password verification).

        Args:
            session: Database session
            user_id: User's UUID
            old_password: Current password
            new_password: New password

        Returns:
            True if password was changed, False otherwise

        Raises:
            ValueError: If old password is incorrect
        """
        # Find user
        stmt = select(Customer).where(Customer.id == user_id)
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            return False

        # Verify old password
        if not customer.password_hash:
            raise ValueError("User has no password set")

        if not PasswordService.verify_password(old_password, customer.password_hash):
            raise ValueError("Old password is incorrect")

        # Set new password
        customer.password_hash = PasswordService.hash_password(new_password)
        await session.flush()

        # Revoke all refresh tokens (force re-login)
        await AuthService.revoke_all_user_tokens(session, user_id)

        return True

    @staticmethod
    async def reset_password(
        session: AsyncSession,
        token: str,
        new_password: str
    ) -> bool:
        """
        Reset a user's password using a reset token.

        Args:
            session: Database session
            token: Password reset token
            new_password: New password

        Returns:
            True if password was reset, False otherwise

        Raises:
            ValueError: If token is invalid or expired
        """
        # Verify reset token
        reset_token = await AuthService.verify_password_reset_token(session, token)

        if not reset_token:
            raise ValueError("Invalid or expired password reset token")

        # Find user
        stmt = select(Customer).where(Customer.id == reset_token.user_id)
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            return False

        # Set new password
        customer.password_hash = PasswordService.hash_password(new_password)

        # Mark token as used
        await AuthService.use_password_reset_token(session, token)

        # Revoke all refresh tokens (force re-login)
        await AuthService.revoke_all_user_tokens(session, reset_token.user_id)

        await session.flush()

        return True

    @staticmethod
    async def verify_email(
        session: AsyncSession,
        user_id: UUID
    ) -> bool:
        """
        Mark a user's email as verified.

        Args:
            session: Database session
            user_id: User's UUID

        Returns:
            True if email was verified, False otherwise
        """
        stmt = select(Customer).where(Customer.id == user_id)
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            return False

        customer.is_email_verified = True
        customer.email_verified_at = datetime.utcnow()
        await session.flush()

        return True

    @staticmethod
    async def create_magic_link_token(
        session: AsyncSession,
        user_id: UUID,
        claim_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, MagicLinkToken]:
        """
        Create a magic link token for passwordless authentication.

        Args:
            session: Database session
            user_id: User's UUID
            claim_id: Optional claim ID if magic link is for a specific claim
            ip_address: Optional client IP address
            user_agent: Optional client user agent

        Returns:
            Tuple of (token_string, MagicLinkToken instance)
        """
        # Generate secure random token
        token_string = secrets.token_urlsafe(64)

        # Token expires in 48 hours
        expiration = datetime.utcnow() + timedelta(hours=48)

        # Create magic link token record
        magic_token = MagicLinkToken(
            user_id=user_id,
            claim_id=claim_id,
            token=token_string,
            expires_at=expiration,
            ip_address=ip_address,
            user_agent=user_agent
        )

        session.add(magic_token)
        await session.flush()

        return token_string, magic_token

    @staticmethod
    async def verify_magic_link_token(
        session: AsyncSession,
        token: str
    ) -> Optional[Tuple[Customer, Optional[UUID]]]:
        """
        Verify a magic link token and mark it as used.

        Args:
            session: Database session
            token: Magic link token string

        Returns:
            Tuple of (Customer, claim_id) if valid, None otherwise
        """
        # Find token
        stmt = select(MagicLinkToken).where(MagicLinkToken.token == token)
        result = await session.execute(stmt)
        magic_token = result.scalar_one_or_none()

        if not magic_token:
            return None

        # Check if token is valid
        if not magic_token.is_valid:
            return None

        # Mark token as used (only if not already used)
        # This allows reuse within the 5-minute grace period
        if magic_token.used_at is None:
            magic_token.used_at = datetime.utcnow()
            await session.flush()

        # Get customer
        stmt = select(Customer).where(Customer.id == magic_token.user_id)
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            return None

        # Update last login
        customer.last_login_at = datetime.utcnow()
        await session.flush()

        return customer, magic_token.claim_id
