"""Pydantic schemas for deletion request management."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


class CustomerSummary(BaseModel):
    """Customer summary for deletion request views."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None  # Changed to Optional[str] to handle encrypted/None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReviewerSummary(BaseModel):
    """Reviewer summary for deletion request views."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None  # Changed to Optional[str] to handle encrypted/None

    class Config:
        from_attributes = True


class DeletionRequestListItem(BaseModel):
    """Deletion request in list view."""
    id: UUID
    customer_id: UUID
    email: Optional[str] = None  # Changed to Optional[str] to handle encrypted/None
    reason: Optional[str] = None
    requested_at: datetime
    status: str
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    open_claims_count: int
    total_claims_count: int

    # Customer details (loaded via relationship)
    customer: Optional[CustomerSummary] = None
    reviewer: Optional[ReviewerSummary] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "customer_id": "223e4567-e89b-12d3-a456-426614174001",
                "email": "customer@example.com",
                "reason": "No longer using the service",
                "requested_at": "2025-01-03T10:00:00Z",
                "status": "pending",
                "reviewed_by": None,
                "reviewed_at": None,
                "notes": None,
                "open_claims_count": 0,
                "total_claims_count": 3
            }
        }


class PaginatedDeletionRequestsResponse(BaseModel):
    """Paginated deletion requests response."""
    requests: List[DeletionRequestListItem]
    total: int
    skip: int
    limit: int
    has_more: bool

    class Config:
        json_schema_extra = {
            "example": {
                "requests": [],
                "total": 10,
                "skip": 0,
                "limit": 50,
                "has_more": False
            }
        }


class DeletionRequestDetailResponse(BaseModel):
    """Detailed deletion request information."""
    id: UUID
    customer_id: UUID
    email: Optional[str] = None  # Changed to Optional[str] to handle encrypted/None
    reason: Optional[str] = None
    requested_at: datetime
    status: str
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    open_claims_count: int
    total_claims_count: int

    # Customer details
    customer: Optional[CustomerSummary] = None
    reviewer: Optional[ReviewerSummary] = None

    class Config:
        from_attributes = True


class DeletionRequestReviewRequest(BaseModel):
    """Request to approve or reject a deletion request."""
    action: str = Field(
        ...,
        pattern="^(approve|reject)$",
        description="Action to take: 'approve' or 'reject'"
    )
    notes: Optional[str] = Field(
        None,
        max_length=5000,
        description="Admin notes (required for rejection, optional for approval)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "action": "approve",
                "notes": "Customer has no open claims. Approved for deletion."
            }
        }


class DeletionProcessResponse(BaseModel):
    """Response after processing a deletion."""
    message: str
    summary: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Account deletion processed successfully",
                "summary": {
                    "customer_id": "223e4567-e89b-12d3-a456-426614174001",
                    "deletion_started_at": "2025-01-03T10:30:00Z",
                    "deletion_completed_at": "2025-01-03T10:30:05Z",
                    "files_deleted": 5,
                    "files_failed": 0,
                    "claims_anonymized": 3,
                    "errors": []
                }
            }
        }
