"""SQLAlchemy models for the flight claim system."""
import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.database import Base


class Customer(Base):
    """Customer model representing a user who can submit claims."""
    
    __tablename__ = "customers"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    street = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    claims = relationship("Claim", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, email={self.email}, name={self.first_name} {self.last_name})>"
    
    @validates('email')
    def validate_email(self, key, address):
        """Validate email format."""
        if address:
            # Basic email validation - in a real app, use email-validator library
            if '@' not in address or '.' not in address.split('@')[-1]:
                raise ValueError("Invalid email format")
        return address
    
    @hybrid_property
    def full_name(self):
        """Return full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def address(self):
        """Return address as a nested object."""
        # Check if any address field has a non-None value
        if (self.street is not None or
            self.city is not None or
            self.postal_code is not None or
            self.country is not None):

            return {
                "street": self.street or None,
                "city": self.city or None,
                "postalCode": self.postal_code or None,
                "country": self.country or None
            }
        return None


class Claim(Base):
    """Claim model representing a flight compensation claim."""
    
    __tablename__ = "claims"
    
    # Incident types
    INCIDENT_DELAY = "delay"
    INCIDENT_CANCELLATION = "cancellation"
    INCIDENT_DENIED_BOARDING = "denied_boarding"
    INCIDENT_BAGGAGE_DELAY = "baggage_delay"
    
    INCIDENT_TYPES = [
        INCIDENT_DELAY,
        INCIDENT_CANCELLATION,
        INCIDENT_DENIED_BOARDING,
        INCIDENT_BAGGAGE_DELAY
    ]
    
    # Status types
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_PAID = "paid"
    STATUS_CLOSED = "closed"
    
    STATUS_TYPES = [
        STATUS_DRAFT,
        STATUS_SUBMITTED,
        STATUS_UNDER_REVIEW,
        STATUS_APPROVED,
        STATUS_REJECTED,
        STATUS_PAID,
        STATUS_CLOSED
    ]
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    flight_number = Column(String(10), nullable=False)
    airline = Column(String(100), nullable=False)
    departure_date = Column(Date, nullable=False)
    departure_airport = Column(String(3), nullable=False)  # IATA code
    arrival_airport = Column(String(3), nullable=False)  # IATA code
    incident_type = Column(String(50), nullable=False)
    status = Column(String(50), default=STATUS_SUBMITTED)
    compensation_amount = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="EUR")
    notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="claims")
    
    def __repr__(self):
        return f"<Claim(id={self.id}, flight={self.flight_number}, incident={self.incident_type}, status={self.status})>"
    
    @validates('incident_type')
    def validate_incident_type(self, key, incident_type):
        """Validate incident type."""
        if incident_type not in self.INCIDENT_TYPES:
            raise ValueError(f"Invalid incident type. Must be one of: {', '.join(self.INCIDENT_TYPES)}")
        return incident_type
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status."""
        if status not in self.STATUS_TYPES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.STATUS_TYPES)}")
        return status
    
    @validates('departure_airport', 'arrival_airport')
    def validate_airport_code(self, key, code):
        """Validate IATA airport codes (should be 3 characters)."""
        if code and len(code) != 3:
            raise ValueError("Airport code must be 3 characters")
        return code.upper()
    
    @validates('flight_number')
    def validate_flight_number(self, key, flight_number):
        """Validate flight number format."""
        if flight_number:
            # Basic validation - should contain airline code and number
            if not any(char.isdigit() for char in flight_number):
                raise ValueError("Flight number must contain digits")
            if len(flight_number) < 3:
                raise ValueError("Flight number too short")
        return flight_number.upper()


