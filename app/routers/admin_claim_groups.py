"""Admin API routes for claim group management (Phase 5 - Multi-Passenger Claims)."""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models import Customer, ClaimGroup
from app.schemas import (
    ClaimGroupSchema,
    ClaimGroupNoteCreateSchema,
    ClaimGroupNoteSchema,
    BulkActionSchema,
    ClaimGroupFilterSchema,
    StandardResponseSchema
)
from app.services.claim_group_service import (
    ClaimGroupService,
    ClaimGroupNoteService,
    ClaimGroupAdminService
)

router = APIRouter(prefix="/admin/claim-groups", tags=["Admin - Claim Groups"])


@router.get(
    "",
    response_model=StandardResponseSchema,
    summary="List all claim groups (admin)",
    description="Get all claim groups with optional filters. Admin only."
)
async def list_claim_groups(
    status: Optional[str] = Query(None, description="Filter by claim status"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    account_holder_id: Optional[UUID] = Query(None, description="Filter by account holder"),
    flight_number: Optional[str] = Query(None, description="Filter by flight number"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_admin: Customer = Depends(get_current_admin)
):
    """List all claim groups with filters."""
    try:
        claim_groups = await ClaimGroupAdminService.get_all_claim_groups(
            db=db,
            status=status,
            date_from=date_from,
            date_to=date_to,
            account_holder_id=account_holder_id,
            flight_number=flight_number,
            skip=skip,
            limit=limit
        )
        
        # Get summaries for each group
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
            data={
                "groups": groups_data,
                "total": len(groups_data),
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{group_id}",
    response_model=StandardResponseSchema,
    summary="Get claim group details (admin)",
    description="Get detailed information about a specific claim group. Admin only."
)
async def get_claim_group_admin(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Customer = Depends(get_current_admin)
):
    """Get claim group details with all claims."""
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
        
        # Get summary
        summary = await ClaimGroupService.get_claim_group_summary(
            db=db,
            group_id=group_id
        )
        
        # Get notes
        notes = await ClaimGroupNoteService.get_group_notes(
            db=db,
            group_id=group_id
        )
        
        return StandardResponseSchema(
            success=True,
            message="Claim group retrieved successfully",
            data={
                **summary,
                "notes": [
                    {
                        "id": str(note.id),
                        "admin_id": str(note.admin_id),
                        "note_text": note.note_text,
                        "created_at": note.created_at.isoformat()
                    }
                    for note in notes
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{group_id}/notes",
    response_model=StandardResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add note to claim group",
    description="Add an admin note to a claim group. Admin only."
)
async def add_claim_group_note(
    group_id: UUID,
    data: ClaimGroupNoteCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_admin: Customer = Depends(get_current_admin)
):
    """Add a note to a claim group."""
    try:
        # Verify group exists
        claim_group = await ClaimGroupService.get_claim_group(db, group_id)
        if not claim_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim group not found"
            )
        
        note = await ClaimGroupNoteService.create_note(
            db=db,
            group_id=group_id,
            admin_id=current_admin.id,
            data=data
        )
        
        return StandardResponseSchema(
            success=True,
            message="Note added successfully",
            data={
                "id": str(note.id),
                "note_text": note.note_text,
                "created_at": note.created_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{group_id}/notes",
    response_model=StandardResponseSchema,
    summary="Get claim group notes",
    description="Get all admin notes for a claim group. Admin only."
)
async def get_claim_group_notes(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Customer = Depends(get_current_admin)
):
    """Get all notes for a claim group."""
    try:
        # Verify group exists
        claim_group = await ClaimGroupService.get_claim_group(db, group_id)
        if not claim_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim group not found"
            )
        
        notes = await ClaimGroupNoteService.get_group_notes(
            db=db,
            group_id=group_id
        )
        
        return StandardResponseSchema(
            success=True,
            message=f"Found {len(notes)} notes",
            data=[
                {
                    "id": str(note.id),
                    "admin_id": str(note.admin_id),
                    "note_text": note.note_text,
                    "created_at": note.created_at.isoformat()
                }
                for note in notes
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{group_id}/bulk-action",
    response_model=StandardResponseSchema,
    summary="Perform bulk action on claim group",
    description="Apply action to all claims in a group (approve_all, reject_all, request_info_all). Admin only."
)
async def bulk_action_claim_group(
    group_id: UUID,
    data: BulkActionSchema,
    db: AsyncSession = Depends(get_db),
    current_admin: Customer = Depends(get_current_admin)
):
    """Perform bulk action on all claims in a group."""
    try:
        # Verify group exists
        claim_group = await ClaimGroupService.get_claim_group(db, group_id)
        if not claim_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim group not found"
            )
        
        result = await ClaimGroupAdminService.bulk_update_claims(
            db=db,
            group_id=group_id,
            data=data,
            admin_id=current_admin.id
        )
        
        return StandardResponseSchema(
            success=result["success"],
            message=f"Bulk action completed. {result['updated_count']} of {result['total_claims']} claims updated.",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
