"""Schemas for account management endpoints (Phase 4)."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class EmailChangeRequest(BaseModel):
    """Request to change email address."""
    current_password: str = Field(..., min_length=1, description="Current password for verification")
    new_email: EmailStr = Field(..., description="New email address")


class PasswordChangeRequest(BaseModel):
    """Request to change password."""
    current_password: str = Field(..., min_length=1, description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets minimum requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class AccountDeletionRequestSchema(BaseModel):
    """Request to delete account."""
    reason: Optional[str] = Field(None, description="Reason for deletion (optional)")


class AccountInfoResponse(BaseModel):
    """Account information response."""
    id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime]
    is_email_verified: bool
    total_claims: int
    has_password: bool  # True if user has password (registered), False for magic link only users

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
