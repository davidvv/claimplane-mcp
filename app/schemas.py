"""Pydantic schemas for request/response validation."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class AddressSchema(BaseModel):
    """Address schema for customer address information."""
    
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20, alias="postalCode")
    country: Optional[str] = Field(None, max_length=100)
    
    class Config:
        populate_by_name = True


class CustomerCreateSchema(BaseModel):
    """Schema for creating a new customer."""
    
    email: EmailStr
    first_name: str = Field(..., max_length=50, alias="firstName")
    last_name: str = Field(..., max_length=50, alias="lastName")
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[AddressSchema] = None
    
    class Config:
        populate_by_name = True


class CustomerUpdateSchema(BaseModel):
    """Schema for updating a customer (PUT - all fields required)."""
    
    email: EmailStr
    first_name: str = Field(..., max_length=50, alias="firstName")
    last_name: str = Field(..., max_length=50, alias="lastName")
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[AddressSchema] = None
    
    class Config:
        populate_by_name = True


class CustomerPatchSchema(BaseModel):
    """Schema for partially updating a customer (PATCH - only specified fields updated)."""
    
    # Use Union to allow both None and str, bypassing strict EmailStr validation
    email: Union[None, str] = None
    first_name: Optional[str] = Field(None, max_length=50, alias="firstName")
    last_name: Optional[str] = Field(None, max_length=50, alias="lastName")
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[AddressSchema] = None
    
    @validator('email', pre=True)
    def handle_empty_email(cls, v):
        """Convert empty strings to None to avoid validation errors."""
        if v == "" or (isinstance(v, str) and v.strip() == ""):
            return None  # Convert empty/whitespace strings to None
        return v
    
    @validator('email')
    def validate_email_if_provided(cls, v):
        """Validate email format only if a non-empty string is provided."""
        if v is not None:  # v is already filtered by pre-validator
            # Basic email validation - in a real app, use email-validator library
            if '@' not in v or '.' not in v.split('@')[-1]:
                raise ValueError("Invalid email format")
        return v
    
    class Config:
        populate_by_name = True


class CustomerResponseSchema(BaseModel):
    """Schema for customer response."""

    id: UUID
    email: EmailStr
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    phone: Optional[str]
    address: Optional[AddressSchema]
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        populate_by_name = True
        from_attributes = True


class HealthResponseSchema(BaseModel):
    """Schema for health check response."""
    
    status: str
    timestamp: datetime
    version: str


class FlightInfoSchema(BaseModel):
    """Flight information schema."""
    
    flight_number: str = Field(..., alias="flightNumber", min_length=3, max_length=10)
    airline: str = Field(..., max_length=100)
    departure_date: date = Field(..., alias="departureDate")
    departure_airport: str = Field(..., alias="departureAirport", min_length=3, max_length=3)
    arrival_airport: str = Field(..., alias="arrivalAirport", min_length=3, max_length=3)
    
    @validator('departure_airport', 'arrival_airport')
    def validate_airport_code(cls, v):
        """Validate airport codes are uppercase."""
        return v.upper()
    
    @validator('flight_number')
    def validate_flight_number(cls, v):
        """Validate flight number format."""
        return v.upper()
    
    class Config:
        populate_by_name = True


class ClaimCreateSchema(BaseModel):
    """Schema for creating a new claim."""
    
    customer_id: UUID = Field(..., alias="customerId")
    flight_info: FlightInfoSchema = Field(..., alias="flightInfo")
    incident_type: str = Field(..., alias="incidentType")
    notes: Optional[str] = None
    
    @validator('incident_type')
    def validate_incident_type(cls, v):
        """Validate incident type."""
        valid_types = ["delay", "cancellation", "denied_boarding", "baggage_delay"]
        if v not in valid_types:
            raise ValueError(f"Incident type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        populate_by_name = True


class ClaimUpdateSchema(BaseModel):
    """Schema for updating a claim (PUT - all fields required)."""
    
    customer_id: UUID = Field(..., alias="customerId")
    flight_info: FlightInfoSchema = Field(..., alias="flightInfo")
    incident_type: str = Field(..., alias="incidentType")
    notes: Optional[str] = None
    
    @validator('incident_type')
    def validate_incident_type(cls, v):
        """Validate incident type."""
        valid_types = ["delay", "cancellation", "denied_boarding", "baggage_delay"]
        if v not in valid_types:
            raise ValueError(f"Incident type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        populate_by_name = True


class ClaimPatchSchema(BaseModel):
    """Schema for partially updating a claim (PATCH - only specified fields updated)."""
    
    customer_id: Optional[UUID] = Field(None, alias="customerId")
    flight_info: Optional[FlightInfoSchema] = Field(None, alias="flightInfo")
    incident_type: Optional[str] = Field(None, alias="incidentType")
    notes: Optional[str] = None
    
    @validator('incident_type')
    def validate_incident_type(cls, v):
        """Validate incident type if provided."""
        if v is not None:
            valid_types = ["delay", "cancellation", "denied_boarding", "baggage_delay"]
            if v not in valid_types:
                raise ValueError(f"Incident type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        populate_by_name = True


class ClaimResponseSchema(BaseModel):
    """Schema for claim response."""

    id: UUID
    customer_id: UUID = Field(..., alias="customerId")
    flight_info: FlightInfoSchema = Field(..., alias="flightInfo")
    incident_type: str = Field(..., alias="incidentType")
    status: str
    compensation_amount: Optional[Decimal] = Field(None, alias="compensationAmount")
    currency: str = "EUR"
    notes: Optional[str]
    submitted_at: datetime = Field(..., alias="submittedAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    @classmethod
    def from_orm(cls, claim):
        """Create response from ORM model by constructing flightInfo from flat fields."""
        return cls(
            id=claim.id,
            customer_id=claim.customer_id,
            flight_info=FlightInfoSchema(
                flightNumber=claim.flight_number,
                airline=claim.airline,
                departureDate=claim.departure_date,
                departureAirport=claim.departure_airport,
                arrivalAirport=claim.arrival_airport
            ),
            incidentType=claim.incident_type,
            status=claim.status,
            compensationAmount=claim.compensation_amount,
            currency=claim.currency,
            notes=claim.notes,
            submittedAt=claim.submitted_at,
            updatedAt=claim.updated_at
        )

    class Config:
        populate_by_name = True
        from_attributes = True


class ClaimSubmitResponseSchema(BaseModel):
    """Schema for claim submission response with access token."""

    claim: ClaimResponseSchema
    access_token: str = Field(..., alias="accessToken")
    token_type: str = Field(default="bearer", alias="tokenType")

    class Config:
        populate_by_name = True
        from_attributes = True


class ClaimRequestSchema(BaseModel):
    """Schema for claim request with customer info."""
    
    customer_info: CustomerCreateSchema = Field(..., alias="customerInfo")
    flight_info: FlightInfoSchema = Field(..., alias="flightInfo")
    incident_type: str = Field(..., alias="incidentType")
    notes: Optional[str] = None
    
    @validator('incident_type')
    def validate_incident_type(cls, v):
        """Validate incident type."""
        valid_types = ["delay", "cancellation", "denied_boarding", "baggage_delay"]
        if v not in valid_types:
            raise ValueError(f"Incident type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        populate_by_name = True


class FileUploadSchema(BaseModel):
    """Schema for file upload requests."""
    
    claim_id: UUID = Field(..., description="ID of the claim this file belongs to")
    customer_id: UUID = Field(..., description="ID of the customer uploading the file")
    document_type: str = Field(..., description="Type of document being uploaded")
    description: Optional[str] = Field(None, max_length=500, description="Optional description of the file")
    access_level: str = Field("private", description="Access level for the file")
    
    @validator('document_type')
    def validate_document_type(cls, v):
        """Validate document type."""
        valid_types = [
            "boarding_pass", "id_document", "receipt", "bank_statement",
            "flight_ticket", "delay_certificate", "cancellation_notice", "other"
        ]
        if v not in valid_types:
            raise ValueError(f"Document type must be one of: {', '.join(valid_types)}")
        return v
    
    @validator('access_level')
    def validate_access_level(cls, v):
        """Validate access level."""
        valid_levels = ["public", "private", "restricted"]
        if v not in valid_levels:
            raise ValueError(f"Access level must be one of: {', '.join(valid_levels)}")
        return v


class FileResponseSchema(BaseModel):
    """Schema for file response."""
    
    id: UUID
    claim_id: UUID = Field(..., alias="claimId")
    customer_id: UUID = Field(..., alias="customerId")
    filename: str
    original_filename: str = Field(..., alias="originalFilename")
    file_size: int = Field(..., alias="fileSize")
    mime_type: str = Field(..., alias="mimeType")
    document_type: str = Field(..., alias="documentType")
    status: str
    access_level: str = Field(..., alias="accessLevel")
    download_count: int = Field(..., alias="downloadCount")
    uploaded_at: datetime = Field(..., alias="uploadedAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    is_deleted: bool = Field(..., alias="isDeleted")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class FileListResponseSchema(BaseModel):
    """Schema for file list response."""
    
    files: List[FileResponseSchema]
    total: int
    page: int
    per_page: int = Field(..., alias="perPage")
    has_next: bool = Field(..., alias="hasNext")
    has_prev: bool = Field(..., alias="hasPrev")


class FileAccessLogSchema(BaseModel):
    """Schema for file access log."""
    
    id: UUID
    file_id: UUID = Field(..., alias="fileId")
    access_type: str = Field(..., alias="accessType")
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    access_status: str = Field(..., alias="accessStatus")
    access_time: datetime = Field(..., alias="accessTime")
    country_code: Optional[str] = Field(None, alias="countryCode")
    city: Optional[str] = Field(None, alias="city")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class FileSearchSchema(BaseModel):
    """Schema for file search requests."""
    
    query: Optional[str] = None
    claim_id: Optional[UUID] = Field(None, alias="claimId")
    customer_id: Optional[UUID] = Field(None, alias="customerId")
    document_type: Optional[str] = Field(None, alias="documentType")
    status: Optional[str] = None
    date_from: Optional[datetime] = Field(None, alias="dateFrom")
    date_to: Optional[datetime] = Field(None, alias="dateTo")
    page: int = 1
    per_page: int = Field(20, alias="perPage")
    
    @validator('per_page')
    def validate_per_page(cls, v):
        """Validate per page value."""
        if v < 1 or v > 100:
            raise ValueError("per_page must be between 1 and 100")
        return v


class FileValidationRuleSchema(BaseModel):
    """Schema for file validation rules."""
    
    id: UUID
    document_type: str = Field(..., alias="documentType")
    max_file_size: int = Field(..., alias="maxFileSize")
    allowed_mime_types: List[str] = Field(..., alias="allowedMimeTypes")
    required_file_extensions: Optional[List[str]] = Field(None, alias="requiredFileExtensions")
    max_pages: Optional[int] = Field(None, alias="maxPages")
    requires_scan: bool = Field(..., alias="requiresScan")
    requires_encryption: bool = Field(..., alias="requiresEncryption")
    retention_days: Optional[int] = Field(None, alias="retentionDays")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class FileSummarySchema(BaseModel):
    """Schema for file summary statistics."""
    
    customer_id: UUID = Field(..., alias="customerId")
    total_files: int = Field(..., alias="totalFiles")
    total_size: int = Field(..., alias="totalSize")
    by_document_type: dict = Field(..., alias="byDocumentType")
    recent_files: List[FileResponseSchema] = Field(..., alias="recentFiles")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class HealthResponseSchema(BaseModel):
    """Schema for health check response."""
    
    status: str
    timestamp: datetime
    version: str


class ErrorResponseSchema(BaseModel):
    """Schema for error responses."""
    
    success: bool = False
    error: dict
    timestamp: datetime