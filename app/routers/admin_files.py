"""Admin endpoints for file/document management and review."""
import logging
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Customer, ClaimFile
from app.dependencies.auth import get_current_admin
from app.repositories.file_repository import FileRepository
from app.schemas.admin_schemas import (
    FileReviewRequest,
    FileReuploadRequest,
    FileMetadataResponse,
    ClaimFileResponse
)
from app.tasks.claim_tasks import send_document_rejected_email
from app.config import config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/files",
    tags=["Admin - Files"],
    responses={404: {"description": "Not found"}},
)


@router.get("/claim/{claim_id}/documents", response_model=List[ClaimFileResponse])
async def list_claim_documents(
    claim_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    List all documents for a specific claim.

    Documents are grouped and sorted by document type and upload date.
    """
    repository = FileRepository(session)

    files = await repository.get_files_by_claim(claim_id)

    if not files:
        logger.info(f"No files found for claim {claim_id}")

    logger.info(f"Admin {admin.id} listed {len(files)} files for claim {claim_id}")

    return files


@router.get("/{file_id}/metadata", response_model=FileMetadataResponse)
async def get_file_metadata(
    file_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Get detailed metadata for a file.

    Includes upload info, security scan results, access logs, and validation status.
    """
    repository = FileRepository(session)

    file = await repository.get_by_id(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )

    logger.info(f"Admin {admin.id} viewed metadata for file {file_id}")

    return file


@router.put("/{file_id}/review", response_model=FileMetadataResponse)
async def review_file(
    file_id: UUID,
    review_request: FileReviewRequest,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Approve or reject a document.

    Approved documents are marked as validated.
    Rejected documents require a rejection reason and may trigger re-upload request.
    """
    repository = FileRepository(session)

    file = await repository.get_by_id(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )

    # Update file status based on review
    if review_request.approved:
        file.status = ClaimFile.STATUS_APPROVED
        file.validation_status = "approved"
        file.rejection_reason = None
    else:
        file.status = ClaimFile.STATUS_REJECTED
        file.validation_status = "rejected"
        file.rejection_reason = review_request.rejection_reason or "Document did not meet requirements"

    # Set reviewer and review timestamp
    file.reviewed_by = admin.id
    file.reviewed_at = datetime.utcnow()

    await session.flush()
    await session.refresh(file)
    await session.commit()

    # Send document rejected email notification (Phase 2)
    if not review_request.approved and config.NOTIFICATIONS_ENABLED:
        try:
            # Load claim and customer information for the email
            from app.repositories.claim_repository import ClaimRepository
            claim_repo = ClaimRepository(session)
            claim = await claim_repo.get_by_id(file.claim_id)

            if claim and claim.customer:
                # Trigger async email task
                send_document_rejected_email.delay(
                    customer_email=claim.customer.email,
                    customer_name=f"{claim.customer.first_name} {claim.customer.last_name}",
                    claim_id=str(file.claim_id),
                    document_type=file.document_type,
                    rejection_reason=file.rejection_reason,
                    flight_number=claim.flight_number,
                    airline=claim.airline
                )
                logger.info(f"Document rejected email task queued for customer {claim.customer.email}")
        except Exception as e:
            # Don't fail the API request if email queueing fails
            logger.error(f"Failed to queue document rejected email: {str(e)}")

    action = "approved" if review_request.approved else "rejected"
    logger.info(f"Admin {admin.id} {action} file {file_id}")

    return file


@router.post("/{file_id}/request-reupload")
async def request_file_reupload(
    file_id: UUID,
    reupload_request: FileReuploadRequest,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Request customer to re-upload a document.

    This marks the file as rejected and sends a notification to the customer
    (notification functionality will be implemented in Phase 2).
    """
    repository = FileRepository(session)

    file = await repository.get_by_id(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )

    # Mark file as rejected with reason
    file.status = ClaimFile.STATUS_REJECTED
    file.validation_status = "reupload_required"
    file.rejection_reason = reupload_request.reason
    file.reviewed_by = admin.id
    file.reviewed_at = datetime.utcnow()

    # Set deadline for re-upload
    deadline = datetime.utcnow() + timedelta(days=reupload_request.deadline_days)
    file.expires_at = deadline

    await session.flush()
    await session.refresh(file)
    await session.commit()

    logger.info(
        f"Admin {admin.id} requested re-upload for file {file_id}. "
        f"Deadline: {deadline.date()}"
    )

    # TODO: In Phase 2, trigger notification to customer here
    # notification_service.send_reupload_request(file, reupload_request)

    return {
        "success": True,
        "message": "Re-upload request created successfully",
        "file_id": str(file_id),
        "deadline": deadline.isoformat(),
        "reason": reupload_request.reason
    }


@router.get("/pending-review", response_model=List[ClaimFileResponse])
async def get_pending_review_files(
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Get all files pending review.

    Returns files with status 'uploaded' or 'validated' that haven't been reviewed yet.
    """
    from sqlalchemy import select

    # Query for files pending review
    query = select(ClaimFile).where(
        ClaimFile.status.in_([ClaimFile.STATUS_UPLOADED, ClaimFile.STATUS_VALIDATED]),
        ClaimFile.reviewed_by.is_(None)
    ).order_by(ClaimFile.uploaded_at)

    result = await session.execute(query)
    files = result.scalars().all()

    logger.info(f"Admin {admin.id} listed {len(files)} files pending review")

    return files


@router.get("/by-document-type/{document_type}", response_model=List[ClaimFileResponse])
async def get_files_by_document_type(
    document_type: str,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Get all files of a specific document type.

    Useful for batch reviewing similar document types.
    """
    from sqlalchemy import select

    query = select(ClaimFile).where(
        ClaimFile.document_type == document_type
    ).order_by(ClaimFile.uploaded_at.desc())

    result = await session.execute(query)
    files = result.scalars().all()

    logger.info(f"Admin {admin.id} listed {len(files)} files of type {document_type}")

    return files


@router.get("/statistics")
async def get_file_statistics(
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Get statistics about files in the system.

    Returns counts by status, document type, and validation status.
    """
    from sqlalchemy import select, func

    # Count by status
    status_query = select(
        ClaimFile.status,
        func.count(ClaimFile.id).label('count')
    ).group_by(ClaimFile.status)
    status_result = await session.execute(status_query)
    status_counts = {row.status: row.count for row in status_result}

    # Count by document type
    doc_type_query = select(
        ClaimFile.document_type,
        func.count(ClaimFile.id).label('count')
    ).group_by(ClaimFile.document_type)
    doc_type_result = await session.execute(doc_type_query)
    doc_type_counts = {row.document_type: row.count for row in doc_type_result}

    # Count by validation status
    validation_query = select(
        ClaimFile.validation_status,
        func.count(ClaimFile.id).label('count')
    ).group_by(ClaimFile.validation_status)
    validation_result = await session.execute(validation_query)
    validation_counts = {row.validation_status: row.count for row in validation_result}

    # Total file size
    size_query = select(func.sum(ClaimFile.file_size))
    size_result = await session.execute(size_query)
    total_size = size_result.scalar() or 0

    # Pending review count
    pending_query = select(func.count(ClaimFile.id)).where(
        ClaimFile.status.in_([ClaimFile.STATUS_UPLOADED, ClaimFile.STATUS_VALIDATED]),
        ClaimFile.reviewed_by.is_(None)
    )
    pending_result = await session.execute(pending_query)
    pending_count = pending_result.scalar()

    logger.info(f"Admin {admin.id} requested file statistics")

    return {
        "status_counts": status_counts,
        "document_type_counts": doc_type_counts,
        "validation_status_counts": validation_counts,
        "total_size_bytes": int(total_size),
        "total_size_mb": round(float(total_size) / (1024 * 1024), 2),
        "pending_review_count": pending_count
    }


@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: Customer = Depends(get_current_admin)
):
    """
    Soft delete a file.

    Files are not physically deleted but marked as deleted.
    Admin action is logged.
    """
    repository = FileRepository(session)

    file = await repository.get_by_id(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )

    # Soft delete
    file.is_deleted = 1
    file.deleted_at = datetime.utcnow()

    await session.flush()
    await session.commit()

    logger.warning(f"Admin {admin.id} deleted file {file_id} (soft delete)")

    return {
        "success": True,
        "message": f"File {file_id} marked as deleted",
        "deleted_at": file.deleted_at.isoformat()
    }
