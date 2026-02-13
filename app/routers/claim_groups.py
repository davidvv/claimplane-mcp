"""API routes for claim group management (Phase 5 - Multi-Passenger Claims)."""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import Customer, ClaimGroup
from app.schemas import (
    ClaimGroupCreateSchema,
    ClaimGroupSchema,
    ClaimGroupSummarySchema,
    ClaimGroupDetailSchema,
    GroupedClaimSubmitSchema,
    StandardResponseSchema
)
from app.services.claim_group_service import ClaimGroupService

router = APIRouter(prefix="/claim-groups", tags=["Claim Groups"])


@router.post(
    "",
    response_model=StandardResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new claim group",
    description="Create a new claim group for multi-passenger/family claims."
)
async def create_claim_group(
    data: ClaimGroupCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user)
):
    """Create a new claim group."""
    try:
        claim_group = await ClaimGroupService.create_claim_group(
            db=db,
            account_holder_id=current_user.id,
            data=data
        )
        
        return StandardResponseSchema(
            success=True,
            message="Claim group created successfully",
            data={
                "id": str(claim_group.id),
                "group_name": claim_group.group_name,
                "flight_number": claim_group.flight_number,
                "flight_date": claim_group.flight_date.isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/me",
    response_model=StandardResponseSchema,
    summary="Get current user's claim groups",
    description="Get all claim groups for the authenticated customer."
)
async def get_my_claim_groups(
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user)
):
    """Get all claim groups for the current user."""
    try:
        claim_groups = await ClaimGroupService.get_customer_claim_groups(
            db=db,
            customer_id=current_user.id
        )
        
        # Get summary for each group
        groups_data = []
        for group in claim_groups:
            summary = await ClaimGroupService.get_claim_group_summary(
                db=db,
                group_id=group.id
            )
            if summary:
                groups_data.append(summary)
        
        return StandardResponseSchema(
            success=True,
            message=f"Found {len(groups_data)} claim groups",
            data={"groups": groups_data}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{group_id}",
    response_model=StandardResponseSchema,
    summary="Get claim group details",
    description="Get detailed information about a specific claim group."
)
async def get_claim_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user)
):
    """Get claim group details."""
    try:
        claim_group = await ClaimGroupService.get_claim_group_with_claims(
            db=db,
            group_id=group_id
        )
        
        if not claim_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim group not found"
            )
        
        # Verify ownership
        if claim_group.account_holder_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this claim group"
            )
        
        # Get summary
        summary = await ClaimGroupService.get_claim_group_summary(
            db=db,
            group_id=group_id
        )
        
        return StandardResponseSchema(
            success=True,
            message="Claim group retrieved successfully",
            data=summary
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{group_id}/consent",
    response_model=StandardResponseSchema,
    summary="Confirm consent for group claims",
    description="Confirm that the account holder has permission to file claims for other passengers."
)
async def confirm_group_consent(
    group_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user)
):
    """Confirm consent for filing claims on behalf of others."""
    try:
        claim_group = await ClaimGroupService.get_claim_group(db, group_id)
        
        if not claim_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim group not found"
            )
        
        # Verify ownership
        if claim_group.account_holder_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this claim group"
            )
        
        # Get client IP
        client_ip = request.headers.get("x-forwarded-for", request.client.host)
        
        updated_group = await ClaimGroupService.confirm_consent(
            db=db,
            group_id=group_id,
            ip_address=client_ip
        )
        
        return StandardResponseSchema(
            success=True,
            message="Consent confirmed successfully",
            data={
                "consent_confirmed": updated_group.consent_confirmed,
                "consent_confirmed_at": updated_group.consent_confirmed_at.isoformat() if updated_group.consent_confirmed_at else None
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
