"""File management tools."""
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from database import get_db_session
from app.models import ClaimFile, Claim
from app.repositories.file_repository import FileRepository


async def list_claim_files(claim_id: str) -> Dict[str, Any]:
    """List all files for a claim.
    
    Args:
        claim_id: Claim ID (UUID)
    
    Returns:
        List of files with metadata
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(
                select(ClaimFile)
                .where(ClaimFile.claim_id == claim_id)
                .order_by(ClaimFile.uploaded_at.desc())
            )
            files = result.scalars().all()
            
            return {
                "success": True,
                "claim_id": claim_id,
                "count": len(files),
                "files": [
                    {
                        "id": str(f.id),
                        "filename": f.filename,
                        "document_type": f.document_type,
                        "file_size": int(f.file_size) if f.file_size else 0,
                        "mime_type": f.mime_type,
                        "encryption_status": f.encryption_status,
                        "status": f.status,
                        "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
                    }
                    for f in files
                ],
                "message": f"Found {len(files)} files for claim {claim_id}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list claim files"
        }


async def get_file_metadata(file_id: str) -> Dict[str, Any]:
    """Get detailed file metadata.
    
    Args:
        file_id: File ID (UUID)
    
    Returns:
        Complete file metadata
    """
    try:
        async with get_db_session() as session:
            repo = FileRepository(session)
            file = await repo.get_by_id(file_id)
            
            if not file:
                return {
                    "success": False,
                    "message": f"File not found: {file_id}"
                }
            
            return {
                "success": True,
                "file": {
                    "id": str(file.id),
                    "claim_id": str(file.claim_id),
                    "filename": file.filename,
                    "original_filename": file.original_filename,
                    "document_type": file.document_type,
                    "file_size": int(file.file_size) if file.file_size else 0,
                    "mime_type": file.mime_type,
                    "storage_path": file.storage_path,
                    "encryption_status": file.encryption_status,
                    "file_hash": file.file_hash,
                    "status": file.status,
                    "validation_status": file.validation_status,
                    "uploaded_at": file.uploaded_at.isoformat() if file.uploaded_at else None,
                    "uploaded_by": str(file.uploaded_by) if file.uploaded_by else None
                },
                "message": "File metadata retrieved successfully"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve file metadata"
        }


async def get_file_validation_status(file_id: str) -> Dict[str, Any]:
    """Get file validation and security scan status.
    
    Args:
        file_id: File ID (UUID)
    
    Returns:
        Validation and scan results
    """
    try:
        async with get_db_session() as session:
            repo = FileRepository(session)
            file = await repo.get_by_id(file_id)
            
            if not file:
                return {
                    "success": False,
                    "message": f"File not found: {file_id}"
                }
            
            return {
                "success": True,
                "file_id": str(file.id),
                "filename": file.filename,
                "validation": {
                    "status": file.validation_status,
                    "encryption_status": file.encryption_status,
                    "file_hash": file.file_hash,
                    "access_level": file.access_level
                },
                "file_status": {
                    "status": file.status,
                    "rejection_reason": file.rejection_reason
                },
                "message": f"File validation status: {file.validation_status}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get file validation status"
        }


async def approve_file(file_id: str, admin_id: Optional[str] = None) -> Dict[str, Any]:
    """Approve a file (admin action).
    
    Args:
        file_id: File ID (UUID)
        admin_id: Admin user ID (optional)
    
    Returns:
        Approval status
    """
    try:
        async with get_db_session() as session:
            repo = FileRepository(session)
            file = await repo.get_by_id(file_id)
            
            if not file:
                return {
                    "success": False,
                    "message": f"File not found: {file_id}"
                }
            
            # Update validation status and file status
            file.validation_status = "approved"
            file.status = "approved"
            await session.commit()
            
            return {
                "success": True,
                "file_id": str(file.id),
                "filename": file.filename,
                "validation_status": "approved",
                "approved_by": admin_id,
                "message": f"File approved: {file.filename}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to approve file"
        }


async def reject_file(
    file_id: str,
    reason: str,
    admin_id: Optional[str] = None
) -> Dict[str, Any]:
    """Reject a file (admin action).
    
    Args:
        file_id: File ID (UUID)
        reason: Rejection reason
        admin_id: Admin user ID (optional)
    
    Returns:
        Rejection status
    """
    try:
        async with get_db_session() as session:
            repo = FileRepository(session)
            file = await repo.get_by_id(file_id)
            
            if not file:
                return {
                    "success": False,
                    "message": f"File not found: {file_id}"
                }
            
            # Update validation status and rejection reason
            file.validation_status = "rejected"
            file.status = "rejected"
            file.rejection_reason = reason
            await session.commit()
            
            return {
                "success": True,
                "file_id": str(file.id),
                "filename": file.filename,
                "validation_status": "rejected",
                "reason": reason,
                "rejected_by": admin_id,
                "message": f"File rejected: {file.filename}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to reject file"
        }


async def delete_file(file_id: str) -> Dict[str, Any]:
    """Delete a file.
    
    Args:
        file_id: File ID (UUID)
    
    Returns:
        Deletion status
    """
    try:
        async with get_db_session() as session:
            repo = FileRepository(session)
            file = await repo.get_by_id(file_id)
            
            if not file:
                return {
                    "success": False,
                    "message": f"File not found: {file_id}"
                }
            
            filename = file.filename
            await repo.delete(file_id)
            
            return {
                "success": True,
                "file_id": file_id,
                "filename": filename,
                "message": f"File deleted: {filename}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to delete file"
        }


async def get_files_by_status(
    validation_status: str,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """Get files by validation status.
    
    Args:
        validation_status: Status (pending, approved, rejected)
        limit: Number of results (default: 10)
        offset: Number to skip (default: 0)
    
    Returns:
        List of files with given status
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(
                select(ClaimFile)
                .where(ClaimFile.validation_status == validation_status)
                .order_by(ClaimFile.uploaded_at.desc())
                .limit(limit)
                .offset(offset)
            )
            files = result.scalars().all()
            
            return {
                "success": True,
                "validation_status": validation_status,
                "count": len(files),
                "files": [
                    {
                        "id": str(f.id),
                        "claim_id": str(f.claim_id),
                        "filename": f.filename,
                        "document_type": f.document_type,
                        "file_size": f.file_size,
                        "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
                    }
                    for f in files
                ],
                "message": f"Found {len(files)} files with status '{validation_status}'"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get files by status"
        }
