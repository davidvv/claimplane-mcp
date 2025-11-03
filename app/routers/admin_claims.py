"""Admin endpoints for claim management."""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.admin_claim_repository import AdminClaimRepository
from app.services.compensation_service import CompensationService
from app.services.claim_workflow_service import ClaimWorkflowService
from app.schemas.admin_schemas import (
    ClaimDetailResponse,
    ClaimListResponse,
    PaginatedClaimsResponse,
    ClaimStatusUpdateRequest,
    ClaimAssignRequest,
    ClaimCompensationUpdateRequest,
    ClaimNoteRequest,
    ClaimNoteResponse,
    BulkActionRequest,
    BulkActionResponse,
    AnalyticsSummaryResponse,
    CompensationCalculationRequest,
    CompensationCalculationResponse,
    StatusTransitionInfo,
    ClaimStatusHistoryResponse
)
from app.tasks.claim_tasks import send_status_update_email
from app.config import config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/claims",
    tags=["Admin - Claims"],
    responses={404: {"description": "Not found"}},
)


def get_admin_user_id(request: Request) -> UUID:
    """
    Get admin user ID from headers.

    TODO: Replace with proper JWT authentication in Phase 3.
    For now, using X-Admin-ID header similar to X-Customer-ID pattern.
    """
    admin_id = request.headers.get("X-Admin-ID")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required (X-Admin-ID header)"
        )
    try:
        return UUID(admin_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid admin ID format"
        )


