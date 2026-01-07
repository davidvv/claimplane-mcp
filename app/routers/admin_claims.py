"""Admin endpoints for claim management."""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Customer
from app.dependencies.auth import get_current_admin
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
    ClaimStatusHistoryResponse,
    CustomerResponse
)
from app.tasks.claim_tasks import send_status_update_email
from app.config import config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/claims",
    tags=["Admin - Claims"],
    responses={404: {"description": "Not found"}},
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
    admin: Customer = Depends(get_current_admin)
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

    logger.info(f"Admin {admin.id} listed {len(result['claims'])} claims (total: {result['total']})")

    return result


@router.get("/{claim_id}", response_model=ClaimDetailResponse)
async def get_claim_detail(
    claim_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
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

    logger.info(f"Admin {admin.id} viewed claim {claim_id}")

    return claim


@router.put("/{claim_id}/status", response_model=ClaimDetailResponse)
async def update_claim_status(
    claim_id: UUID,
    update_request: ClaimStatusUpdateRequest,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
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
        changed_by=admin.id,
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

    logger.info(f"Admin {admin.id} updated claim {claim_id} status to {update_request.new_status}")

    return claim_detail


@router.put("/{claim_id}/assign", response_model=ClaimDetailResponse)
async def assign_claim(
    claim_id: UUID,
    assign_request: ClaimAssignRequest,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
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
        assigned_by=admin.id
    )

    await session.commit()

    # Reload with full details
    claim_detail = await repository.get_claim_with_full_details(claim_id)

    logger.info(f"Admin {admin.id} assigned claim {claim_id} to {assign_request.assigned_to}")

    return claim_detail


@router.put("/{claim_id}/compensation", response_model=ClaimDetailResponse)
async def set_compensation(
    claim_id: UUID,
    compensation_request: ClaimCompensationUpdateRequest,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
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
        set_by=admin.id,
        reason=compensation_request.reason
    )

    await session.commit()

    # Reload with full details
    claim_detail = await repository.get_claim_with_full_details(claim_id)

    logger.info(f"Admin {admin.id} set compensation for claim {claim_id} to €{compensation_request.compensation_amount}")

    return claim_detail


@router.post("/{claim_id}/notes", response_model=ClaimNoteResponse)
async def add_note(
    claim_id: UUID,
    note_request: ClaimNoteRequest,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
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
        author_id=admin.id,
        note_text=note_request.note_text,
        is_internal=note_request.is_internal
    )

    await session.commit()

    logger.info(f"Admin {admin.id} added {'internal' if note_request.is_internal else 'customer-facing'} note to claim {claim_id}")

    return note


@router.get("/{claim_id}/notes", response_model=List[ClaimNoteResponse])
async def get_notes(
    claim_id: UUID,
    include_internal: bool = Query(True),
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
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
    admin: Customer = Depends(get_current_admin)
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
    admin: Customer = Depends(get_current_admin)
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
                changed_by=admin.id,
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
                assigned_by=admin.id
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action: {bulk_request.action}"
            )

        await session.commit()

        logger.info(f"Admin {admin.id} performed bulk {bulk_request.action} on {affected_count} claims")

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
    admin: Customer = Depends(get_current_admin)
):
    """
    Get analytics summary for admin dashboard.
    """
    repository = AdminClaimRepository(session)

    summary = await repository.get_analytics_summary()

    logger.info(f"Admin {admin.id} requested analytics summary")

    return summary


@router.post("/calculate-compensation", response_model=CompensationCalculationResponse)
async def calculate_compensation(
    calculation_request: CompensationCalculationRequest,
    admin: Customer = Depends(get_current_admin)
):
    """
    Calculate compensation for a claim based on EU261/2004 regulations.

    This is a standalone calculation endpoint for reference.
    """
    result = await CompensationService.calculate_compensation(
        departure_airport=calculation_request.departure_airport,
        arrival_airport=calculation_request.arrival_airport,
        delay_hours=calculation_request.delay_hours,
        incident_type=calculation_request.incident_type,
        extraordinary_circumstances=calculation_request.extraordinary_circumstances,
        use_api=True  # Enable AeroDataBox API for any airport
    )

    return result


@router.get("/{claim_id}/status-transitions", response_model=StatusTransitionInfo)
async def get_valid_transitions(
    claim_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
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


@router.get("/users/admins", response_model=List[CustomerResponse])
async def get_admin_users(
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Get list of all admin users for assignment purposes.

    Returns list of users with admin or superadmin role.
    """
    from app.repositories.customer_repository import CustomerRepository
    from sqlalchemy import select

    # Query for admin and superadmin users
    query = select(Customer).where(
        Customer.role.in_(['admin', 'superadmin'])
    ).order_by(Customer.first_name, Customer.last_name)

    result = await session.execute(query)
    admin_users = result.scalars().all()

    logger.info(f"Admin {admin.id} requested list of {len(admin_users)} admin users")

    return admin_users


# Phase 6: AeroDataBox API Management Endpoints

@router.get("/api-usage/stats")
async def get_api_usage_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Get AeroDataBox API usage statistics for the last N days.

    Returns:
    - Total API calls and credits used
    - Average and max response times
    - Daily usage breakdown
    - Top endpoints by usage

    Admin authentication required.
    """
    from app.services.quota_tracking_service import QuotaTrackingService

    try:
        stats = await QuotaTrackingService.get_usage_statistics(session, days=days)

        logger.info(f"Admin {admin.id} requested API usage stats for {days} days")

        return stats

    except Exception as e:
        logger.error(f"Failed to get API usage stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API usage statistics: {str(e)}"
        )


@router.get("/api-usage/quota")
async def get_quota_status(
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Get current AeroDataBox API quota status.

    Returns:
    - Current billing period (start/end dates)
    - Total credits allowed and used
    - Credits remaining
    - Usage percentage
    - Alert status (80%, 90%, 95% thresholds)
    - Whether quota is exceeded (>95%)

    Admin authentication required.
    """
    from app.services.quota_tracking_service import QuotaTrackingService

    try:
        quota_status = await QuotaTrackingService.get_quota_status(session)

        logger.info(
            f"Admin {admin.id} checked quota status: "
            f"{quota_status['credits_used']}/{quota_status['total_credits_allowed']} "
            f"({quota_status['usage_percentage']}%)"
        )

        return quota_status

    except Exception as e:
        logger.error(f"Failed to get quota status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quota status: {str(e)}"
        )


@router.post("/{claim_id}/refresh-flight-data", response_model=ClaimDetailResponse)
async def refresh_flight_data(
    claim_id: UUID,
    force: bool = Query(False, description="Force API call even if cached"),
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Force refresh flight data for a specific claim using AeroDataBox API.

    This endpoint:
    - Bypasses cache if force=True
    - Calls AeroDataBox API to get latest flight status
    - Updates claim with verified flight data (distance, delay, compensation)
    - Stores new FlightData snapshot in database
    - Returns updated claim details

    Use this when:
    - Flight data has changed (delay increased, status updated)
    - Initial verification failed and you want to retry
    - Cache is stale and you need fresh data

    **WARNING**: This consumes API credits (2 credits per call for TIER 2 endpoint).
    Use sparingly to avoid exceeding quota.

    Admin authentication required.
    """
    from app.services.flight_data_service import FlightDataService
    from app.repositories.admin_claim_repository import AdminClaimRepository

    repository = AdminClaimRepository(session)

    # Verify claim exists
    claim = await repository.get_by_id(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )

    try:
        logger.info(
            f"Admin {admin.id} requesting flight data refresh for claim {claim_id} "
            f"(force={force})"
        )

        # Call FlightDataService to verify and enrich claim
        enriched_data = await FlightDataService.verify_and_enrich_claim(
            session=session,
            claim=claim,
            user_id=admin.id,
            force_refresh=force
        )

        # Update claim with verified data
        if enriched_data.get("verified"):
            logger.info(
                f"Flight verified for claim {claim_id}: "
                f"compensation={enriched_data.get('compensation_amount')} EUR, "
                f"cached={enriched_data.get('cached')}"
            )

            # Update claim fields
            if enriched_data.get("compensation_amount") is not None:
                claim.calculated_compensation = enriched_data["compensation_amount"]

            if enriched_data.get("distance_km") is not None:
                claim.flight_distance_km = enriched_data["distance_km"]

            if enriched_data.get("delay_hours") is not None:
                claim.delay_hours = enriched_data["delay_hours"]

            await session.commit()

            logger.info(
                f"Updated claim {claim_id} with verified flight data "
                f"(API credits used: {enriched_data.get('api_credits_used', 0)})"
            )

        else:
            logger.warning(
                f"Flight not verified for claim {claim_id}: "
                f"source={enriched_data.get('verification_source')}"
            )

        # Reload claim with full details
        claim_detail = await repository.get_claim_with_full_details(claim_id)

        return claim_detail

    except Exception as e:
        logger.error(
            f"Failed to refresh flight data for claim {claim_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh flight data: {str(e)}"
        )


@router.post("/backfill-flight-data")
async def backfill_flight_data(
    batch_size: int = Query(50, ge=1, le=500, description="Number of claims to process"),
    admin: Customer = Depends(get_current_admin)
):
    """
    Trigger backfill of flight data for existing claims without verification.

    This endpoint queues a Celery task to process claims in the background.
    The task will:
    - Find claims without flight data
    - Call AeroDataBox API to verify flight details
    - Update claims with distance, delay, and compensation
    - Stop if API quota is exceeded (>95%)

    **Cost Warning**: Each claim consumes 2 API credits (TIER 2 endpoint).
    - Free tier: 600 credits/month = 300 claims/month
    - Recommended batch size: 50 claims at a time

    **Returns immediately** with task ID. Use GET /admin/claims/backfill-status/{task_id}
    to check progress.

    Admin authentication required.

    Args:
        batch_size: Number of claims to process (1-500, default: 50)
        admin: Current admin user

    Returns:
        Task information:
        - task_id: Celery task ID for status tracking
        - status: Task status (PENDING, STARTED, SUCCESS, FAILURE)
        - message: Human-readable message
    """
    from app.tasks.claim_tasks import backfill_flight_data as backfill_task

    try:
        logger.info(
            f"Admin {admin.id} triggered backfill for {batch_size} claims"
        )

        # Queue the backfill task (runs in background via Celery)
        task = backfill_task.delay(
            batch_size=batch_size,
            admin_user_id=str(admin.id)
        )

        logger.info(f"Backfill task queued: {task.id}")

        return {
            "success": True,
            "task_id": task.id,
            "status": task.status,
            "message": f"Backfill task queued for {batch_size} claims. Use task_id to check status.",
            "batch_size": batch_size,
            "check_status_url": f"/admin/claims/backfill-status/{task.id}"
        }

    except Exception as e:
        logger.error(f"Failed to queue backfill task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue backfill task: {str(e)}"
        )


@router.get("/backfill-status/{task_id}")
async def get_backfill_status(
    task_id: str,
    admin: Customer = Depends(get_current_admin)
):
    """
    Get status of a backfill task.

    Returns real-time status and statistics for a running or completed backfill task.

    Admin authentication required.

    Args:
        task_id: Celery task ID from backfill-flight-data endpoint
        admin: Current admin user

    Returns:
        Task status information:
        - task_id: Task ID
        - status: PENDING | STARTED | SUCCESS | FAILURE | RETRY
        - result: Task result (if completed) with statistics
        - error: Error message (if failed)
    """
    from celery.result import AsyncResult

    try:
        task = AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": task.status,
        }

        if task.status == "SUCCESS":
            # Task completed successfully - return statistics
            result = task.result
            response["result"] = result
            response["message"] = (
                f"Backfill complete: {result.get('verified_count', 0)} claims verified, "
                f"{result.get('failed_count', 0)} failed, "
                f"{result.get('api_credits_used', 0)} API credits used"
            )

        elif task.status == "FAILURE":
            # Task failed - return error
            response["error"] = str(task.result)
            response["message"] = "Backfill task failed"

        elif task.status == "PENDING":
            response["message"] = "Backfill task queued, waiting to start"

        elif task.status == "STARTED":
            response["message"] = "Backfill task in progress"

        else:
            response["message"] = f"Task status: {task.status}"

        logger.info(f"Admin {admin.id} checked backfill task {task_id}: {task.status}")

        return response

    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task status: {str(e)}"
        )
