"""Authentication schemas for Phase 3 JWT authentication."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
import re

from app.utils.phone_validator import validate_phone_number


class UserRegisterSchema(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50, alias="firstName")
    last_name: str = Field(..., min_length=1, max_length=50, alias="lastName")
    phone: Optional[str] = Field(None, max_length=20)

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('phone')
    def validate_phone_field(cls, v):
        """Validate and normalize phone number."""
        if v:
            # This will remove spaces and validate format
            return validate_phone_number(v)
        return None

    @validator('first_name', 'last_name')
    def validate_no_html_in_names(cls, v):
        """Prevent XSS by rejecting HTML tags in name fields (Option A - Strict validation)."""
        if v and ('<' in v or '>' in v):
            raise ValueError('HTML tags are not allowed in name fields')
        return v

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecureP@ssw0rd!",
                "firstName": "John",
                "lastName": "Doe",
                "phone": "+34612345678"
            }
        }


class UserLoginSchema(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecureP@ssw0rd!"
            }
        }


class TokenResponseSchema(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }


class RefreshTokenSchema(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class PasswordResetRequestSchema(BaseModel):
    """Schema for password reset request."""
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirmSchema(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=12, max_length=128)

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "NewSecureP@ssw0rd!"
            }
        }


class PasswordChangeSchema(BaseModel):
    """Schema for password change (authenticated user)."""
    current_password: str
    new_password: str = Field(..., min_length=12, max_length=128)

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldP@ssw0rd!",
                "new_password": "NewSecureP@ssw0rd!"
            }
        }


class UserResponseSchema(BaseModel):
    """Schema for user response."""
    id: UUID
    email: Optional[str] = None  # Changed from str to Optional[str] to handle encrypted/None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+34612345678",
                "role": "customer",
                "is_active": True,
                "is_email_verified": False,
                "created_at": "2025-11-02T10:00:00Z",
                "last_login_at": "2025-11-02T15:30:00Z"
            }
        }


class AuthResponseSchema(BaseModel):
    """Schema for authentication response with user and tokens."""
    user: UserResponseSchema
    tokens: TokenResponseSchema

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone": "+34612345678",
                    "role": "customer",
                    "is_active": True,
                    "is_email_verified": False,
                    "created_at": "2025-11-02T10:00:00Z",
                    "last_login_at": "2025-11-02T15:30:00Z"
                },
                "tokens": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 900
                }
            }
        }


class MagicLinkRequestSchema(BaseModel):
    """Schema for requesting a magic link."""
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }
