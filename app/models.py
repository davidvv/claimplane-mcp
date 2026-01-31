"""SQLAlchemy models for the flight claim system."""
import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey, DateTime, func, Boolean, Integer, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
import cryptography.fernet

from app.database import Base
from app.config import config
from app.utils.phone_validator import validate_phone_number


class AESEncryptedString(TypeDecorator):
    """
    Custom TypeDecorator for AES encryption using Fernet.
    Async-safe and robust replacement for sqlalchemy-utils EncryptedType.
    """
    impl = Text
    cache_ok = True

    def __init__(self, key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fernet = cryptography.fernet.Fernet(key)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        return self.fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return self.fernet.decrypt(value.encode()).decode()
        except Exception:
            # Fallback for data that might not be encrypted during transition
            return value


class Customer(Base):
    """Customer model representing a user who can submit claims."""

    __tablename__ = "customers"

    # User roles
    ROLE_CUSTOMER = "customer"
    ROLE_ADMIN = "admin"
    ROLE_SUPERADMIN = "superadmin"

    ROLES = [ROLE_CUSTOMER, ROLE_ADMIN, ROLE_SUPERADMIN]

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Encrypted PII
    email = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=False)
    email_idx = Column(String(255), unique=True, nullable=False, index=True)
    
    password_hash = Column(String(255), nullable=True)  # Nullable for migration compatibility
    
    first_name = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=False)
    last_name = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=False)
    phone = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=True)
    street = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=True)
    city = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=True)
    postal_code = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=True)
    country = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=True)

    # Authentication fields (Phase 3)
    role = Column(String(20), nullable=False, default=ROLE_CUSTOMER, server_default=ROLE_CUSTOMER)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    is_email_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Account lockout fields (Security)
    failed_login_attempts = Column(Integer, nullable=False, default=0, server_default="0")
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Account deletion fields (Phase 4)
    deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    is_blacklisted = Column(Boolean, nullable=False, default=False, server_default="false")
    blacklisted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    claims = relationship("Claim", back_populates="customer", foreign_keys="Claim.customer_id", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    magic_link_tokens = relationship("MagicLinkToken", back_populates="user", cascade="all, delete-orphan")
    
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

    @validates('role')
    def validate_role(self, key, role):
        """Validate user role."""
        if role not in self.ROLES:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(self.ROLES)}")
        return role

    @validates('phone')
    def validate_phone(self, key, phone):
        """Validate and normalize phone number."""
        if phone:
            # Validate and normalize (removes spaces, validates format)
            return validate_phone_number(phone)
        return None

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
    STATUS_ABANDONED = "abandoned"
    
    STATUS_TYPES = [
        STATUS_DRAFT,
        STATUS_SUBMITTED,
        STATUS_UNDER_REVIEW,
        STATUS_APPROVED,
        STATUS_REJECTED,
        STATUS_PAID,
        STATUS_CLOSED,
        STATUS_ABANDONED
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

    # Booking identifiers (passenger-specific)
    booking_reference = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=True)
    booking_reference_idx = Column(String(255), nullable=True, index=True)
    ticket_number = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=True)
    ticket_number_idx = Column(String(255), nullable=True, index=True)

    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Terms acceptance tracking (legal compliance)
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    terms_acceptance_ip = Column(String(45), nullable=True)  # IPv6 compatible

    # Draft workflow fields (Phase 7 - Workflow v2)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    reminder_count = Column(Integer, default=0, server_default="0")  # Number of abandonment reminders sent
    current_step = Column(Integer, default=2, nullable=True)  # Which wizard step user is on (2-4)

    # Admin workflow fields (Phase 1)
    assigned_to = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    calculated_compensation = Column(Numeric(10, 2), nullable=True)
    flight_distance_km = Column(Numeric(10, 2), nullable=True)
    delay_hours = Column(Numeric(5, 2), nullable=True)
    extraordinary_circumstances = Column(String(255), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="claims", foreign_keys=[customer_id])
    assignee = relationship("Customer", foreign_keys=[assigned_to])
    reviewer = relationship("Customer", foreign_keys=[reviewed_by])
    claim_notes = relationship("ClaimNote", back_populates="claim", cascade="all, delete-orphan")
    status_history = relationship("ClaimStatusHistory", back_populates="claim", cascade="all, delete-orphan")
    passengers = relationship("Passenger", back_populates="claim", cascade="all, delete-orphan")
    segments = relationship("FlightSegment", back_populates="claim", cascade="all, delete-orphan")
    
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


