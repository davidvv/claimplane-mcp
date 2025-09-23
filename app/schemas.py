"""Pydantic schemas for API validation and serialization."""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# Base schemas
class ErrorResponse(BaseModel):
    """Error response schema matching OpenAPI spec."""
    message: str = Field(..., description="Error message detail")


# Flight Details schemas
class FlightDetails(BaseModel):
    """Flight details schema matching OpenAPI spec."""
    flightNumber: str = Field(
        ...,
        description="Flight code (e.g., LH1234)",
        pattern=r"^[A-Z]{2}\d{3,4}$",
        example="LH1234"
    )
    plannedDepartureDate: date = Field(
        ...,
        description="Planned departure date (YYYY-MM-DD)",
        example="2024-01-15"
    )
    actualDepartureTime: Optional[datetime] = Field(
        None,
        description="Actual departure timestamp, optional",
        example="2024-01-15T14:30:00Z"
    )
    
    @validator('flightNumber')
    def validate_flight_number(cls, v):
        """Validate flight number format."""
        if not v or len(v) < 4 or len(v) > 6:
            raise ValueError('Flight number must be 4-6 characters')
        if not v[:2].isalpha() or not v[:2].isupper():
            raise ValueError('Flight number must start with 2 uppercase letters')
        if not v[2:].isdigit():
            raise ValueError('Flight number must end with 3-4 digits')
        return v


class FlightDetailsResponse(BaseModel):
    """Response schema for flight details submission."""
    message: str = Field(..., example="Flight details recorded.")


# Personal Info schemas
class PersonalInfo(BaseModel):
    """Personal information schema matching OpenAPI spec."""
    fullName: str = Field(..., description="User's full name", min_length=1, max_length=255)
    email: EmailStr = Field(..., description="User's email address")
    bookingReference: str = Field(..., description="Booking reference code", min_length=6, max_length=255)


class PersonalInfoResponse(BaseModel):
    """Response schema for personal information submission."""
    message: str = Field(..., example="Personal information recorded.")


# Upload schemas
class UploadResponse(BaseModel):
    """Upload response schema matching OpenAPI spec."""
    message: str = Field(..., example="Files uploaded.")


# Claim Status schemas
class ClaimStatus(BaseModel):
    """Claim status schema matching OpenAPI spec."""
    claimId: str = Field(..., description="Unique claim identifier")
    status: str = Field(..., description="Current claim status (pending, approved, rejected, etc.)")
    lastUpdated: datetime = Field(..., description="Last update timestamp")


# Admin schemas
class AdminClaimListItem(BaseModel):
    """Admin claim list item schema."""
    claimId: str
    userName: str
    flightNumber: str
    status: str
    submittedAt: datetime


class AdminClaimList(BaseModel):
    """Admin claim list response schema."""
    claims: List[AdminClaimListItem]


class AdminClaimStatusUpdate(BaseModel):
    """Admin claim status update request schema."""
    status: str = Field(..., description="New claim status (approved, rejected, etc.)")


class AdminClaimStatusUpdateResponse(BaseModel):
    """Admin claim status update response schema."""
    message: str = Field(..., example="Claim status updated.")


# Additional schemas for complete functionality
class ClaimCreate(BaseModel):
    """Schema for creating a new claim."""
    flightNumber: str
    plannedDepartureDate: date
    actualDepartureTime: Optional[datetime] = None
    fullName: str
    email: EmailStr
    bookingReference: str


class ClaimResponse(BaseModel):
    """Complete claim response schema."""
    claimId: str
    flightNumber: str
    plannedDepartureDate: date
    actualDepartureTime: Optional[datetime]
    fullName: str
    email: EmailStr
    bookingReference: str
    status: str
    createdAt: datetime
    updatedAt: Optional[datetime]


# Chat schemas
class ChatMessageRequest(BaseModel):
    """Chat message request schema."""
    sessionId: str = Field(..., description="Chat session ID")
    message: str = Field(..., description="User message", min_length=1, max_length=1000)


class ChatMessageResponse(BaseModel):
    """Chat message response schema."""
    success: bool
    reply: str
    intent: str = "general"
    confidence: float = Field(..., ge=0.0, le=1.0)


class ChatSessionResponse(BaseModel):
    """Chat session response schema."""
    sessionId: str
    createdAt: datetime


# File upload schemas
class FileUploadRequest(BaseModel):
    """File upload request schema."""
    boardingPass: bytes = Field(..., description="Boarding pass scan or photo (required)")
    receipt: Optional[bytes] = Field(None, description="Expense receipt (optional)")


# Authentication schemas
class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    email: Optional[str] = None


class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    bookingReference: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    email: EmailStr
    bookingReference: str
    isAdmin: bool
    createdAt: datetime


# Health check schema
class HealthCheck(BaseModel):
    """Health check response schema."""
    status: str
    version: str
    timestamp: datetime
    database: str