class ClaimFile(Base):
    """File model for claim-related documents."""
    
    __tablename__ = "claim_files"
    
    # Document types
    DOCUMENT_BOARDING_PASS = "boarding_pass"
    DOCUMENT_ID_DOCUMENT = "id_document"
    DOCUMENT_RECEIPT = "receipt"
    DOCUMENT_BANK_STATEMENT = "bank_statement"
    DOCUMENT_FLIGHT_TICKET = "flight_ticket"
    DOCUMENT_DELAY_CERTIFICATE = "delay_certificate"
    DOCUMENT_CANCELLATION_NOTICE = "cancellation_notice"
    DOCUMENT_OTHER = "other"
    
    DOCUMENT_TYPES = [
        DOCUMENT_BOARDING_PASS,
        DOCUMENT_ID_DOCUMENT,
        DOCUMENT_RECEIPT,
        DOCUMENT_BANK_STATEMENT,
        DOCUMENT_FLIGHT_TICKET,
        DOCUMENT_DELAY_CERTIFICATE,
        DOCUMENT_CANCELLATION_NOTICE,
        DOCUMENT_OTHER
    ]
    
    # File status
    STATUS_UPLOADED = "uploaded"
    STATUS_SCANNING = "scanning"
    STATUS_VALIDATED = "validated"
    STATUS_REJECTED = "rejected"
    STATUS_APPROVED = "approved"
    STATUS_ARCHIVED = "archived"
    
    STATUS_TYPES = [
        STATUS_UPLOADED,
        STATUS_SCANNING,
        STATUS_VALIDATED,
        STATUS_REJECTED,
        STATUS_APPROVED,
        STATUS_ARCHIVED
    ]
    
    # Encryption status
    ENCRYPTION_ENCRYPTED = "encrypted"
    ENCRYPTION_DECRYPTED = "decrypted"
    ENCRYPTION_PENDING = "pending"
    
    ENCRYPTION_STATUS_TYPES = [
        ENCRYPTION_ENCRYPTED,
        ENCRYPTION_DECRYPTED,
        ENCRYPTION_PENDING
    ]
    
    # Access level
    ACCESS_PUBLIC = "public"
    ACCESS_PRIVATE = "private"
    ACCESS_RESTRICTED = "restricted"
    
    ACCESS_LEVEL_TYPES = [
        ACCESS_PUBLIC,
        ACCESS_PRIVATE,
        ACCESS_RESTRICTED
    ]
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    # File metadata
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Numeric(20, 0), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    
    # Document classification
    document_type = Column(String(50), nullable=False)
    
    # Storage information
    storage_provider = Column(String(50), default="nextcloud")
    storage_path = Column(Text, nullable=False)
    nextcloud_file_id = Column(String(255))
    nextcloud_share_token = Column(String(255))
    description = Column(Text)
    
    # Security and access
    encryption_status = Column(String(20), default=ENCRYPTION_ENCRYPTED)
    access_level = Column(String(20), default=ACCESS_PRIVATE)
    download_count = Column(Numeric(10, 0), default=0)
    
    # Status and workflow
    status = Column(String(50), default=STATUS_UPLOADED)
    validation_status = Column(String(50), default="pending")
    rejection_reason = Column(Text)
    
    # Audit trail
    uploaded_by = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"))
    reviewed_by = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Soft delete and versioning
    is_deleted = Column(Numeric(1, 0), default=0)
    deleted_at = Column(DateTime(timezone=True))
    version = Column(Numeric(5, 0), default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    claim = relationship("Claim", back_populates="files", foreign_keys=[claim_id])
    customer = relationship("Customer", back_populates="files", foreign_keys=[customer_id])
    uploader = relationship("Customer", foreign_keys=[uploaded_by])
    reviewer = relationship("Customer", foreign_keys=[reviewed_by])
    access_logs = relationship("FileAccessLog", back_populates="file", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ClaimFile(id={self.id}, filename={self.filename}, claim_id={self.claim_id}, status={self.status})>"
    
    @validates('document_type')
    def validate_document_type(self, key, document_type):
        """Validate document type."""
        if document_type not in self.DOCUMENT_TYPES:
            raise ValueError(f"Invalid document type. Must be one of: {', '.join(self.DOCUMENT_TYPES)}")
        return document_type
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate file status."""
        if status not in self.STATUS_TYPES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.STATUS_TYPES)}")
        return status
    
    @validates('encryption_status')
    def validate_encryption_status(self, key, encryption_status):
        """Validate encryption status."""
        if encryption_status not in self.ENCRYPTION_STATUS_TYPES:
            raise ValueError(f"Invalid encryption status. Must be one of: {', '.join(self.ENCRYPTION_STATUS_TYPES)}")
        return encryption_status
    
    @validates('access_level')
    def validate_access_level(self, key, access_level):
        """Validate access level."""
        if access_level not in self.ACCESS_LEVEL_TYPES:
            raise ValueError(f"Invalid access level. Must be one of: {', '.join(self.ACCESS_LEVEL_TYPES)}")
        return access_level


class FileAccessLog(Base):
    """Log model for file access events."""
    
    __tablename__ = "file_access_logs"
    
    # Access types
    ACCESS_UPLOAD = "upload"
    ACCESS_DOWNLOAD = "download"
    ACCESS_VIEW = "view"
    ACCESS_SHARE = "share"
    ACCESS_DELETE = "delete"
    ACCESS_RESTORE = "restore"
    ACCESS_UPDATE = "update"
    
    ACCESS_TYPES = [
        ACCESS_UPLOAD,
        ACCESS_DOWNLOAD,
        ACCESS_VIEW,
        ACCESS_SHARE,
        ACCESS_DELETE,
        ACCESS_RESTORE,
        ACCESS_UPDATE
    ]
    
    # Access status
    ACCESS_SUCCESS = "success"
    ACCESS_DENIED = "denied"
    ACCESS_ERROR = "error"
    
    ACCESS_STATUS_TYPES = [
        ACCESS_SUCCESS,
        ACCESS_DENIED,
        ACCESS_ERROR
    ]
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(PGUUID(as_uuid=True), ForeignKey("claim_files.id"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"))
    
    access_type = Column(String(50), nullable=False)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    referrer = Column(Text)
    access_status = Column(String(20), nullable=False)
    failure_reason = Column(Text)
    session_id = Column(String(255))
    
    access_time = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # Geographic information for security monitoring
    country_code = Column(String(2))
    city = Column(String(100))
    coordinates = Column(String(100))  # POINT type simplified as string
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    file = relationship("ClaimFile", back_populates="access_logs")
    user = relationship("Customer")
    
    def __repr__(self):
        return f"<FileAccessLog(id={self.id}, file_id={self.file_id}, access_type={self.access_type}, status={self.access_status})>"
    
    @validates('access_type')
    def validate_access_type(self, key, access_type):
        """Validate access type."""
        if access_type not in self.ACCESS_TYPES:
            raise ValueError(f"Invalid access type. Must be one of: {', '.join(self.ACCESS_TYPES)}")
        return access_type
    
    @validates('access_status')
    def validate_access_status(self, key, access_status):
        """Validate access status."""
        if access_status not in self.ACCESS_STATUS_TYPES:
            raise ValueError(f"Invalid access status. Must be one of: {', '.join(self.ACCESS_STATUS_TYPES)}")
        return access_status


class FileValidationRule(Base):
    """Validation rules for different document types."""
    
    __tablename__ = "file_validation_rules"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_type = Column(String(50), nullable=False, unique=True)
    max_file_size = Column(Numeric(20, 0), nullable=False)
    allowed_mime_types = Column(Text, nullable=False)  # JSON array stored as text
    required_file_extensions = Column(Text)  # JSON array stored as text
    
    # Content validation rules
    min_dimensions = Column(String(20))
    max_dimensions = Column(String(20))
    max_pages = Column(Numeric(5, 0))
    requires_ocr = Column(Numeric(1, 0), default=0)
    allowed_content_patterns = Column(Text)  # JSON array stored as text
    
    # Security requirements
    requires_scan = Column(Numeric(1, 0), default=1)
    requires_encryption = Column(Numeric(1, 0), default=1)
    retention_days = Column(Numeric(5, 0))
    
    # Status and priority
    is_active = Column(Numeric(1, 0), default=1)
    priority = Column(Numeric(5, 0), default=100)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<FileValidationRule(id={self.id}, document_type={self.document_type}, max_size={self.max_file_size})>"


# Add relationships to existing models
Customer.files = relationship("ClaimFile", back_populates="customer", foreign_keys="ClaimFile.customer_id")
Claim.files = relationship("ClaimFile", back_populates="claim", cascade="all, delete-orphan")