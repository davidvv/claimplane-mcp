
"""Admin router for claim management."""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Claim, User, ClaimStatusHistory
from app.schemas import (
    AdminClaimList, AdminClaimListItem, AdminClaimStatusUpdate, 
    AdminClaimStatusUpdateResponse, ErrorResponse, ClaimStatus
)
from app.services.claim_service import ClaimService
from app.utils.auth import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/claims", response_model=AdminClaimList)
async def list_all_claims(
    skip: int = Query(0, ge=0, description="Number of claims to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of claims to return"),
    status_filter: str = Query(None, description="Filter by claim status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> AdminClaimList:
    """Admin - list all claims for review."""
    try:
        claim_service = ClaimService(db)
        claims = claim_service.get_all_claims(
            skip=skip,
            limit=limit,
            status_filter=status_filter
        )
        
        claim_items = []
        for claim in claims:
            claim_items.append(AdminClaimListItem(
                claimId=claim.claim_id,
                userName=claim.full_name,
                flightNumber=claim.flight_number,
                status=claim.status,
                submittedAt=claim.created_at
            ))
        
        return AdminClaimList(claims=claim_items)
        
    except Exception as e:
        logger.error(f"Error listing claims: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving claims"
        )


@router.get("/claims/{claim_id}", response_model=ClaimStatus)
async def get_admin_claim_details(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> ClaimStatus:
    """Admin - get detailed claim information."""
    try:
        claim_service = ClaimService(db)
        claim = claim_service.get_claim_by_id(claim_id)
        
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
        
        return ClaimStatus(
            claimId=claim.claim_id,
            status=claim.status,
            lastUpdated=claim.updated_at or claim.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving claim details"
        )


@router.patch("/claims/{claim_id}/status", response_model=AdminClaimStatusUpdateResponse)
async def update_claim_status(
    claim_id: str,
    status_update: AdminClaimStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> AdminClaimStatusUpdateResponse:
    """Admin - update claim status."""
    try:
        claim_service = ClaimService(db)
        
        # Get the claim
        claim = claim_service.get_claim_by_id(claim_id)
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
        
        # Validate status
        valid_statuses = ["submitted", "under_review", "approved", "rejected", "resolved"]
        if status_update.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Update claim status
        previous_status = claim.status
        claim.status = status_update.status
        claim.updated_at = datetime.utcnow()
        
        # Create status history entry
        status_history = ClaimStatusHistory(
            claim_id=claim.id,
            previous_status=previous_status,
            new_status=status_update.status,
            changed_by=f"admin:{current_user.email}",
            notes=f"Status updated by admin {current_user.email}"
        )
        db.add(status_history)
        db.commit()
        
        logger.info(f"Admin {current_user.email} updated claim {claim_id} status from {previous_status} to {status_update.status}")
        
        return AdminClaimStatusUpdateResponse(message="Claim status updated.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating claim status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating claim status"
        )


@router.get("/claims/{claim_id}/history")
async def get_claim_status_history(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> List[dict]:
    """Admin - get claim status history."""
    try:
        claim_service = ClaimService(db)
        claim = claim_service.get_claim_by_id(claim_id)
        
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
        
        history = db.query(ClaimStatusHistory).filter(
            ClaimStatusHistory.claim_id == claim.id
        ).order_by(ClaimStatusHistory.changed_at.desc()).all()
        
        return [
            {
                "previousStatus": h.previous_status,
                "newStatus": h.new_status,
                "changedBy": h.changed_by,
                "changedAt": h.changed_at,
                "notes": h.notes
            }
            for h in history
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim status history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving claim status history"
        )


@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> dict:
    """Admin - get system statistics."""
    try:
        # Total claims
        total_claims = db.query(Claim).count()
        
        # Claims by status
        status_counts = {}
        for status_value in ["submitted", "under_review", "approved", "rejected", "resolved"]:
            count = db.query(Claim).filter(Claim.status == status_value).count()
            status_counts[status_value] = count
        
        # Recent claims (last 30 days)
        thirty_days_ago = datetime.utcnow().timestamp() - (30 * 24 * 60 * 60)
        recent_claims = db.query(Claim).filter(
            Claim.created_at >= datetime.fromtimestamp(thirty_days_ago)
        ).count()
        
        return {
            "totalClaims": total_claims,
            "claimsByStatus": status_counts,
            "recentClaims30Days": recent_claims,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving statistics"
        )


@router.post("/claims/{claim_id}/notes")
async def add_claim_note(
    claim_id: str,
    note: str = Query(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> dict:
    """Admin - add a note to a claim."""
    try:
        claim_service = ClaimService(db)
        claim = claim_service.get_claim_by_id(claim_id)
        
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
        
        # Create status history entry with note
        status_history = ClaimStatusHistory(
            claim_id=claim.id,
            previous_status=claim.status,
            new_status=claim.status,  # Status doesn't change, just adding note
            changed_by=f"admin:{current_user.email}",
            notes=f"Note added by admin {current_user.email}: {note}"
        )
        db.add(status_history)
        db.commit()
        
        return {"message": "Note added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding claim note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding note to claim"
        )
