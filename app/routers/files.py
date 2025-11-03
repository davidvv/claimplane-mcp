"""File management API endpoints."""
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Customer, Claim
from app.repositories import ClaimRepository
from app.schemas import (
    FileResponseSchema, FileListResponseSchema, FileAccessLogSchema,
    FileSearchSchema, FileSummarySchema, FileValidationRuleSchema
)
from app.services.file_service import FileService, get_file_service
from app.services.file_validation_service import file_validation_service
from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/files", tags=["files"])


async def verify_file_access(file_info, current_user: Customer) -> None:
    """
    Verify that the current user has access to the file.
    Admins can access all files.
    Customers can only access their own files.

    Args:
        file_info: File information object
        current_user: Currently authenticated user

    Raises:
        HTTPException: 403 if user doesn't have access
    """
    # Admins can access all files
    if current_user.role in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
        return

    # Customers can only access their own files
    if file_info.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own files"
        )


@router.post("/upload", response_model=FileResponseSchema, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    claim_id: str = Form(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    access_level: str = Form("private"),
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file to the system.

    Requires authentication. The file will be associated with the authenticated user.
    Customers can only upload files to their own claims.
    Admins can upload files to any claim.

    Args:
        file: The file to upload
        claim_id: ID of the claim this file belongs to
        document_type: Type of document (boarding_pass, id_document, etc.)
        description: Optional description of the file
        access_level: Access level for the file (public, private, restricted)
        current_user: Currently authenticated user
        db: Database session

    Returns:
        FileResponseSchema: Information about the uploaded file

    Raises:
        HTTPException: If validation fails, access denied, or upload errors occur
    """
    try:
        # Verify claim ownership (customers can only upload to their own claims)
        claim_repo = ClaimRepository(db)
        claim = await claim_repo.get_by_id(uuid.UUID(claim_id))

        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Claim with id {claim_id} not found"
            )

        # Customers can only upload files to their own claims
        if current_user.role not in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
            if claim.customer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You can only upload files to your own claims"
                )

        # Validate file size
        if file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 50MB limit"
            )

        # Get file service
        file_service = get_file_service(db)

        # Upload file (use authenticated user's ID)
        uploaded_file = await file_service.upload_file(
            file=file,
            claim_id=claim_id,
            customer_id=str(current_user.id),
            document_type=document_type,
            description=description,
            access_level=access_level
        )

        return FileResponseSchema.model_validate(uploaded_file)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.get("/{file_id}", response_model=FileResponseSchema)
async def get_file_info(
    file_id: str,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about a specific file.

    Requires authentication. Customers can only access their own files.
    Admins can access all files.

    Args:
        file_id: ID of the file
        current_user: Currently authenticated user
        db: Database session

    Returns:
        FileResponseSchema: File information

    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        file_service = get_file_service(db)
        file_info = await file_service.get_file_info(file_id, str(current_user.id))

        # Verify access
        await verify_file_access(file_info, current_user)

        return FileResponseSchema.model_validate(file_info)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file info: {str(e)}"
        )


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download a file.

    Requires authentication. Customers can only download their own files.
    Admins can download any file.

    Args:
        file_id: ID of the file to download
        current_user: Currently authenticated user
        db: Database session

    Returns:
        StreamingResponse: File content as downloadable response

    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        file_service = get_file_service(db)

        # Get file info first to verify access
        file_info = await file_service.get_file_info(file_id, str(current_user.id))

        # Verify access
        await verify_file_access(file_info, current_user)

        # Download file
        file_content, file_info = await file_service.download_file(file_id, str(current_user.id))

        return StreamingResponse(
            iter([file_content]),
            media_type=file_info.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_info.original_filename}"',
                "Content-Length": str(file_info.file_size)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File download failed: {str(e)}"
        )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (soft delete) a file.

    Requires authentication. Customers can only delete their own files.
    Admins can delete any file.

    Args:
        file_id: ID of the file to delete
        current_user: Currently authenticated user
        db: Database session

    Returns:
        None

    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        file_service = get_file_service(db)

        # Get file info first to verify access
        file_info = await file_service.get_file_info(file_id, str(current_user.id))

        # Verify access
        await verify_file_access(file_info, current_user)

        # Delete file
        success = await file_service.delete_file(file_id, str(current_user.id))

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File deletion failed: {str(e)}"
        )


@router.get("/claim/{claim_id}", response_model=FileListResponseSchema)
async def get_files_by_claim(
    claim_id: str,
    page: int = 1,
    per_page: int = 20,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get files for a specific claim.

    Requires authentication. Customers can only access files for their own claims.
    Admins can access files for any claim.

    Args:
        claim_id: ID of the claim
        page: Page number for pagination
        per_page: Items per page
        current_user: Currently authenticated user
        db: Database session

    Returns:
        FileListResponseSchema: List of files with pagination info

    Raises:
        HTTPException: If claim not found or access denied
    """
    try:
        # Verify claim access first
        claim_repo = ClaimRepository(db)
        claim = await claim_repo.get_by_id(uuid.UUID(claim_id))

        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Claim with id {claim_id} not found"
            )

        # Customers can only access their own claims
        if current_user.role not in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
            if claim.customer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You can only access files for your own claims"
                )

        file_service = get_file_service(db)
        files = await file_service.get_files_by_claim(claim_id, str(current_user.id))

        # Simple pagination (in production, this would be done in the database)
        total = len(files)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_files = files[start:end]

        return FileListResponseSchema(
            files=[FileResponseSchema.model_validate(f) for f in paginated_files],
            total=total,
            page=page,
            per_page=per_page,
            has_next=end < total,
            has_prev=start > 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get claim files: {str(e)}"
        )