class Passenger(Base):
    """Passenger model for multi-passenger claims (Phase 5)."""
    __tablename__ = "passengers"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True)
    
    first_name = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=False)
    last_name = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=False)
    ticket_number = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=True)
    ticket_number_idx = Column(String(255), nullable=True, index=True)
    email = Column(AESEncryptedString(config.DB_ENCRYPTION_KEY), nullable=True)
    email_idx = Column(String(255), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    claim = relationship("Claim", back_populates="passengers")

    def __repr__(self):
        return f"<Passenger(id={self.id}, name={self.first_name} {self.last_name})>"


class FlightSegment(Base):
    """Flight segment model for multi-leg journeys."""
    __tablename__ = "flight_segments"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True)
    flight_number = Column(String(10), nullable=False)
    airline = Column(String(100), nullable=True)
    departure_airport = Column(String(3), nullable=False)
    arrival_airport = Column(String(3), nullable=False)
    departure_date = Column(Date, nullable=False)
    segment_order = Column(Integer, default=1)
    status = Column(String(50), default="scheduled")
    
    # Relationships
    claim = relationship("Claim", back_populates="segments")

    def __repr__(self):
        return f"<FlightSegment({self.flight_number}, {self.departure_airport}->{self.arrival_airport})>"


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
    DOCUMENT_POWER_OF_ATTORNEY = "power_of_attorney"
    DOCUMENT_OTHER = "other"
    
    DOCUMENT_TYPES = [
        DOCUMENT_BOARDING_PASS,
        DOCUMENT_ID_DOCUMENT,
        DOCUMENT_RECEIPT,
        DOCUMENT_BANK_STATEMENT,
        DOCUMENT_FLIGHT_TICKET,
        DOCUMENT_DELAY_CERTIFICATE,
        DOCUMENT_CANCELLATION_NOTICE,
        DOCUMENT_POWER_OF_ATTORNEY,
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
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=True)  # Nullable for temp files from OCR
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)  # Nullable for anonymous OCR
    
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


class ClaimNote(Base):
    """Notes associated with claims for internal or customer communication."""

    __tablename__ = "claim_notes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    author_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    note_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True)  # Internal vs customer-facing
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    claim = relationship("Claim", back_populates="claim_notes")
    author = relationship("Customer")

    def __repr__(self):
        return f"<ClaimNote(id={self.id}, claim_id={self.claim_id}, internal={self.is_internal})>"


class ClaimStatusHistory(Base):
    """Audit trail for claim status changes."""

    __tablename__ = "claim_status_history"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    change_reason = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    claim = relationship("Claim", back_populates="status_history")
    changed_by_user = relationship("Customer")

    def __repr__(self):
        return f"<ClaimStatusHistory(id={self.id}, claim_id={self.claim_id}, {self.previous_status} -> {self.new_status})>"


# Add relationships to existing models (these are defined here because ClaimFile is defined after Claim)
Customer.files = relationship("ClaimFile", back_populates="customer", foreign_keys="ClaimFile.customer_id")
Claim.files = relationship("ClaimFile", back_populates="claim", cascade="all, delete-orphan")
Claim.magic_link_tokens = relationship("MagicLinkToken", back_populates="claim", cascade="all, delete-orphan")


