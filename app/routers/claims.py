"""Claims router implementing OpenAPI spec endpoints."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Claim, User, Document
from app.schemas import (
    FlightDetails, FlightDetailsResponse, PersonalInfo, PersonalInfoResponse,
    UploadResponse, ClaimStatus, ErrorResponse, AdminClaimList, 
    AdminClaimStatusUpdate, AdminClaimStatusUpdateResponse
)
from app.services.claim_service import ClaimService
from app.services.file_service import FileService
from app.utils.auth import get_current_user, get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/flight-details", response_model=FlightDetailsResponse)
async def submit_flight_details(
    flight_details: FlightDetails,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FlightDetailsResponse:
    """Submit flight details for a claim."""
    try:
        claim_service = ClaimService(db)
        claim_service.save_flight_details(current_user.id, flight_details)
        
        return FlightDetailsResponse(message="Flight details recorded.")
    except Exception as e:
        logger.error(f"Error submitting flight details: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data"
        )


@router.post("/personal-info", response_model=PersonalInfoResponse)
async def submit_personal_info(
    personal_info: PersonalInfo,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PersonalInfoResponse:
    """Submit user personal information."""
    try:
        claim_service = ClaimService(db)
        claim_service.save_personal_info(current_user.id, personal_info)
        
        return PersonalInfoResponse(message="Personal information recorded.")
    except Exception as e:
        logger.error(f"Error submitting personal info: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data"
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    boarding_pass: UploadFile = File(..., description="Boarding pass scan or photo (required)"),
    receipt: Optional[UploadFile] = File(None, description="Expense receipt (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UploadResponse:
    """Upload claim-related documents."""
    try:
        file_service = FileService(db)
        
        # Validate and save boarding pass
        if boarding_pass:
            file_service.validate_and_save_file(
                current_user.id, 
                boarding_pass, 
                "boarding_pass"
            )
        
        # Validate and save receipt if provided
        if receipt:
            file_service.validate_and_save_file(
                current_user.id, 
                receipt, 
                "receipt"
            )
        
        return UploadResponse(message="Files uploaded.")
    except ValueError as e:
        logger.error(f"File validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required files or invalid format"
        )


@router.get("/claim-status", response_model=ClaimStatus)
async def get_claim_status(
    claim_id: str = Query(..., description="Unique claim identifier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ClaimStatus:
    """Get the current status of a claim."""
    try:
        claim_service = ClaimService(db)
        claim = claim_service.get_claim_by_id_and_user(claim_id, current_user.id)
        
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
        logger.error(f"Error getting claim status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Additional endpoints for complete functionality

@router.get("/claims", response_model=List[ClaimStatus])
async def get_user_claims(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ClaimStatus]:
    """Get all claims for the current user."""
    try:
        claim_service = ClaimService(db)
        claims = claim_service.get_user_claims(current_user.id)
        
        return [
            ClaimStatus(
                claimId=claim.claim_id,
                status=claim.status,
                lastUpdated=claim.updated_at or claim.created_at
            )
            for claim in claims
        ]
    except Exception as e:
        logger.error(f"Error getting user claims: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/claims/{claim_id}", response_model=ClaimStatus)
async def get_claim_details(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ClaimStatus:
    """Get detailed information about a specific claim."""
    try:
        claim_service = ClaimService(db)
        claim = claim_service.get_claim_by_id_and_user(claim_id, current_user.id)
        
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
            detail="Internal server error"
        )


@router.post("/claims", response_model=ClaimStatus)
async def create_claim(
    flight_details: FlightDetails,
    personal_info: PersonalInfo,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ClaimStatus:
    """Create a new claim with flight details and personal information."""
    try:
        claim_service = ClaimService(db)
        claim = claim_service.create_complete_claim(
            user_id=current_user.id,
            flight_details=flight_details,
            personal_info=personal_info
        )
        
        return ClaimStatus(
            claimId=claim.claim_id,
            status=claim.status,
            lastUpdated=claim.created_at
        )
    except Exception as e:
        logger.error(f"Error creating claim: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data"
        )