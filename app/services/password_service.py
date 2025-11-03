"""Password hashing and verification service using bcrypt."""
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Configure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordService:
    """Service for password hashing and verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False

    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        Check if password needs to be rehashed (algorithm upgrade).

        Args:
            hashed_password: Hashed password to check

        Returns:
            True if needs rehash, False otherwise
        """
        return pwd_context.needs_update(hashed_password)
