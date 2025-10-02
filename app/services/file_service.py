"""File service for managing file operations."""
import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClaimFile, FileAccessLog
from app.repositories.file_repository import FileRepository, FileAccessLogRepository, FileValidationRuleRepository
from app.services.encryption_service import encryption_service
from app.services.file_validation_service import file_validation_service
from app.services.nextcloud_service import nextcloud_service


class FileService:
    """Service for file management operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize file service with database session."""
        self.db = db
        self.file_repo = FileRepository(db)
        self.access_log_repo = FileAccessLogRepository(db)
        self.validation_rule_repo = FileValidationRuleRepository(db)
    
    async def upload_file(self, file: UploadFile, claim_id: str, customer_id: str,
                         document_type: str, description: Optional[str] = None,
                         access_level: str = "private") -> ClaimFile:
        """Upload and process a file."""
        try:
            # Read file content
            file_content = await file.read()
            
            # Validate file
            validation_result = await file_validation_service.validate_file(
                file_content=file_content,
                filename=file.filename,
                document_type=document_type,
                declared_mime_type=file.content_type,
                file_size=len(file_content)
            )
            
            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File validation failed: {'; '.join(validation_result['errors'])}"
                )
            
            # Check for duplicate files
            existing_file = await self.file_repo.get_by_file_hash(validation_result["file_hash"])
            if existing_file:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="File already exists (duplicate detected)"
                )
            
            # Generate secure filename and storage path
            secure_filename = encryption_service.generate_secure_filename(file.filename)
            storage_path = f"flight_claims/{claim_id}/{secure_filename}"
            
            # Encrypt file content
            encrypted_content = encryption_service.encrypt_file_content(file_content)
            
            # Upload to Nextcloud
            upload_result = await nextcloud_service.upload_file(
                file_content=encrypted_content,
                remote_path=storage_path
            )
            
            # Create file record
            file_record = ClaimFile(
                id=uuid.uuid4(),
                claim_id=uuid.UUID(claim_id),
                customer_id=uuid.UUID(customer_id),
                filename=secure_filename,
                original_filename=file.filename,
                file_size=len(file_content),
                mime_type=validation_result["mime_type"],
                file_hash=validation_result["file_hash"],
                document_type=document_type,
                storage_provider="nextcloud",
                storage_path=storage_path,
                nextcloud_file_id=upload_result.get("file_id"),
                access_level=access_level,
                status="uploaded",
                validation_status="pending",
                description=description,
                uploaded_by=uuid.UUID(customer_id),
                expires_at=datetime.utcnow() + timedelta(days=365)  # 1 year default
            )
            
            # Save to database
            self.db.add(file_record)
            await self.db.flush()
            
            # Log access
            await self.access_log_repo.log_access(
                file_id=file_record.id,
                user_id=uuid.UUID(customer_id),
                access_type="upload",
                ip_address=None,  # Will be set by middleware
                user_agent=None,  # Will be set by middleware
                access_status="success"
            )
            
            return file_record
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File upload failed: {str(e)}"
            )
    
    async def download_file(self, file_id: str, user_id: str) -> tuple[bytes, ClaimFile]:
        """Download and decrypt a file."""
        try:
            # Get file record
            file_record = await self.file_repo.get_by_id(uuid.UUID(file_id))
            if not file_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
            
            # Check permissions (simplified - should be enhanced)
            if str(file_record.customer_id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Download from Nextcloud
            encrypted_content = await nextcloud_service.download_file(
                remote_path=file_record.storage_path
            )
            
            # Decrypt content
            decrypted_content = encryption_service.decrypt_file_content(encrypted_content)
            
            # Verify integrity
            if not encryption_service.verify_integrity(encrypted_content, file_record.file_hash):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="File integrity check failed"
                )
            
            # Update download count
            await self.file_repo.increment_download_count(file_record.id)
            
            # Log access
            await self.access_log_repo.log_access(
                file_id=file_record.id,
                user_id=uuid.UUID(user_id),
                access_type="download",
                ip_address=None,  # Will be set by middleware
                user_agent=None,  # Will be set by middleware
                access_status="success"
            )
            
            return decrypted_content, file_record
            
        except HTTPException:
            raise
        except Exception as e:
            # Log failed access
            await self.access_log_repo.log_access(
                file_id=uuid.UUID(file_id),
                user_id=uuid.UUID(user_id) if user_id else None,
                access_type="download",
                ip_address=None,
                user_agent=None,
                access_status="error",
                failure_reason=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File download failed: {str(e)}"
            )
    
    async def delete_file(self, file_id: str, user_id: str) -> bool:
        """Soft delete a file."""
        try:
            # Get file record
            file_record = await self.file_repo.get_by_id(uuid.UUID(file_id))
            if not file_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
            
            # Check permissions
            if str(file_record.customer_id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Soft delete (mark as deleted)
            file_record.is_deleted = 1
            file_record.deleted_at = datetime.utcnow()
            file_record.status = "archived"
            
            # Delete from Nextcloud
            await nextcloud_service.delete_file(file_record.storage_path)
            
            # Log access
            await self.access_log_repo.log_access(
                file_id=file_record.id,
                user_id=uuid.UUID(user_id),
                access_type="delete",
                ip_address=None,
                user_agent=None,
                access_status="success"
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File deletion failed: {str(e)}"
            )
    
    async def get_file_info(self, file_id: str, user_id: str) -> ClaimFile:
        """Get file information."""
        try:
            file_record = await self.file_repo.get_by_id(uuid.UUID(file_id))
            if not file_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
            
            # Check permissions
            if str(file_record.customer_id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Log access
            await self.access_log_repo.log_access(
                file_id=file_record.id,
                user_id=uuid.UUID(user_id),
                access_type="view",
                ip_address=None,
                user_agent=None,
                access_status="success"
            )
            
            return file_record
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get file info: {str(e)}"
            )
    
    async def get_files_by_claim(self, claim_id: str, user_id: str) -> List[ClaimFile]:
        """Get files for a specific claim."""
        try:
            files = await self.file_repo.get_by_claim_id(uuid.UUID(claim_id))
            
            # Filter by user permissions
            filtered_files = [f for f in files if str(f.customer_id) == user_id]
            
            return filtered_files
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get claim files: {str(e)}"
            )
    
    async def get_files_by_customer(self, customer_id: str) -> List[ClaimFile]:
        """Get files for a specific customer."""
        try:
            return await self.file_repo.get_by_customer_id(uuid.UUID(customer_id))
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get customer files: {str(e)}"
            )
    
    async def get_file_summary(self, customer_id: str) -> Dict[str, Any]:
        """Get file statistics for a customer."""
        try:
            return await self.file_repo.get_files_summary(uuid.UUID(customer_id))
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get file summary: {str(e)}"
            )
    
    async def search_files(self, query: str, customer_id: str, **filters) -> List[ClaimFile]:
        """Search files with various criteria."""
        try:
            return await self.file_repo.search_files(
                query=query,
                customer_id=uuid.UUID(customer_id),
                **filters
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search files: {str(e)}"
            )
    
    async def get_access_logs(self, file_id: str, user_id: str, limit: int = 100) -> List[FileAccessLog]:
        """Get access logs for a file."""
        try:
            # Get file to verify permissions
            file_record = await self.file_repo.get_by_id(uuid.UUID(file_id))
            if not file_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
            
            # Check permissions
            if str(file_record.customer_id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            return await self.access_log_repo.get_access_logs_by_file(
                file_id=uuid.UUID(file_id),
                limit=limit
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get access logs: {str(e)}"
            )


# Global file service factory
def get_file_service(db: AsyncSession) -> FileService:
    """Get file service instance."""
    return FileService(db)