class RefreshToken(Base):
    """Refresh token model for JWT authentication (Phase 3)."""

    __tablename__ = "refresh_tokens"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    replaced_by_token = Column(String(500), nullable=True)

    # Device/session tracking
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    device_id = Column(String(255), nullable=True)

    # Relationships
    user = relationship("Customer", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_valid(self):
        """Check if token is still valid."""
        return (
            self.revoked_at is None and
            self.expires_at > datetime.utcnow()
        )


class PasswordResetToken(Base):
    """Password reset token model (Phase 3)."""

    __tablename__ = "password_reset_tokens"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Security tracking
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relationships
    user = relationship("Customer", back_populates="password_reset_tokens")

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_valid(self):
        """Check if token is still valid."""
        from datetime import timezone
        return (
            self.used_at is None and
            self.expires_at > datetime.now(timezone.utc)
        )


class MagicLinkToken(Base):
    """Magic link token model for passwordless authentication."""

    __tablename__ = "magic_link_tokens"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=True, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Security tracking
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relationships
    user = relationship("Customer", back_populates="magic_link_tokens")
    claim = relationship("Claim", back_populates="magic_link_tokens")

    def __repr__(self):
        return f"<MagicLinkToken(id={self.id}, user_id={self.user_id}, claim_id={self.claim_id}, expires_at={self.expires_at})>"

    @property
    def is_valid(self):
        """
        Check if token is still valid.

        Tokens are valid if:
        - Not expired (within 48 hours of creation)
        - Either never used OR used within last 24 hours (grace period for multiple uses)
        """
        from datetime import timezone, timedelta
        now = datetime.now(timezone.utc)

        # Check expiration
        if self.expires_at <= now:
            return False

        # If never used, it's valid
        if self.used_at is None:
            return True

        # Allow reuse within 24 hour grace period
        # This lets users click the link multiple times within a day
        grace_period = timedelta(hours=24)
        return (now - self.used_at.replace(tzinfo=timezone.utc)) < grace_period


class AccountDeletionRequest(Base):
    """Account deletion request model for GDPR compliance (Phase 4)."""

    __tablename__ = "account_deletion_requests"

    # Request status types
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_COMPLETED = "completed"

    STATUS_TYPES = [
        STATUS_PENDING,
        STATUS_APPROVED,
        STATUS_REJECTED,
        STATUS_COMPLETED
    ]

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), nullable=False, default=STATUS_PENDING, server_default=STATUS_PENDING)

    # Admin review tracking
    reviewed_by = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # Snapshot of user data at deletion time
    open_claims_count = Column(Integer, default=0)
    total_claims_count = Column(Integer, default=0)

    # Relationships
    customer = relationship("Customer", foreign_keys=[customer_id])
    reviewer = relationship("Customer", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<AccountDeletionRequest(id={self.id}, customer_id={self.customer_id}, status={self.status})>"

    @validates('status')
    def validate_status(self, key, status):
        """Validate deletion request status."""
        if status not in self.STATUS_TYPES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.STATUS_TYPES)}")
        return status


# ============================================================================
# PHASE 6: AeroDataBox Flight Data Models
# ============================================================================


class FlightData(Base):
    """Flight data snapshot from AeroDataBox API for audit trail and verification."""

    __tablename__ = "flight_data"

    # Flight status types
    STATUS_SCHEDULED = "scheduled"
    STATUS_DELAYED = "delayed"
    STATUS_CANCELLED = "cancelled"
    STATUS_DIVERTED = "diverted"
    STATUS_LANDED = "landed"

    STATUS_TYPES = [
        STATUS_SCHEDULED,
        STATUS_DELAYED,
        STATUS_CANCELLED,
        STATUS_DIVERTED,
        STATUS_LANDED,
        "arrived" # Added for API compatibility
    ]

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True)

    # Flight identification
    flight_number = Column(String(10), nullable=False, index=True)
    flight_date = Column(Date, nullable=False, index=True)
    airline_iata = Column(String(3), nullable=True)
    airline_name = Column(String(255), nullable=True)

    # Airports
    departure_airport_iata = Column(String(3), nullable=False)
    departure_airport_name = Column(String(255), nullable=True)
    arrival_airport_iata = Column(String(3), nullable=False)
    arrival_airport_name = Column(String(255), nullable=True)
    distance_km = Column(Numeric(10, 2), nullable=True)

    # Scheduled times
    scheduled_departure = Column(DateTime(timezone=True), nullable=True)
    scheduled_arrival = Column(DateTime(timezone=True), nullable=True)

    # Actual times
    actual_departure = Column(DateTime(timezone=True), nullable=True)
    actual_arrival = Column(DateTime(timezone=True), nullable=True)

    # Status
    flight_status = Column(String(50), nullable=True, default=STATUS_SCHEDULED)
    delay_minutes = Column(Integer, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # API metadata
    api_source = Column(String(50), default="aerodatabox", nullable=False)
    api_retrieved_at = Column(DateTime(timezone=True), server_default=func.now())
    api_response_raw = Column(JSON, nullable=True)  # Full API response for audit

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    claim = relationship("Claim", back_populates="flight_data")

    def __repr__(self):
        return f"<FlightData(id={self.id}, flight={self.flight_number}, date={self.flight_date}, status={self.flight_status})>"

    @validates('flight_status')
    def validate_status(self, key, status):
        """Validate flight status."""
        if status and status not in self.STATUS_TYPES:
            raise ValueError(f"Invalid flight status. Must be one of: {', '.join(self.STATUS_TYPES)}")
        return status

    @property
    def delay_hours(self):
        """Calculate delay in hours from delay_minutes."""
        if self.delay_minutes is not None:
            return round(self.delay_minutes / 60.0, 2)
        return None


class APIUsageTracking(Base):
    """Track every API call for quota monitoring and cost analysis."""

    __tablename__ = "api_usage_tracking"

    # API tier levels
    TIER_FREE = "TIER_FREE"
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"
    TIER_4 = "TIER_4"

    TIER_LEVELS = [TIER_FREE, TIER_1, TIER_2, TIER_3, TIER_4]

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # API details
    api_provider = Column(String(50), nullable=False, default="aerodatabox", index=True)
    endpoint = Column(String(255), nullable=False)  # e.g., "/flights/number/BA123/2024-01-15"
    tier_level = Column(String(10), nullable=False, default=TIER_2)
    credits_used = Column(Integer, nullable=False, default=2)  # 2 credits for TIER_2

    # Response details
    http_status = Column(Integer, nullable=True)  # 200, 404, 503, etc.
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Context tracking
    triggered_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True, index=True)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    triggered_by_user = relationship("Customer", foreign_keys=[triggered_by_user_id])
    claim = relationship("Claim", foreign_keys=[claim_id])

    def __repr__(self):
        return f"<APIUsageTracking(id={self.id}, provider={self.api_provider}, endpoint={self.endpoint}, credits={self.credits_used})>"

    @validates('tier_level')
    def validate_tier_level(self, key, tier_level):
        """Validate API tier level."""
        if tier_level not in self.TIER_LEVELS:
            raise ValueError(f"Invalid tier level. Must be one of: {', '.join(self.TIER_LEVELS)}")
        return tier_level


