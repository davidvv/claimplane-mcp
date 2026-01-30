"""Admin endpoints for managing account deletion requests."""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Customer
from app.dependencies.auth import get_current_admin
from app.repositories.deletion_request_repository import DeletionRequestRepository
from app.services.gdpr_service import GDPRService
from app.schemas.deletion_schemas import (
    DeletionRequestListItem,
    PaginatedDeletionRequestsResponse,
    DeletionRequestDetailResponse,
    DeletionRequestReviewRequest,
    DeletionProcessResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/deletion-requests",
    tags=["Admin - Deletion Requests"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=PaginatedDeletionRequestsResponse)
async def list_deletion_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: str = Query(None, alias="status"),
    date_from: str = Query(None),
    date_to: str = Query(None),
    search: str = Query(None),
    sort_by: str = Query("requested_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    List all deletion requests with filtering and pagination.

    Admin authentication required.
    """
    # Parse dates if provided
    date_from_parsed = datetime.fromisoformat(date_from).date() if date_from else None
    date_to_parsed = datetime.fromisoformat(date_to).date() if date_to else None

    repository = DeletionRequestRepository(session)

    result = await repository.get_deletion_requests_with_details(
        skip=skip,
        limit=limit,
        status=status_filter,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

    logger.info(
        f"Admin {admin.id} listed {len(result['requests'])} deletion requests "
        f"(total: {result['total']})"
    )

    return result


@router.get("/{request_id}", response_model=DeletionRequestDetailResponse)
async def get_deletion_request(
    request_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """Get detailed deletion request information."""
    repository = DeletionRequestRepository(session)

    request = await repository.get_request_with_customer_details(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deletion request {request_id} not found"
        )

    logger.info(f"Admin {admin.id} viewed deletion request {request_id}")

    return request


@router.put("/{request_id}/review", response_model=DeletionRequestDetailResponse)
async def review_deletion_request(
    request_id: UUID,
    review: DeletionRequestReviewRequest,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Approve or reject a deletion request.

    - **Approve**: Marks request as approved, sends confirmation email
    - **Reject**: Marks request as rejected, unblacklists account, sends rejection email
    """
    repository = DeletionRequestRepository(session)

    try:
        if review.action == "approve":
            updated_request = await repository.approve_request(
                request_id=request_id,
                admin_id=admin.id,
                notes=review.notes
            )

            # Reload with relationships for email
            updated_request = await repository.get_request_with_customer_details(request_id)

            # Send approval email to customer
            from app.tasks.account_tasks import send_account_deletion_approval_notification
            send_account_deletion_approval_notification.delay(
                email=updated_request.email,
                customer_name=f"{updated_request.customer.first_name} {updated_request.customer.last_name}",
                notes=review.notes or "Your deletion request has been approved."
            )

            logger.info(f"Admin {admin.id} approved deletion request {request_id}")

        elif review.action == "reject":
            if not review.notes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rejection reason is required in notes field"
                )

            updated_request = await repository.reject_request(
                request_id=request_id,
                admin_id=admin.id,
                rejection_reason=review.notes
            )

            # Reload with relationships for email
            updated_request = await repository.get_request_with_customer_details(request_id)

            # Send rejection email to customer
            from app.tasks.account_tasks import send_account_deletion_rejection_notification
            send_account_deletion_rejection_notification.delay(
                email=updated_request.email,
                customer_name=f"{updated_request.customer.first_name} {updated_request.customer.last_name}",
                rejection_reason=review.notes
            )

            logger.info(f"Admin {admin.id} rejected deletion request {request_id}")

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {review.action}. Must be 'approve' or 'reject'"
            )

        return updated_request

    except ValueError as e:
        logger.error(f"Validation error in deletion request review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in deletion request review: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the review"
        )


@router.post("/{request_id}/process", response_model=DeletionProcessResponse)
async def process_deletion(
    request_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Process an approved deletion request - actually delete/anonymize customer data.

    **CRITICAL**: This action is irreversible. Only approved requests can be processed.

    This will:
    - Delete all files from Nextcloud
    - Anonymize claims (retained for legal compliance)
    - Anonymize customer profile
    - Mark deletion request as completed
    """
    repository = DeletionRequestRepository(session)

    request = await repository.get_by_id(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deletion request {request_id} not found"
        )

    if request.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request must be approved before processing (current status: {request.status})"
        )

    # Perform actual deletion
    deletion_summary = await GDPRService.delete_customer_data(
        session=session,
        customer_id=request.customer_id,
        deletion_request_id=request_id
    )

    logger.warning(
        f"Admin {admin.id} processed deletion for customer {request.customer_id}. "
        f"Files deleted: {deletion_summary['files_deleted']}, "
        f"Files failed: {deletion_summary['files_failed']}, "
        f"Claims anonymized: {deletion_summary['claims_anonymized']}"
    )

    # Send admin notification (not customer - account is deleted)
    from app.tasks.account_tasks import send_account_deletion_completed_admin_notification
    send_account_deletion_completed_admin_notification.delay(
        admin_email=admin.email,
        customer_email=deletion_summary.get("original_email", request.email),
        deletion_summary=deletion_summary
    )

    return DeletionProcessResponse(
        message="Account deletion processed successfully",
        summary=deletion_summary
    )
