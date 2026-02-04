"""Pydantic schemas for file management operations."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


class DocumentType(str, Enum):
    """Document type enumeration."""
    BOARDING_PASS = "boarding_pass"
    ID_DOCUMENT = "id_document"
    RECEIPT = "receipt"
    BANK_STATEMENT = "bank_statement"
    FLIGHT_TICKET = "flight_ticket"
    DELAY_CERTIFICATE = "delay_certificate"
    CANCELLATION_NOTICE = "cancellation_notice"
    LPOA = "lpoa"
    CLAIM_ASSIGNMENT = "claim_assignment"
    SERVICE_AGREEMENT = "service_agreement"
    OTHER = "other"


class FileStatus(str, Enum):
    """File status enumeration."""
    UPLOADED = "uploaded"
    SCANNING = "scanning"
    VALIDATED = "validated"
    REJECTED = "rejected"
    APPROVED = "approved"
    ARCHIVED = "archived"


class EncryptionStatus(str, Enum):
    """Encryption status enumeration."""
    ENCRYPTED = "encrypted"
    DECRYPTED = "decrypted"
    PENDING = "pending"


class AccessLevel(str, Enum):
    """Access level enumeration."""
    PUBLIC = "public"
    PRIVATE = "private"
    RESTRICTED = "restricted"


class FileUploadSchema(BaseModel):
    """Schema for file upload request."""
    
    claim_id: UUID = Field(..., description="ID of the associated claim")
    customer_id: UUID = Field(..., description="ID of the customer uploading the file")
    document_type: DocumentType = Field(..., description="Type of document being uploaded")
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650, description="Optional expiration period in days")
    
    class Config:
        populate_by_name = True


class FileUploadResponseSchema(BaseModel):
    """Schema for file upload response."""
    
    file_id: UUID = Field(..., description="ID of the uploaded file")
    status: str = Field(..., description="Upload status")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")
    document_type: DocumentType = Field(..., description="Type of document")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    share_url: Optional[str] = Field(None, description="Share URL if created")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    message: Optional[str] = Field(None, description="Additional message")
    existing_file_id: Optional[UUID] = Field(None, description="ID of existing file if duplicate")
    
    class Config:
        populate_by_name = True


class FileInfoSchema(BaseModel):
    """Schema for file information."""
    
    id: UUID
    claim_id: UUID = Field(..., alias="claimId")
    customer_id: UUID = Field(..., alias="customerId")
    filename: str = Field(..., alias="originalFilename")
    file_size: int = Field(..., alias="fileSize")
    mime_type: str = Field(..., alias="mimeType")
    document_type: DocumentType = Field(..., alias="documentType")
    status: FileStatus
    uploaded_at: datetime = Field(..., alias="uploadedAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    download_count: int = Field(..., alias="downloadCount")
    encryption_status: EncryptionStatus = Field(..., alias="encryptionStatus")
    storage_provider: str = Field(..., alias="storageProvider")
    validation_status: str = Field(..., alias="validationStatus")
    is_deleted: bool = Field(..., alias="isDeleted")
    share_url: Optional[str] = Field(None, alias="shareUrl")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class FileListResponseSchema(BaseModel):
    """Schema for file list response."""
    
    files: List[FileInfoSchema]
    total_count: int = Field(..., alias="totalCount")
    page: int = Field(default=1)
    page_size: int = Field(..., alias="pageSize")
    
    class Config:
        populate_by_name = True


class FileSearchSchema(BaseModel):
    """Schema for file search request."""
    
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    customer_id: Optional[UUID] = Field(None, description="Filter by customer ID")
    document_type: Optional[DocumentType] = Field(None, description="Filter by document type")
    status: Optional[FileStatus] = Field(None, description="Filter by file status")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum number of results")
    
    class Config:
        populate_by_name = True


class FileSummarySchema(BaseModel):
    """Schema for file summary statistics."""
    
    total_files: int = Field(..., alias="totalFiles")
    total_size: float = Field(..., alias="totalSize")
    avg_size: float = Field(..., alias="avgSize")
    status_breakdown: Dict[str, int] = Field(..., alias="statusBreakdown")
    document_type_breakdown: Dict[str, int] = Field(..., alias="documentTypeBreakdown")
    
    class Config:
        populate_by_name = True


class FileAccessLogSchema(BaseModel):
    """Schema for file access log entry."""
    
    id: UUID
    file_id: UUID = Field(..., alias="fileId")
    user_id: Optional[UUID] = Field(None, alias="userId")
    access_type: str = Field(..., alias="accessType")
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    user_agent: Optional[str] = Field(None, alias="userAgent")
    access_status: str = Field(..., alias="accessStatus")
    failure_reason: Optional[str] = Field(None, alias="failureReason")
    access_time: datetime = Field(..., alias="accessTime")
    country_code: Optional[str] = Field(None, alias="countryCode")
    city: Optional[str] = Field(None, alias="city")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class FileDeleteResponseSchema(BaseModel):
    """Schema for file deletion response."""
    
    success: bool
    message: str
    file_id: UUID = Field(..., alias="fileId")
    
    class Config:
        populate_by_name = True


class FileValidationRuleSchema(BaseModel):
    """Schema for file validation rule."""
    
    id: UUID
    document_type: DocumentType = Field(..., alias="documentType")
    max_file_size: int = Field(..., alias="maxFileSize")
    allowed_mime_types: List[str] = Field(..., alias="allowedMimeTypes")
    required_file_extensions: List[str] = Field(..., alias="requiredFileExtensions")
    max_pages: Optional[int] = Field(None, alias="maxPages")
    requires_ocr: bool = Field(..., alias="requiresOcr")
    requires_scan: bool = Field(..., alias="requiresScan")
    retention_days: Optional[int] = Field(None, alias="retentionDays")
    is_active: bool = Field(..., alias="isActive")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class FileUploadErrorSchema(BaseModel):
    """Schema for file upload error response."""
    
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    class Config:
        populate_by_name = True


class FileDownloadResponseSchema(BaseModel):
    """Schema for file download response."""
    
    file_content: bytes = Field(..., alias="fileContent")
    filename: str
    mime_type: str = Field(..., alias="mimeType")
    file_size: int = Field(..., alias="fileSize")
    
    class Config:
        populate_by_name = True


# Query parameter schemas
class FileQueryParams(BaseModel):
    """Schema for file query parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, alias="pageSize", description="Items per page")
    include_deleted: bool = Field(default=False, alias="includeDeleted", description="Include deleted files")
    sort_by: Optional[str] = Field(None, alias="sortBy", description="Sort field")
    sort_order: Optional[str] = Field("desc", alias="sortOrder", description="Sort order (asc/desc)")
    
    class Config:
        populate_by_name = True


class FileAccessType(str, Enum):
    """File access type enumeration."""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    VIEW = "view"
    SHARE = "share"
    DELETE = "delete"
    RESTORE = "restore"
    UPDATE = "update"


class FileAccessStatus(str, Enum):
    """File access status enumeration."""
    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"