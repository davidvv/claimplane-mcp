"""File service for handling document uploads and storage."""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import magic
from fastapi import UploadFile, HTTPException, status

from app.config import settings
from app.models import Document, Claim
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FileService:
    """Service for handling file uploads and storage."""
    
    def __init__(self, db: Session):
        """Initialize file service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.upload_dir = Path(settings.upload_dir)
        self._ensure_upload_directory()
    
    def _ensure_upload_directory(self):
        """Ensure upload directory exists."""
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Upload directory ensured: {self.upload_dir}")
        except Exception as e:
            logger.error(f"Error creating upload directory: {e}")
            raise
    
    def validate_file(self, file: UploadFile, document_type: str) -> dict:
        """Validate uploaded file.
        
        Args:
            file: Uploaded file
            document_type: Type of document (boarding_pass, receipt, etc.)
            
        Returns:
            dict: Validation results
        """
        errors = []
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        max_size = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            errors.append(f"File size exceeds {settings.max_file_size_mb}MB limit")
        
        # Check file type
        if file.content_type not in settings.allowed_file_types:
            errors.append(f"File type {file.content_type} not allowed")
        
        # Validate file extension
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            errors.append(f"File extension {file_extension} not allowed")
        
        # Check MIME type using python-magic
        try:
            file_content = file.file.read()
            file.file.seek(0)  # Reset for later use
            
            detected_mime = magic.from_buffer(file_content, mime=True)
            if detected_mime not in settings.allowed_file_types:
                errors.append(f"Detected file type {detected_mime} not allowed")
        except Exception as e:
            logger.warning(f"Could not detect MIME type: {e}")
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return {
            "file_size": file_size,
            "mime_type": file.content_type,
            "extension": file_extension
        }
    
    def generate_filename(self, original_filename: str, document_type: str) -> str:
        """Generate a unique filename for uploaded file.
        
        Args:
            original_filename: Original filename
            document_type: Type of document
            
        Returns:
            str: Generated filename
        """
        # Generate unique ID
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Get file extension
        extension = Path(original_filename).suffix
        
        # Generate new filename
        filename = f"{document_type}_{timestamp}_{unique_id}{extension}"
        
        return filename
    
    def save_file_to_disk(self, file: UploadFile, filename: str) -> str:
        """Save file to disk.
        
        Args:
            file: Uploaded file
            filename: Filename to save as
            
        Returns:
            str: File path
        """
        try:
            file_path = self.upload_dir / filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            logger.info(f"File saved: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise ValueError(f"Error saving file: {e}")
    
    def validate_and_save_file(
        self,
        user_id: int,
        file: UploadFile,
        document_type: str,
        claim_id: Optional[str] = None
    ) -> Document:
        """Validate and save a file.
        
        Args:
            user_id: User ID
            file: Uploaded file
            document_type: Type of document
            claim_id: Optional claim ID to associate with
            
        Returns:
            Document: Saved document record
        """
        try:
            # Validate file
            validation_result = self.validate_file(file, document_type)
            
            # Find claim if claim_id provided
            claim = None
            if claim_id:
                claim = self.db.query(Claim).filter(Claim.claim_id == claim_id).first()
                if not claim:
                    raise ValueError(f"Claim {claim_id} not found")
            
            # Generate filename
            filename = self.generate_filename(file.filename, document_type)
            
            # Save file to disk
            file_path = self.save_file_to_disk(file, filename)
            
            # Create document record
            document = Document(
                claim_id=claim.id if claim else None,
                filename=filename,
                original_filename=file.filename,
                file_size=validation_result["file_size"],
                mime_type=validation_result["mime_type"],
                file_path=file_path,
                document_type=document_type
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Document saved: {document.id} - {filename}")
            return document
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error validating and saving file: {e}")
            raise ValueError(f"Error processing file: {e}")
    
    def get_document(self, document_id: int) -> Optional[Document]:
        """Get document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Optional[Document]: Document if found
        """
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_claim_documents(self, claim_id: str) -> List[Document]:
        """Get all documents for a claim.
        
        Args:
            claim_id: Claim ID
            
        Returns:
            List[Document]: Documents for the claim
        """
        claim = self.db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            return []
        
        return self.db.query(Document).filter(Document.claim_id == claim.id).all()
    
    def delete_document(self, document_id: int) -> bool:
        """Delete a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            document = self.get_document(document_id)
            if not document:
                return False
            
            # Delete file from disk
            try:
                file_path = Path(document.file_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"File deleted: {file_path}")
            except Exception as e:
                logger.warning(f"Could not delete file {document.file_path}: {e}")
            
            # Delete from database
            self.db.delete(document)
            self.db.commit()
            
            logger.info(f"Document deleted: {document_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting document: {e}")
            raise
    
    def cleanup_old_files(self, days_old: int = 30) -> int:
        """Clean up old uploaded files.
        
        Args:
            days_old: Age in days to consider for cleanup
            
        Returns:
            int: Number of files cleaned up
        """
        try:
            cutoff_date = datetime.utcnow().timestamp() - (days_old * 24 * 60 * 60)
            old_documents = self.db.query(Document).filter(
                Document.uploaded_at < datetime.fromtimestamp(cutoff_date)
            ).all()
            
            cleaned_count = 0
            for document in old_documents:
                if self.delete_document(document.id):
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            raise