@router.get("/customer/{customer_id}", response_model=FileListResponseSchema)
async def get_files_by_customer(
    customer_id: str,
    request: Request,
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Get files for a specific customer.
    
    Args:
        customer_id: ID of the customer
        request: FastAPI request object
        page: Page number for pagination
        per_page: Items per page
        db: Database session
        
    Returns:
        FileListResponseSchema: List of files with pagination info
    """
    try:
        file_service = get_file_service(db)
        files = await file_service.get_files_by_customer(customer_id)
        
        # Simple pagination
        total = len(files)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_files = files[start:end]
        
        return FileListResponseSchema(
            files=[FileResponseSchema.model_validate(f) for f in paginated_files],
            total=total,
            page=page,
            per_page=per_page,
            has_next=end < total,
            has_prev=start > 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer files: {str(e)}"
        )


@router.get("/{file_id}/access-logs", response_model=List[FileAccessLogSchema])
async def get_file_access_logs(
    file_id: str,
    request: Request,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get access logs for a specific file.
    
    Args:
        file_id: ID of the file
        request: FastAPI request object
        limit: Maximum number of logs to return
        db: Database session
        
    Returns:
        List[FileAccessLogSchema]: List of access logs
        
    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        # Placeholder user ID
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        
        file_service = get_file_service(db)
        access_logs = await file_service.get_access_logs(file_id, user_id, limit)
        
        return [FileAccessLogSchema.model_validate(log) for log in access_logs]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access logs: {str(e)}"
        )


@router.get("/summary/{customer_id}", response_model=FileSummarySchema)
async def get_file_summary(
    customer_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get file statistics for a customer.
    
    Args:
        customer_id: ID of the customer
        request: FastAPI request object
        db: Database session
        
    Returns:
        FileSummarySchema: File statistics
    """
    try:
        file_service = get_file_service(db)
        summary = await file_service.get_file_summary(customer_id)
        
        return FileSummarySchema.model_validate(summary)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file summary: {str(e)}"
        )


@router.post("/search", response_model=FileListResponseSchema)
async def search_files(
    search_params: FileSearchSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Search files with various criteria.
    
    Args:
        search_params: Search parameters
        request: FastAPI request object
        db: Database session
        
    Returns:
        FileListResponseSchema: Search results with pagination
    """
    try:
        # Placeholder user ID
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        
        file_service = get_file_service(db)
        
        # Build search filters
        filters = {
            "document_type": search_params.document_type,
            "date_from": search_params.date_from,
            "date_to": search_params.date_to
        }
        
        files = await file_service.search_files(
            query=search_params.query,
            customer_id=user_id,
            **filters
        )
        
        # Apply pagination
        total = len(files)
        start = (search_params.page - 1) * search_params.per_page
        end = start + search_params.per_page
        paginated_files = files[start:end]
        
        return FileListResponseSchema(
            files=[FileResponseSchema.model_validate(f) for f in paginated_files],
            total=total,
            page=search_params.page,
            per_page=search_params.per_page,
            has_next=end < total,
            has_prev=start > 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search files: {str(e)}"
        )


@router.get("/validation-rules", response_model=List[FileValidationRuleSchema])
async def get_validation_rules(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get file validation rules for all document types.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        List[FileValidationRuleSchema]: Validation rules
    """
    try:
        # This would typically come from the validation rule repository
        # For now, return the default rules
        default_rules = file_validation_service.default_rules
        
        rules = []
        for doc_type, rule in default_rules.items():
            rules.append(FileValidationRuleSchema(
                id=uuid.uuid4(),  # Placeholder ID
                document_type=doc_type,
                max_file_size=rule["max_file_size"],
                allowed_mime_types=rule["allowed_mime_types"],
                required_file_extensions=rule["required_extensions"],
                max_pages=rule.get("max_pages"),
                requires_scan=rule.get("requires_scan", True),
                requires_encryption=rule.get("requires_encryption", True),
                retention_days=None
            ))
        
        return rules
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation rules: {str(e)}"
        )