class APIQuotaStatus(Base):
    """Track current quota status for API providers with alert management."""

    __tablename__ = "api_quota_status"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_provider = Column(String(50), nullable=False, unique=True, index=True)

    # Billing period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Quota tracking
    total_credits_allowed = Column(Integer, nullable=False, default=600)  # Free tier: 600 credits/month
    credits_used = Column(Integer, nullable=False, default=0)

    # Alert tracking (multi-tier alerts at 80%, 90%, 95%)
    alert_80_sent = Column(Boolean, nullable=False, default=False)
    alert_80_sent_at = Column(DateTime(timezone=True), nullable=True)
    alert_90_sent = Column(Boolean, nullable=False, default=False)
    alert_90_sent_at = Column(DateTime(timezone=True), nullable=True)
    alert_95_sent = Column(Boolean, nullable=False, default=False)
    alert_95_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Emergency brake (block API calls when quota > 95%)
    is_quota_exceeded = Column(Boolean, nullable=False, default=False)

    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<APIQuotaStatus(id={self.id}, provider={self.api_provider}, used={self.credits_used}/{self.total_credits_allowed})>"

    @property
    def credits_remaining(self):
        """Calculate remaining credits."""
        return max(0, self.total_credits_allowed - self.credits_used)

    @property
    def usage_percentage(self):
        """Calculate usage percentage."""
        if self.total_credits_allowed == 0:
            return 100.0
        return round((self.credits_used / self.total_credits_allowed) * 100, 2)

    @property
    def should_send_alert_80(self):
        """Check if 80% alert should be sent."""
        return self.usage_percentage >= 80 and not self.alert_80_sent

    @property
    def should_send_alert_90(self):
        """Check if 90% alert should be sent."""
        return self.usage_percentage >= 90 and not self.alert_90_sent

    @property
    def should_send_alert_95(self):
        """Check if 95% alert should be sent."""
        return self.usage_percentage >= 95 and not self.alert_95_sent


# Add flight_data relationship to Claim model
Claim.flight_data = relationship("FlightData", back_populates="claim", uselist=False, cascade="all, delete-orphan")


# ============================================================================
# PHASE 6.5: Flight Search Analytics Models
# ============================================================================


