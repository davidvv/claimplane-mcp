"""File service for managing file operations."""
import os
import uuid
import io
import hashlib
import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime, timedelta

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClaimFile, FileAccessLog
from app.repositories.file_repository import FileRepository, FileAccessLogRepository, FileValidationRuleRepository
from app.services.encryption_service import encryption_service
from app.services.file_validation_service import file_validation_service
from app.services.nextcloud_service import nextcloud_service
from app.exceptions import NextcloudRetryableError, NextcloudPermanentError
from app.config import config


class FileService:
    """Service for file management operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize file service with database session."""
        self.db = db
        self.file_repo = FileRepository(db)
        self.access_log_repo = FileAccessLogRepository(db)
        self.validation_rule_repo = FileValidationRuleRepository(db)

    async def _get_file_size(self, file: UploadFile) -> int:
        """Get file size without loading content into memory."""
        current_pos = file.file.tell() if hasattr(file.file, 'tell') else 0
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(current_pos)  # Restore position
        return size

    async def _read_file_chunks(self, file: UploadFile, chunk_size: int) -> AsyncGenerator[bytes, None]:
        """Read file in chunks for memory-efficient processing."""
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            yield chunk

    async def _calculate_rolling_hash(self, chunks: AsyncGenerator[bytes, None]) -> str:
        """Calculate rolling hash for integrity verification across chunks."""
        hash_obj = hashlib.sha256()
        async for chunk in chunks:
            hash_obj.update(chunk)
        return hash_obj.hexdigest()

    async def _handle_upload_error(self, file: UploadFile, error: Exception, partial_path: str = None) -> None:
        """Handle upload errors and cleanup partial uploads."""
        try:
            # Log the error
            print(f"Upload error occurred: {str(error)}")

            # If we have a partial upload path, attempt cleanup
            if partial_path:
                try:
                    await nextcloud_service.cancel_upload(partial_path)
                    print(f"Cleaned up partial upload: {partial_path}")
                except Exception as cleanup_error:
                    print(f"Failed to cleanup partial upload {partial_path}: {str(cleanup_error)}")

            # Reset file position for potential retry
            if hasattr(file.file, 'seek'):
                file.file.seek(0)

        except Exception as e:
            print(f"Error during upload error handling: {str(e)}")

    async def _retry_chunk_upload(self, chunk_data: bytes, remote_path: str, max_retries: int = 3) -> bool:
        """Retry uploading a specific chunk with exponential backoff."""
        for attempt in range(max_retries):
            try:
                # Use the existing upload method for the chunk
                await nextcloud_service.upload_file(chunk_data, remote_path, overwrite=True)
                return True
            except NextcloudRetryableError:
                if attempt < max_retries - 1:
                    delay = (2 ** attempt) * 0.5  # Exponential backoff starting at 0.5s
                    await asyncio.sleep(delay)
                    continue
                else:
                    return False
            except NextcloudPermanentError:
                return False

        return False

    async def _upload_large_file_streaming(
        self,
        file: UploadFile,
        claim_id: str,
        customer_id: str,
        document_type: str,
        description: Optional[str],
        access_level: str,
        file_size: int
    ) -> ClaimFile:
        """Upload large file using streaming approach with progress tracking."""
        # Validate large file first
        validation_result = await self._validate_large_file_streaming(file, document_type, file_size)

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

        # Initialize encryption context for streaming
        encryption_context = encryption_service.create_streaming_context()

        # Create temporary buffer for staging
        temp_buffer = io.BytesIO()
        total_processed = 0
        rolling_hash = hashlib.sha256()

        # Progress tracking
        progress_chunks = 0
        total_chunks = (file_size + config.CHUNK_SIZE - 1) // config.CHUNK_SIZE

        try:
            # Process file in chunks
            async for chunk in self._read_file_chunks(file, config.CHUNK_SIZE):
                # Update rolling hash
                rolling_hash.update(chunk)

                # Encrypt chunk and add to buffer
                encrypted_chunk = encryption_service.encrypt_chunk(chunk, encryption_context)
                temp_buffer.write(encrypted_chunk)

                total_processed += len(chunk)
                progress_chunks += 1

                # Log progress for large files
                if progress_chunks % 10 == 0 or total_processed >= file_size:
                    print(f"Processed {total_processed}/{file_size} bytes ({progress_chunks}/{total_chunks} chunks)")

                # Upload when buffer is full or file is complete
                if temp_buffer.tell() >= config.CHUNK_SIZE or total_processed >= file_size:
                    # Upload current buffer content
                    temp_buffer.seek(0)
                    buffer_content = temp_buffer.read()
                    temp_buffer.seek(0)
                    temp_buffer.truncate(0)

                    # Upload chunk to Nextcloud (this would need streaming support in nextcloud_service)
                    # For now, we'll accumulate and upload at the end
                    pass

            # Final upload of remaining content
            if temp_buffer.tell() > 0:
                temp_buffer.seek(0)
                final_content = temp_buffer.read()
                # Upload final chunk
                upload_result = await nextcloud_service.upload_file(
                    file_content=final_content,
                    remote_path=storage_path
                )

                # Verify upload integrity for large files if enabled
                if config.UPLOAD_VERIFICATION_ENABLED:
                    try:
                        verification_result = await nextcloud_service.verify_upload_integrity(
                            original_content=final_content,
                            remote_path=storage_path,
                            verification_strategy="auto"
                        )

                        if not verification_result["verified"]:
                            # Verification failed - attempt cleanup and retry
                            try:
                                await nextcloud_service.delete_file(storage_path)
                            except Exception as cleanup_error:
                                print(f"Failed to cleanup after verification failure: {str(cleanup_error)}")

                            error_msg = f"Upload verification failed: {verification_result.get('error', 'Unknown verification error')}"
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error_msg
                            )

                        print(f"Upload verification successful for {storage_path} using {verification_result['strategy_used']} strategy")

                    except HTTPException:
                        raise
                    except Exception as verification_error:
                        print(f"Upload verification error for {storage_path}: {str(verification_error)}")
            else:
                # Handle empty file case
                upload_result = await nextcloud_service.upload_file(
                    file_content=b"",
                    remote_path=storage_path
                )

            # Create file record
            file_record = ClaimFile(
                id=uuid.uuid4(),
                claim_id=uuid.UUID(claim_id),
                customer_id=uuid.UUID(customer_id),
                filename=secure_filename,
                original_filename=file.filename,
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                file_hash=rolling_hash.hexdigest(),
                document_type=document_type,
                storage_provider="nextcloud",
                storage_path=storage_path,
                nextcloud_file_id=upload_result.get("file_id"),
                access_level=access_level,
                status="uploaded",
                validation_status="pending",
                description=description,
                uploaded_by=uuid.UUID(customer_id),
                expires_at=datetime.utcnow() + timedelta(days=365)
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
        except NextcloudRetryableError as e:
            # Retryable errors should be treated as service unavailable
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"File upload failed due to temporary Nextcloud error: {str(e)}"
            )
        except NextcloudPermanentError as e:
            # Permanent errors should use the original status code
            raise HTTPException(
                status_code=e.status_code,
                detail=f"File upload failed due to permanent Nextcloud error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File upload failed: {str(e)}"
            )
        finally:
            temp_buffer.close()

    async def _validate_large_file_streaming(
        self,
        file: UploadFile,
        document_type: str,
        file_size: int
    ) -> Dict[str, Any]:
        """Validate large file using streaming approach."""
        # For large files, we'll do basic validation first
        if file_size > config.MAX_FILE_SIZE:
            return {
                "valid": False,
                "errors": [f"File size {file_size} exceeds maximum allowed size {config.MAX_FILE_SIZE}"],
                "file_hash": None,
                "mime_type": file.content_type
            }

        # For large files, we'll calculate hash during streaming instead of upfront
        # Just do basic validation for now
        return {
            "valid": True,
            "errors": [],
            "file_hash": None,  # Will be calculated during streaming
            "mime_type": file.content_type or "application/octet-stream"
        }
    
    async def upload_file(self, file: UploadFile, claim_id: str, customer_id: str,
                           document_type: str, description: Optional[str] = None,
                           access_level: str = "private") -> ClaimFile:
        """Upload and process a file with size-based routing for memory efficiency."""
        try:
            # Get file size without loading content into memory
            file_size = await self._get_file_size(file)

            # Route based on file size
            if file_size >= config.STREAMING_THRESHOLD:
                # Use streaming upload for large files
                return await self._upload_large_file_streaming(
                    file=file,
                    claim_id=claim_id,
                    customer_id=customer_id,
                    document_type=document_type,
                    description=description,
                    access_level=access_level,
                    file_size=file_size
                )
            else:
                # Use regular upload for smaller files
                return await self._upload_small_file(
                    file=file,
                    claim_id=claim_id,
                    customer_id=customer_id,
                    document_type=document_type,
                    description=description,
                    access_level=access_level
                )

        except HTTPException:
            raise
        except NextcloudRetryableError as e:
            # Retryable errors should be treated as service unavailable
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"File upload failed due to temporary Nextcloud error: {str(e)}"
            )
        except NextcloudPermanentError as e:
            # Permanent errors should use the original status code
            raise HTTPException(
                status_code=e.status_code,
                detail=f"File upload failed due to permanent Nextcloud error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File upload failed: {str(e)}"
            )

    async def _upload_small_file(self, file: UploadFile, claim_id: str, customer_id: str,
                                document_type: str, description: Optional[str] = None,
                                access_level: str = "private") -> ClaimFile:
        """Upload small file using traditional approach."""
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

            # Generate secure filename and storage path
            secure_filename = encryption_service.generate_secure_filename(file.filename)
            storage_path = f"flight_claims/{claim_id}/{secure_filename}"

            # Encrypt file content
            encrypted_content = encryption_service.encrypt_file_content(file_content)

            # Verify encryption/decryption integrity using original data
            if not encryption_service.verify_integrity(encrypted_content, validation_result["file_hash"], original_data=file_content):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="File encryption/decryption integrity check failed"
                )

            # Upload to Nextcloud
            upload_result = await nextcloud_service.upload_file(
                file_content=encrypted_content,
                remote_path=storage_path
            )

            # Verify upload integrity if enabled
            if config.UPLOAD_VERIFICATION_ENABLED:
                try:
                    verification_result = await nextcloud_service.verify_upload_integrity(
                        original_content=encrypted_content,
                        remote_path=storage_path,
                        verification_strategy="auto"
                    )

                    if not verification_result["verified"]:
                        # Verification failed - attempt cleanup and retry
                        try:
                            await nextcloud_service.delete_file(storage_path)
                        except Exception as cleanup_error:
                            print(f"Failed to cleanup after verification failure: {str(cleanup_error)}")

                        # Raise appropriate error based on verification failure
                        error_msg = f"Upload verification failed: {verification_result.get('error', 'Unknown verification error')}"
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_msg
                        )

                    # Log successful verification
                    print(f"Upload verification successful for {storage_path} using {verification_result['strategy_used']} strategy")

                except HTTPException:
                    raise
                except Exception as verification_error:
                    # Log verification error but don't fail the upload unless it's critical
                    print(f"Upload verification error for {storage_path}: {str(verification_error)}")
                    # Continue with upload - verification errors are logged but not fatal

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
        except NextcloudRetryableError as e:
            # Retryable errors should be treated as service unavailable
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"File upload failed due to temporary Nextcloud error: {str(e)}"
            )
        except NextcloudPermanentError as e:
            # Permanent errors should use the original status code
            raise HTTPException(
                status_code=e.status_code,
                detail=f"File upload failed due to permanent Nextcloud error: {str(e)}"
            )
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
            
            # Verify integrity (fallback to decryption method since original data not available)
            if not encryption_service.verify_integrity(encrypted_content, file_record.file_hash):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="File integrity verification failed - file may be corrupted or tampered with"
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
        except NextcloudRetryableError as e:
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
            # Retryable errors should be treated as service unavailable
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"File download failed due to temporary Nextcloud error: {str(e)}"
            )
        except NextcloudPermanentError as e:
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
            # Permanent errors should use the original status code
            raise HTTPException(
                status_code=e.status_code,
                detail=f"File download failed due to permanent Nextcloud error: {str(e)}"
            )
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
        except NextcloudRetryableError as e:
            # Retryable errors should be treated as service unavailable
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"File deletion failed due to temporary Nextcloud error: {str(e)}"
            )
        except NextcloudPermanentError as e:
            # Permanent errors should use the original status code
            raise HTTPException(
                status_code=e.status_code,
                detail=f"File deletion failed due to permanent Nextcloud error: {str(e)}"
            )
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
    
    async def upload_orphan_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        document_type: str,
        customer_id: Optional[str] = None
    ) -> ClaimFile:
        """
        Upload a file without associating it to a claim (for OCR pre-upload).
        
        Files uploaded via this method are stored in temp_uploads/ and have a 24-hour expiry.
        They should be linked to a claim via link_file_to_claim() within 24 hours,
        otherwise they will be cleaned up by the orphan file cleanup task.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            mime_type: MIME type of the file
            document_type: Type of document (boarding_pass, etc.)
            customer_id: Optional customer ID if user is authenticated
            
        Returns:
            ClaimFile record with claim_id=None
        """
        try:
            # Validate file
            validation_result = await file_validation_service.validate_file(
                file_content=file_content,
                filename=filename,
                document_type=document_type,
                declared_mime_type=mime_type,
                file_size=len(file_content)
            )
            
            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File validation failed: {'; '.join(validation_result['errors'])}"
                )
            
            # Generate secure filename and storage path for temp uploads
            secure_filename = encryption_service.generate_secure_filename(filename)
            storage_path = f"temp_uploads/{secure_filename}"
            
            # Encrypt file content
            encrypted_content = encryption_service.encrypt_file_content(file_content)
            
            # Verify encryption/decryption integrity using original data
            if not encryption_service.verify_integrity(encrypted_content, validation_result["file_hash"], original_data=file_content):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="File encryption/decryption integrity check failed"
                )
            
            # Upload to Nextcloud
            upload_result = await nextcloud_service.upload_file(
                file_content=encrypted_content,
                remote_path=storage_path
            )
            
            # Create file record WITHOUT claim_id
            file_record = ClaimFile(
                id=uuid.uuid4(),
                claim_id=None,  # NULL - will be linked later
                customer_id=uuid.UUID(customer_id) if customer_id else None,
                filename=secure_filename,
                original_filename=filename,
                file_size=len(file_content),
                mime_type=validation_result["mime_type"],
                file_hash=validation_result["file_hash"],
                document_type=document_type,
                storage_provider="nextcloud",
                storage_path=storage_path,
                nextcloud_file_id=upload_result.get("file_id"),
                access_level="private",
                status="uploaded",
                validation_status="pending",
                uploaded_by=uuid.UUID(customer_id) if customer_id else None,
                expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry for orphans
            )
            
            self.db.add(file_record)
            await self.db.flush()
            
            return file_record
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Orphan file upload failed: {str(e)}"
            )

    async def upload_generated_document(
        self,
        file_content: bytes,
        filename: str,
        claim_id: str,
        customer_id: str,
        document_type: str,
        mime_type: str = "application/pdf",
        description: Optional[str] = None
    ) -> ClaimFile:
        """
        Upload a system-generated document (e.g., signed POA).
        
        Args:
            file_content: Raw bytes of the generated file
            filename: Desired filename
            claim_id: Claim ID to link to
            customer_id: Customer ID who owns the claim
            document_type: Type of document
            mime_type: MIME type (default application/pdf)
            description: Optional description
            
        Returns:
            Created ClaimFile record
        """
        try:
            # Generate secure filename
            secure_filename = encryption_service.generate_secure_filename(filename)
            storage_path = f"flight_claims/{claim_id}/{secure_filename}"
            
            # Calculate hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Encrypt content
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
                original_filename=filename,
                file_size=len(file_content),
                mime_type=mime_type,
                file_hash=file_hash,
                document_type=document_type,
                storage_provider="nextcloud",
                storage_path=storage_path,
                nextcloud_file_id=upload_result.get("file_id"),
                access_level="private",
                status="uploaded",
                validation_status="validated",  # System generated files are auto-validated
                description=description or "System generated document",
                uploaded_by=uuid.UUID(customer_id),
                expires_at=datetime.utcnow() + timedelta(days=3650)  # 10 years retention
            )
            
            self.db.add(file_record)
            await self.db.flush()
            
            # Log access
            await self.access_log_repo.log_access(
                file_id=file_record.id,
                user_id=uuid.UUID(customer_id),
                access_type="upload",
                ip_address=None,
                user_agent="System",
                access_status="success"
            )
            
            return file_record
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Generated document upload failed: {str(e)}"
            )
    
    async def link_file_to_claim(
        self,
        file_id: uuid.UUID,
        claim_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> ClaimFile:
        """
        Link an orphan file (from OCR) to a claim.
        
        This method:
        1. Retrieves the orphan file record
        2. Moves the file from temp_uploads/ to flight_claims/{claim_id}/
        3. Updates the file record with claim_id and customer_id
        4. Extends expiry to 1 year
        
        Args:
            file_id: ID of the orphan file to link
            claim_id: ID of the claim to link to
            customer_id: ID of the customer who owns the claim
            
        Returns:
            Updated ClaimFile record
            
        Raises:
            HTTPException: If file not found, already linked, or move operation fails
        """
        try:
            # Get the orphan file
            file_record = await self.file_repo.get_by_id(file_id)
            
            if not file_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
            
            if file_record.claim_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File already linked to a claim"
                )
            
            # Move file from temp path to claim path
            old_path = file_record.storage_path
            new_path = f"flight_claims/{claim_id}/{file_record.filename}"
            
            await nextcloud_service.move_file(old_path, new_path)
            
            # Update file record
            file_record.claim_id = claim_id
            file_record.customer_id = customer_id
            file_record.storage_path = new_path
            file_record.expires_at = datetime.utcnow() + timedelta(days=365)  # Extend to 1 year
            file_record.updated_at = datetime.utcnow()
            
            await self.db.flush()
            
            return file_record
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to link file to claim: {str(e)}"
            )


# Global file service factory
def get_file_service(db: AsyncSession) -> FileService:
    """Get file service instance."""
    return FileService(db)