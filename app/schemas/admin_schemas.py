"""Pydantic schemas for admin endpoints."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


def validate_no_html(value: str) -> str:
    """Validate that string does not contain HTML tags."""
    if not value:
        return value
    if '<' in value or '>' in value:
        raise ValueError('HTML tags are not allowed in this field')
    return value


# Claim Status Update Schemas
class ClaimStatusUpdateRequest(BaseModel):
    """Request model for updating claim status."""
    new_status: str = Field(..., description="New status for the claim")
    change_reason: Optional[str] = Field(None, description="Reason for status change")

    @validator('change_reason')
    def validate_no_html_in_reason(cls, v):
        """Prevent XSS by rejecting HTML tags in change reason."""
        if v is not None:
            return validate_no_html(v)
        return v

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

    @validator('reason')
    def validate_no_html_in_reason(cls, v):
        """Prevent XSS by rejecting HTML tags in reason."""
        if v is not None:
            return validate_no_html(v)
        return v

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

    @validator('note_text')
    def validate_no_html_in_note(cls, v):
        """Prevent XSS by rejecting HTML tags in note text."""
        return validate_no_html(v)

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
class AdminCustomerResponse(BaseModel):
    """Customer information in admin responses."""
    id: UUID
    email: Optional[Any] = None
    first_name: Optional[Any] = None
    last_name: Optional[Any] = None
    phone: Optional[Any] = None
    full_name: Optional[Any] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class ClaimNoteResponse(BaseModel):
    """Note response model."""
    id: UUID
    claim_id: UUID
    author_id: UUID
    note_text: Optional[str] = None
    is_internal: bool = True
    created_at: Optional[datetime] = None
    author: Optional[AdminCustomerResponse] = None  # Author details (loaded via relationship)

    class Config:
        from_attributes = True


class ClaimStatusHistoryResponse(BaseModel):
    """Status history response model."""
    id: UUID
    claim_id: UUID
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    changed_by: Optional[UUID] = None
    change_reason: Optional[str] = None
    changed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClaimFileResponse(BaseModel):
    """File information in claim responses."""
    id: UUID
    filename: Optional[str] = None
    original_filename: Optional[str] = None
    document_type: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    status: Optional[str] = None
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClaimDetailResponse(BaseModel):
    """Detailed claim response with all related data."""
    id: UUID
    customer_id: UUID
    flight_number: Optional[str] = None
    airline: Optional[str] = None
    departure_date: Optional[date] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    incident_type: Optional[str] = None
    status: Optional[str] = None
    compensation_amount: Optional[Decimal] = None
    calculated_compensation: Optional[Decimal] = None
    currency: Optional[str] = "EUR"
    incident_description: Optional[str] = Field(None, alias="notes")  # Maps DB 'notes' field to 'incident_description' for frontend
    submitted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Admin fields
    assigned_to: Optional[UUID] = None
    assigned_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    flight_distance_km: Optional[Decimal] = None
    delay_hours: Optional[Decimal] = None
    extraordinary_circumstances: Optional[str] = None

    # Related data
    customer: Optional[AdminCustomerResponse] = None
    assignee: Optional[AdminCustomerResponse] = None  # Admin assigned to this claim
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
    flight_number: Optional[str] = None
    airline: Optional[str] = None
    departure_date: Optional[date] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    incident_type: Optional[str] = None
    status: Optional[str] = None
    compensation_amount: Optional[Decimal] = None
    submitted_at: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    customer: Optional[AdminCustomerResponse] = None
    assignee: Optional[AdminCustomerResponse] = None  # Admin assigned to this claim

    class Config:
        from_attributes = True
        populate_by_name = True


class PaginatedClaimsResponse(BaseModel):
    """Paginated claims response."""
    claims: List[ClaimListResponse] = []
    total: int = 0
    skip: int = 0
    limit: int = 100
    has_next: bool = False
    has_prev: bool = False


class AnalyticsSummaryResponse(BaseModel):
    """Analytics summary response."""
    total_claims: int = 0
    pending_review: int = 0
    approved: int = 0
    rejected: int = 0
    total_compensation: float = 0.0
    avg_processing_time_hours: float = 0.0
    claims_by_status: dict = Field(default_factory=dict)
    claims_by_airline: dict = Field(default_factory=dict)
    claims_by_incident_type: dict = Field(default_factory=dict)


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
    filename: Optional[str] = None
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    file_hash: Optional[str] = None
    document_type: Optional[str] = None
    storage_provider: Optional[str] = None
    storage_path: Optional[str] = None
    encryption_status: Optional[str] = None
    access_level: Optional[str] = None
    download_count: Optional[int] = None
    status: Optional[str] = None
    validation_status: Optional[str] = None
    rejection_reason: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None

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
    current_status: Optional[str] = None
    valid_next_statuses: List[str] = Field(default_factory=list)
    status_info: dict = Field(default_factory=dict)
