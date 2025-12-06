"""Pydantic schemas for admin endpoints."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


# Claim Status Update Schemas
class ClaimStatusUpdateRequest(BaseModel):
    """Request model for updating claim status."""
    new_status: str = Field(..., description="New status for the claim")
    change_reason: Optional[str] = Field(None, description="Reason for status change")

    class Config:
        json_schema_extra = {
            "example": {
                "new_status": "approved",
                "change_reason": "All documents verified and compensation calculated"
            }
        }


class ClaimAssignRequest(BaseModel):
    """Request model for assigning a claim to a reviewer."""
    assigned_to: UUID = Field(..., description="UUID of user to assign to")

    class Config:
        json_schema_extra = {
            "example": {
                "assigned_to": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class ClaimCompensationUpdateRequest(BaseModel):
    """Request model for updating compensation amount."""
    compensation_amount: Decimal = Field(..., gt=0, description="Compensation amount in EUR")
    reason: Optional[str] = Field(None, description="Reason for manual compensation adjustment")

    class Config:
        json_schema_extra = {
            "example": {
                "compensation_amount": 400.00,
                "reason": "Standard EU261 compensation for 1500-3500km flight"
            }
        }


class ClaimNoteRequest(BaseModel):
    """Request model for adding a note to a claim."""
    note_text: str = Field(..., min_length=1, max_length=5000, description="Note content")
    is_internal: bool = Field(True, description="Whether note is internal (not visible to customer)")

    class Config:
        json_schema_extra = {
            "example": {
                "note_text": "Customer provided additional documentation via email.",
                "is_internal": True
            }
        }


class BulkActionRequest(BaseModel):
    """Request model for bulk operations on claims."""
    claim_ids: List[UUID] = Field(..., min_length=1, description="List of claim IDs")
    action: str = Field(..., description="Action to perform: status_update, assign, export")
    parameters: dict = Field(default_factory=dict, description="Action-specific parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "claim_ids": ["123e4567-e89b-12d3-a456-426614174000", "223e4567-e89b-12d3-a456-426614174001"],
                "action": "status_update",
                "parameters": {
                    "new_status": "under_review",
                    "change_reason": "Bulk review initiated"
                }
            }
        }


# Filtering and Search Schemas
class ClaimFilterParams(BaseModel):
    """Query parameters for filtering claims."""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")
    status: Optional[str] = Field(None, description="Filter by claim status")
    airline: Optional[str] = Field(None, description="Filter by airline")
    incident_type: Optional[str] = Field(None, description="Filter by incident type")
    assigned_to: Optional[UUID] = Field(None, description="Filter by assigned reviewer")
    date_from: Optional[date] = Field(None, description="Filter by departure date from")
    date_to: Optional[date] = Field(None, description="Filter by departure date to")
    search: Optional[str] = Field(None, description="Search in customer name, email, flight number")
    sort_by: str = Field("submitted_at", description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


# Response Schemas
class CustomerResponse(BaseModel):
    """Customer information in responses."""
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class ClaimNoteResponse(BaseModel):
    """Note response model."""
    id: UUID
    claim_id: UUID
    author_id: UUID
    note_text: str
    is_internal: bool
    created_at: datetime
    author: Optional[CustomerResponse] = None  # Author details (loaded via relationship)

    class Config:
        from_attributes = True


class ClaimStatusHistoryResponse(BaseModel):
    """Status history response model."""
    id: UUID
    claim_id: UUID
    previous_status: Optional[str]
    new_status: str
    changed_by: UUID
    change_reason: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True


class ClaimFileResponse(BaseModel):
    """File information in claim responses."""
    id: UUID
    filename: str
    document_type: str
    file_size: int
    mime_type: str
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ClaimDetailResponse(BaseModel):
    """Detailed claim response with all related data."""
    id: UUID
    customer_id: UUID
    flight_number: str
    airline: str
    departure_date: date
    departure_airport: str
    arrival_airport: str
    incident_type: str
    status: str
    compensation_amount: Optional[Decimal]
    calculated_compensation: Optional[Decimal]
    currency: str
    claim_description: Optional[str] = Field(None, alias="notes")  # Claim description field
    submitted_at: datetime
    updated_at: datetime

    # Admin fields
    assigned_to: Optional[UUID]
    assigned_at: Optional[datetime]
    reviewed_by: Optional[UUID]
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]
    flight_distance_km: Optional[Decimal]
    delay_hours: Optional[Decimal]
    extraordinary_circumstances: Optional[str]

    # Related data
    customer: Optional[CustomerResponse] = None
    assignee: Optional[CustomerResponse] = None  # Admin assigned to this claim
    files: List[ClaimFileResponse] = []
    claim_notes: List[ClaimNoteResponse] = Field(default=[])  # List of notes on this claim
    status_history: List[ClaimStatusHistoryResponse] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class ClaimListResponse(BaseModel):
    """Claim in list view (less detail)."""
    id: UUID
    customer_id: UUID
    flight_number: str
    airline: str
    departure_date: date
    departure_airport: str
    arrival_airport: str
    incident_type: str
    status: str
    compensation_amount: Optional[Decimal]
    submitted_at: datetime
    assigned_to: Optional[UUID]
    customer: Optional[CustomerResponse]
    assignee: Optional[CustomerResponse] = None  # Admin assigned to this claim

    class Config:
        from_attributes = True


class PaginatedClaimsResponse(BaseModel):
    """Paginated claims response."""
    claims: List[ClaimListResponse]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_prev: bool


class AnalyticsSummaryResponse(BaseModel):
    """Analytics summary response."""
    total_claims: int
    pending_review: int
    approved: int
    rejected: int
    total_compensation: float
    avg_processing_time_hours: float
    claims_by_status: dict
    claims_by_airline: dict
    claims_by_incident_type: dict


class BulkActionResponse(BaseModel):
    """Response for bulk operations."""
    success: bool
    affected_count: int
    message: str
    errors: List[str] = []


# File Review Schemas
class FileReviewRequest(BaseModel):
    """Request model for reviewing a file."""
    approved: bool = Field(..., description="Whether file is approved")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if not approved")
    reviewer_notes: Optional[str] = Field(None, description="Additional notes from reviewer")

    class Config:
        json_schema_extra = {
            "example": {
                "approved": True,
                "reviewer_notes": "Boarding pass verified - all information visible and valid"
            }
        }


class FileReuploadRequest(BaseModel):
    """Request model for requesting file re-upload."""
    reason: str = Field(..., min_length=1, description="Reason for requesting re-upload")
    deadline_days: int = Field(7, ge=1, le=30, description="Days until deadline")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "The uploaded document is not clear enough. Please upload a higher quality scan.",
                "deadline_days": 7
            }
        }


class FileMetadataResponse(BaseModel):
    """Detailed file metadata response."""
    id: UUID
    claim_id: UUID
    customer_id: UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    file_hash: str
    document_type: str
    storage_provider: str
    storage_path: str
    encryption_status: str
    access_level: str
    download_count: int
    status: str
    validation_status: str
    rejection_reason: Optional[str]
    uploaded_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[UUID]

    class Config:
        from_attributes = True


# Compensation Calculation Schemas
class CompensationCalculationRequest(BaseModel):
    """Request for calculating compensation."""
    departure_airport: str = Field(..., min_length=3, max_length=3, description="IATA departure airport code")
    arrival_airport: str = Field(..., min_length=3, max_length=3, description="IATA arrival airport code")
    delay_hours: Optional[float] = Field(None, ge=0, description="Delay in hours")
    incident_type: str = Field(..., description="Type of incident")
    extraordinary_circumstances: Optional[str] = Field(None, description="Description of extraordinary circumstances")

    class Config:
        json_schema_extra = {
            "example": {
                "departure_airport": "LHR",
                "arrival_airport": "JFK",
                "delay_hours": 4.5,
                "incident_type": "delay"
            }
        }


class CompensationCalculationResponse(BaseModel):
    """Response from compensation calculation."""
    eligible: bool
    amount: Decimal
    distance_km: float
    reason: str
    requires_manual_review: bool


class StatusTransitionInfo(BaseModel):
    """Information about valid status transitions."""
    current_status: str
    valid_next_statuses: List[str]
    status_info: dict