@router.get("", response_model=PaginatedClaimsResponse)
async def list_claims(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: str = Query(None, alias="status"),
    airline: str = Query(None),
    incident_type: str = Query(None),
    assigned_to: UUID = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    search: str = Query(None),
    sort_by: str = Query("submitted_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    List all claims with filtering and pagination.

    Admin authentication required via X-Admin-ID header.
    """
    from datetime import datetime

    # Parse dates if provided
    date_from_parsed = datetime.fromisoformat(date_from).date() if date_from else None
    date_to_parsed = datetime.fromisoformat(date_to).date() if date_to else None

    repository = AdminClaimRepository(session)

    result = await repository.get_claims_with_details(
        skip=skip,
        limit=limit,
        status=status_filter,
        airline=airline,
        incident_type=incident_type,
        assigned_to=assigned_to,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

    logger.info(f"Admin {admin_id} listed {len(result['claims'])} claims (total: {result['total']})")

    return result


@router.get("/{claim_id}", response_model=ClaimDetailResponse)
async def get_claim_detail(
    claim_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Get detailed claim information including all files, notes, and history.

    Admin authentication required via X-Admin-ID header.
    """
    repository = AdminClaimRepository(session)

    claim = await repository.get_claim_with_full_details(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )

    logger.info(f"Admin {admin_id} viewed claim {claim_id}")

    return claim


@router.put("/{claim_id}/status", response_model=ClaimDetailResponse)
async def update_claim_status(
    claim_id: UUID,
    update_request: ClaimStatusUpdateRequest,
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Update claim status with validation and audit trail.

    Valid status transitions are enforced. Rejection requires a reason.
    """
    repository = AdminClaimRepository(session)

    claim = await repository.get_by_id(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )

    # Store old status before transition
    old_status = claim.status

    # Use workflow service to transition status
    updated_claim = await ClaimWorkflowService.transition_status(
        session=session,
        claim=claim,
        new_status=update_request.new_status,
        changed_by=admin_id,
        change_reason=update_request.change_reason
    )

    await session.commit()

    # Reload with full details
    claim_detail = await repository.get_claim_with_full_details(claim_id)

    # Send status update email notification (Phase 2)
    if config.NOTIFICATIONS_ENABLED and claim_detail.customer:
        try:
            # Get compensation amount if claim is approved
            compensation = None
            if claim_detail.calculated_compensation:
                compensation = float(claim_detail.calculated_compensation)

            # Trigger async email task (runs in background via Celery)
            send_status_update_email.delay(
                customer_email=claim_detail.customer.email,
                customer_name=f"{claim_detail.customer.first_name} {claim_detail.customer.last_name}",
                claim_id=str(claim_id),
                old_status=old_status,  # Use stored old status
                new_status=update_request.new_status,
                flight_number=claim_detail.flight_number,
                airline=claim_detail.airline,
                change_reason=update_request.change_reason,
                compensation_amount=compensation
            )
            logger.info(f"Status update email task queued for customer {claim_detail.customer.email}")
        except Exception as e:
            # Don't fail the API request if email queueing fails
            logger.error(f"Failed to queue status update email: {str(e)}")

    logger.info(f"Admin {admin_id} updated claim {claim_id} status to {update_request.new_status}")

    return claim_detail


@router.put("/{claim_id}/assign", response_model=ClaimDetailResponse)
async def assign_claim(
    claim_id: UUID,
    assign_request: ClaimAssignRequest,
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Assign claim to a reviewer.
    """
    repository = AdminClaimRepository(session)

    claim = await repository.get_by_id(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )

    # Use workflow service to assign
    await ClaimWorkflowService.assign_claim(
        session=session,
        claim=claim,
        assigned_to=assign_request.assigned_to,
        assigned_by=admin_id
    )

    await session.commit()

    # Reload with full details
    claim_detail = await repository.get_claim_with_full_details(claim_id)

    logger.info(f"Admin {admin_id} assigned claim {claim_id} to {assign_request.assigned_to}")

    return claim_detail


@router.put("/{claim_id}/compensation", response_model=ClaimDetailResponse)
async def set_compensation(
    claim_id: UUID,
    compensation_request: ClaimCompensationUpdateRequest,
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Set or update compensation amount for a claim.
    """
    repository = AdminClaimRepository(session)

    claim = await repository.get_by_id(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )

    # Use workflow service to set compensation
    await ClaimWorkflowService.set_compensation(
        session=session,
        claim=claim,
        compensation_amount=float(compensation_request.compensation_amount),
        set_by=admin_id,
        reason=compensation_request.reason
    )

    await session.commit()

    # Reload with full details
    claim_detail = await repository.get_claim_with_full_details(claim_id)

    logger.info(f"Admin {admin_id} set compensation for claim {claim_id} to €{compensation_request.compensation_amount}")

    return claim_detail


@router.post("/{claim_id}/notes", response_model=ClaimNoteResponse)
async def add_note(
    claim_id: UUID,
    note_request: ClaimNoteRequest,
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Add a note to a claim.

    Notes can be internal (visible only to admins) or customer-facing.
    """
    repository = AdminClaimRepository(session)

    # Verify claim exists
    claim = await repository.get_by_id(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )

    note = await repository.add_note(
        claim_id=claim_id,
        author_id=admin_id,
        note_text=note_request.note_text,
        is_internal=note_request.is_internal
    )

    await session.commit()

    logger.info(f"Admin {admin_id} added {'internal' if note_request.is_internal else 'customer-facing'} note to claim {claim_id}")

    return note


@router.get("/{claim_id}/notes", response_model=List[ClaimNoteResponse])
async def get_notes(
    claim_id: UUID,
    include_internal: bool = Query(True),
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Get all notes for a claim.
    """
    repository = AdminClaimRepository(session)

    notes = await repository.get_notes(
        claim_id=claim_id,
        include_internal=include_internal
    )

    return notes


@router.get("/{claim_id}/history", response_model=List[ClaimStatusHistoryResponse])
async def get_status_history(
    claim_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Get status change history for a claim.
    """
    repository = AdminClaimRepository(session)

    history = await repository.get_status_history(claim_id)

    return history


@router.post("/bulk-action", response_model=BulkActionResponse)
async def bulk_action(
    bulk_request: BulkActionRequest,
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Perform bulk operations on multiple claims.

    Supported actions:
    - status_update: Update status for multiple claims
    - assign: Assign multiple claims to a reviewer
    """
    repository = AdminClaimRepository(session)

    errors = []
    affected_count = 0

    try:
        if bulk_request.action == "status_update":
            new_status = bulk_request.parameters.get("new_status")
            change_reason = bulk_request.parameters.get("change_reason")

            if not new_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="new_status parameter required for status_update action"
                )

            affected_count = await repository.bulk_update_status(
                claim_ids=bulk_request.claim_ids,
                new_status=new_status,
                changed_by=admin_id,
                change_reason=change_reason
            )

        elif bulk_request.action == "assign":
            assigned_to = bulk_request.parameters.get("assigned_to")

            if not assigned_to:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="assigned_to parameter required for assign action"
                )

            affected_count = await repository.bulk_assign(
                claim_ids=bulk_request.claim_ids,
                assigned_to=UUID(assigned_to),
                assigned_by=admin_id
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action: {bulk_request.action}"
            )

        await session.commit()

        logger.info(f"Admin {admin_id} performed bulk {bulk_request.action} on {affected_count} claims")

        return BulkActionResponse(
            success=True,
            affected_count=affected_count,
            message=f"Successfully performed {bulk_request.action} on {affected_count} claims",
            errors=errors
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Bulk action failed: {str(e)}")
        raise


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Get analytics summary for admin dashboard.
    """
    repository = AdminClaimRepository(session)

    summary = await repository.get_analytics_summary()

    logger.info(f"Admin {admin_id} requested analytics summary")

    return summary


@router.post("/calculate-compensation", response_model=CompensationCalculationResponse)
async def calculate_compensation(
    calculation_request: CompensationCalculationRequest,
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Calculate compensation for a claim based on EU261/2004 regulations.

    This is a standalone calculation endpoint for reference.
    """
    result = CompensationService.calculate_compensation(
        departure_airport=calculation_request.departure_airport,
        arrival_airport=calculation_request.arrival_airport,
        delay_hours=calculation_request.delay_hours,
        incident_type=calculation_request.incident_type,
        extraordinary_circumstances=calculation_request.extraordinary_circumstances
    )

    return result


@router.get("/{claim_id}/status-transitions", response_model=StatusTransitionInfo)
async def get_valid_transitions(
    claim_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_admin_user_id)
):
    """
    Get valid status transitions for a claim.
    """
    repository = AdminClaimRepository(session)

    claim = await repository.get_by_id(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )

    valid_next = ClaimWorkflowService.get_valid_next_statuses(claim.status)
    status_info = ClaimWorkflowService.get_status_display_info(claim.status)

    return StatusTransitionInfo(
        current_status=claim.status,
        valid_next_statuses=valid_next,
        status_info=status_info
    )