class FlightSearchLog(Base):
    """Track route searches for business intelligence and analytics.

    Purpose:
    - Identify popular routes for targeted marketing campaigns
    - Understand user search patterns and behavior
    - A/B testing for search UX improvements
    - Monitor route search adoption rate
    """

    __tablename__ = "flight_search_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Search parameters
    departure_airport = Column(String(3), nullable=False, index=True)  # IATA code
    arrival_airport = Column(String(3), nullable=False, index=True)  # IATA code
    search_date = Column(Date, nullable=False)
    search_time = Column(String(10), nullable=True)  # "morning", "afternoon", "evening", or "HH:MM"

    # Results
    results_count = Column(Integer, nullable=False, default=0)
    selected_flight_number = Column(String(10), nullable=True)  # Which flight user selected (if any)

    # Metadata
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True)  # Anonymous session tracking
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible (optional, for fraud detection)
    user_agent = Column(Text, nullable=True)  # Browser/device info (optional)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("Customer", foreign_keys=[user_id])

    def __repr__(self):
        return f"<FlightSearchLog(id={self.id}, route={self.departure_airport}->{self.arrival_airport}, results={self.results_count})>"

    @validates('departure_airport', 'arrival_airport')
    def validate_airport_code(self, key, code):
        """Validate IATA airport codes (must be 3 characters)."""
        if code and len(code) != 3:
            raise ValueError("Airport code must be 3 characters")
        return code.upper()

    @validates('search_time')
    def validate_search_time(self, key, search_time):
        """Validate search time format."""
        if search_time:
            valid_options = ['morning', 'afternoon', 'evening']
            # Check if it's one of the predefined options or HH:MM format
            if search_time not in valid_options:
                # Validate HH:MM format
                if ':' not in search_time or len(search_time.split(':')) != 2:
                    raise ValueError("Search time must be 'morning', 'afternoon', 'evening', or 'HH:MM' format")
                try:
                    hours, minutes = search_time.split(':')
                    if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                        raise ValueError("Invalid time range")
                except ValueError:
                    raise ValueError("Search time must be valid HH:MM format")
        return search_time


# ============================================================================
# PHASE 7: Workflow v2 - Analytics & Draft Tracking
# ============================================================================


class ClaimEvent(Base):
    """Analytics event model for tracking claim workflow progress.

    Purpose:
    - Track where users drop off in the claim process
    - Enable abandoned cart recovery emails
    - Business intelligence on conversion funnel
    - Audit trail for customer journey
    """

    __tablename__ = "claim_events"

    # Event types
    EVENT_DRAFT_CREATED = "draft_created"
    EVENT_STEP_COMPLETED = "step_completed"
    EVENT_FILE_UPLOADED = "file_uploaded"
    EVENT_FILE_REMOVED = "file_removed"
    EVENT_CLAIM_SUBMITTED = "claim_submitted"
    EVENT_CLAIM_ABANDONED = "claim_abandoned"
    EVENT_REMINDER_SENT = "reminder_sent"
    EVENT_REMINDER_CLICKED = "reminder_clicked"
    EVENT_CLAIM_RESUMED = "claim_resumed"
    EVENT_CLAIM_DELETED = "claim_deleted"
    EVENT_SESSION_STARTED = "session_started"
    EVENT_SESSION_ENDED = "session_ended"

    EVENT_TYPES = [
        EVENT_DRAFT_CREATED,
        EVENT_STEP_COMPLETED,
        EVENT_FILE_UPLOADED,
        EVENT_FILE_REMOVED,
        EVENT_CLAIM_SUBMITTED,
        EVENT_CLAIM_ABANDONED,
        EVENT_REMINDER_SENT,
        EVENT_REMINDER_CLICKED,
        EVENT_CLAIM_RESUMED,
        EVENT_CLAIM_DELETED,
        EVENT_SESSION_STARTED,
        EVENT_SESSION_ENDED,
    ]

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=True, index=True)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True, index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSON, nullable=True)  # Flexible data for event-specific info

    # Context
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)  # Browser session ID

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    claim = relationship("Claim", back_populates="events", foreign_keys=[claim_id])
    customer = relationship("Customer", foreign_keys=[customer_id])

    def __repr__(self):
        return f"<ClaimEvent(id={self.id}, type={self.event_type}, claim_id={self.claim_id})>"

    @validates('event_type')
    def validate_event_type(self, key, event_type):
        """Validate event type."""
        if event_type not in self.EVENT_TYPES:
            raise ValueError(f"Invalid event type. Must be one of: {', '.join(self.EVENT_TYPES)}")
        return event_type


# Add events relationship to Claim model
Claim.events = relationship("ClaimEvent", back_populates="claim", cascade="all, delete-orphan")