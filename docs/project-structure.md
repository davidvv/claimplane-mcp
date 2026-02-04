# Project Structure Guide

## Flight Claim System - Complete Project Organization

This document provides a comprehensive overview of the Flight Claim System's project structure, explaining the purpose and responsibility of each module, directory, and file within the codebase.

## Project Root Structure

```
flight_claim/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization with version
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration and environment variables
│   ├── database.py              # Database configuration and session management
│   ├── models.py                # SQLAlchemy ORM models (7 tables)
│   ├── schemas.py               # Pydantic validation schemas (customer/claim)
│   ├── exceptions.py            # Custom exception definitions
│   ├── middleware.py            # Error handling middleware
│   ├── celery_app.py            # Celery configuration (Phase 2)
│   ├── repositories/            # Data access layer
│   │   ├── __init__.py         # Repository exports
│   │   ├── base.py             # Generic base repository
│   │   ├── customer_repository.py    # Customer data operations
│   │   ├── claim_repository.py       # Claim data operations
│   │   ├── admin_claim_repository.py # Admin claim operations (Phase 1)
│   │   └── file_repository.py        # File management operations (Phase 1)
│   ├── routers/                 # API route handlers
│   │   ├── __init__.py         # Router exports
│   │   ├── customers.py        # Customer API endpoints
│   │   ├── claims.py           # Claim API endpoints (with notifications)
│   │   ├── files.py            # File upload/download endpoints
│   │   ├── admin_claims.py     # Admin claim management (Phase 1)
│   │   ├── admin_files.py      # Admin file review (Phase 1)
│   │   └── health.py           # System health endpoints
│   ├── services/                # Business logic and external integrations
│   │   ├── compensation_service.py      # EU261/2004 calculations (Phase 1)
│   │   ├── claim_workflow_service.py    # Status workflow management (Phase 1)
│   │   ├── email_service.py             # Email sending service (Phase 2)
│   │   ├── encryption_service.py        # File encryption
│   │   ├── file_validation_service.py   # Document validation
│   │   └── nextcloud_service.py         # Nextcloud WebDAV integration
│   ├── schemas/                 # Pydantic schemas (organized by domain)
│   │   └── admin_schemas.py     # Admin-specific schemas (Phase 1)
│   ├── tasks/                   # Celery async tasks (Phase 2)
│   │   ├── __init__.py         # Task package initialization
│   │   └── claim_tasks.py      # Email notification tasks
│   └── templates/               # Email templates (Phase 2)
│       └── emails/              # HTML email templates
│           ├── claim_submitted.html      # Claim confirmation email
│           ├── status_updated.html       # Status change notification
│           └── document_rejected.html    # Document rejection notice
├── docs/                        # Project documentation
│   ├── system-architecture-overview.md  # Architecture documentation
│   ├── database-schema.md              # Database design (updated Phase 1)
│   ├── api-reference.md                # Complete API reference (updated Phase 1)
│   ├── api-flow-diagrams.md            # API flow documentation
│   ├── project-structure.md            # This file
│   ├── setup-deployment-guide.md       # Setup and deployment instructions
│   ├── troubleshooting-guide.md        # Common issues and solutions
│   ├── security-best-practices.md      # Security guidelines
│   ├── file-management-system-design.md        # File system design
│   ├── file-management-implementation-guide.md # File system implementation
│   ├── implementation-deep-dive.md     # Detailed implementation notes
│   ├── interactive-examples.md         # Code examples
│   └── data-flow-visualization.md      # Data flow diagrams
├── API/                         # API specification files
│   └── openapi.yaml            # Complete OpenAPI specification
├── requirements.txt             # Python dependencies (FastAPI, SQLAlchemy, Celery, etc.)
├── Dockerfile                   # Container build configuration
├── docker-compose.yml          # Multi-container setup (API, DB, Redis, Celery)
├── nginx.conf                  # Nginx reverse proxy configuration
├── .env                        # Environment variables (not committed)
├── .gitignore                  # Git ignore patterns
├── README.md                   # Project overview (updated Phase 2)
├── ROADMAP.md                  # Development roadmap (Phase 2 complete)
├── VERSIONING.md               # Version strategy and release process
├── CLAUDE.md                   # Instructions for AI-assisted development
├── DEVELOPMENT_WORKFLOW.md     # Environment setup and workflow
├── PHASE1_SUMMARY.md           # Phase 1 implementation details
├── PHASE2_SUMMARY.md           # Phase 2 implementation details
├── PHASE2_TESTING_GUIDE.md     # Phase 2 testing procedures
├── DOCS_CLEANUP_ANALYSIS.md    # Documentation cleanup analysis
├── init_db.py                  # Database initialization script
└── scripts/                    # Utility and test scripts
    ├── test_nextcloud_integration.py
    └── generate_secrets.py
```

## Application Package (`app/`)

### Core Application Files

#### `__init__.py`
```python
"""Flight Claim System API"""
__version__ = "0.2.0"
```

**Purpose**: Package initialization and version management
- Defines the application version used throughout the system
- Enables import of the app package
- Centralizes version information for consistency
- **Current Version**: v0.2.0 (Phase 2 Complete - Notifications & Async Processing)

#### `main.py` - Application Entry Point
**Responsibilities**:
- FastAPI application creation and configuration
- Middleware setup (CORS, error handling)
- Router registration and URL mapping  
- Application lifespan management (startup/shutdown)
- Database initialization on startup
- Auto-documentation configuration (Swagger UI, ReDoc)

**Key Components**:
```python
# Async lifespan manager for startup/shutdown tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Database initialization
    await init_db()
    yield
    # Cleanup tasks

# FastAPI application with comprehensive configuration
app = FastAPI(
    title="Flight Claim System API",
    description="API for managing flight compensation claims",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)
```

#### `database.py` - Database Configuration
**Responsibilities**:
- Async SQLAlchemy engine configuration
- Database session factory setup
- Connection pool management
- Database initialization utilities
- Dependency injection for database sessions

**Key Components**:
```python
# Async database engine
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Session factory for dependency injection
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Database session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

### Data Layer

#### `models.py` - SQLAlchemy ORM Models
**Responsibilities**:
- Database table definitions using SQLAlchemy ORM
- Model relationships and foreign key constraints
- Data validation at the model level
- Business logic methods and properties
- Enum definitions for status fields

**Key Models**:

##### Customer Model
```python
class Customer(Base):
    __tablename__ = "customers"
    
    # Primary fields
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    
    # Optional contact information
    phone = Column(String(20), nullable=True)
    
    # Address information (embedded)
    street = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    claims = relationship("Claim", back_populates="customer", cascade="all, delete-orphan")
    
    # Validation methods
    @validates('email')
    def validate_email(self, key, address):
        # Email format validation
        
    # Business logic properties
    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
```

##### Claim Model (Updated Phase 1)
```python
class Claim(Base):
    __tablename__ = "claims"

    # Status and incident type enums
    INCIDENT_TYPES = ["delay", "cancellation", "denied_boarding", "baggage_delay"]
    STATUS_TYPES = ["draft", "submitted", "under_review", "documents_requested",
                   "approved", "rejected", "paid", "closed"]

    # Primary fields
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Flight information
    flight_number = Column(String(10), nullable=False)
    airline = Column(String(100), nullable=False)
    departure_date = Column(Date, nullable=False)
    departure_airport = Column(String(3), nullable=False)  # IATA code
    arrival_airport = Column(String(3), nullable=False)    # IATA code

    # Claim details
    incident_type = Column(String(50), nullable=False)
    status = Column(String(50), default=STATUS_SUBMITTED)
    compensation_amount = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="EUR")
    notes = Column(Text, nullable=True)

    # Phase 1 Admin workflow fields
    assigned_to = Column(PGUUID(as_uuid=True), nullable=True)  # Admin reviewer
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    calculated_compensation = Column(Numeric(10, 2), nullable=True)  # EU261 calculation

    # Audit timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="claims")
    files = relationship("ClaimFile", back_populates="claim", cascade="all, delete-orphan")
    notes = relationship("ClaimNote", back_populates="claim", cascade="all, delete-orphan")
    status_history = relationship("ClaimStatusHistory", back_populates="claim", cascade="all, delete-orphan")

    # Validation methods for business rules
    @validates('incident_type', 'status', 'departure_airport', 'arrival_airport', 'flight_number')
    def validate_fields(self, key, value):
        # Field-specific validation logic
```

##### ClaimNote Model (Phase 1)
```python
class ClaimNote(Base):
    __tablename__ = "claim_notes"

    # Primary fields
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    author_id = Column(PGUUID(as_uuid=True), nullable=False)  # Admin user ID

    # Note content
    note_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True)  # Internal vs customer-facing

    # Audit timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    claim = relationship("Claim", back_populates="notes")
```

**Purpose**: Audit trail for claim discussions and decisions
- Internal notes for admin-only communication
- Customer-facing notes for transparency
- Chronological history of all claim communication

##### ClaimStatusHistory Model (Phase 1)
```python
class ClaimStatusHistory(Base):
    __tablename__ = "claim_status_history"

    # Primary fields
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)

    # Status change details
    previous_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(PGUUID(as_uuid=True), nullable=False)  # Admin user ID
    change_reason = Column(Text, nullable=True)

    # Audit timestamp
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    claim = relationship("Claim", back_populates="status_history")
```

**Purpose**: Complete audit trail for status changes
- Track every status transition
- Record who made the change and why
- Support compliance and transparency requirements
- Enable analytics on processing times

##### ClaimFile Model
```python
class ClaimFile(Base):
    __tablename__ = "claim_files"

    # File statuses
    STATUS_UPLOADED = "uploaded"
    STATUS_VALIDATED = "validated"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    # Document types
    DOCUMENT_TYPES = ["boarding_pass", "id_document", "receipt", "bank_statement",
                     "flight_ticket", "delay_certificate", "cancellation_notice", "other"]

    # Primary fields with relationships
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # File metadata
    document_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)

    # Security and validation
    status = Column(String(50), default=STATUS_UPLOADED)
    validation_status = Column(String(50), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Admin review fields (Phase 1)
    reviewed_by = Column(PGUUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    claim = relationship("Claim", back_populates="files")
    customer = relationship("Customer")
```


#### `schemas.py` - Pydantic Validation Schemas
**Responsibilities**:
- Request/response data validation using Pydantic
- API input sanitization and type conversion
- Response serialization with field aliasing
- Different schema types for different operations (Create, Update, Patch, Response)

**Schema Categories**:

##### Request Schemas
```python
# Complete customer creation
class CustomerCreateSchema(BaseModel):
    email: EmailStr
    first_name: str = Field(..., max_length=50, alias="firstName")
    last_name: str = Field(..., max_length=50, alias="lastName")
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[AddressSchema] = None

# Complete customer update (PUT)
class CustomerUpdateSchema(BaseModel):
    # All fields required for PUT operations

# Partial customer update (PATCH)  
class CustomerPatchSchema(BaseModel):
    # All fields optional for PATCH operations
    email: Union[None, str] = None
    # Custom validation for empty string handling
```

##### Response Schemas
```python
class CustomerResponseSchema(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str = Field(..., alias="firstName")
    # ... other fields with proper aliasing
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    
    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase
        from_attributes = True   # Enable ORM model conversion
```

### Business Logic Layer

#### Repository Pattern (`repositories/`)

##### `base.py` - Generic Repository
**Responsibilities**:
- Common CRUD operations for all entities
- Generic type support using Python generics
- Standardized database interaction patterns
- Transaction management and error handling
- Pagination support

**Core Methods**:
```python
class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession)
    
    # Basic CRUD operations
    async def get_by_id(self, id: UUID) -> Optional[ModelType]
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]
    async def create(self, **kwargs) -> ModelType
    async def update(self, instance: ModelType, **kwargs) -> ModelType
    async def delete(self, instance: ModelType) -> bool
    
    # Utility methods
    async def count(self) -> int
    async def exists(self, id: UUID) -> bool
    async def get_by_field(self, field: str, value) -> Optional[ModelType]
    async def get_all_by_field(self, field: str, value, skip: int = 0, limit: int = 100) -> List[ModelType]
```

##### `customer_repository.py` - Customer Operations
**Responsibilities**:
- Customer-specific database operations
- Email uniqueness validation
- Name-based search functionality
- Address management
- PUT vs PATCH update logic

**Specialized Methods**:
```python
class CustomerRepository(BaseRepository[Customer]):
    # Customer-specific queries
    async def get_by_email(self, email: str) -> Optional[Customer]
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Customer]
    async def search_by_email(self, email: str, skip: int = 0, limit: int = 100) -> List[Customer]
    async def get_active_customers(self, skip: int = 0, limit: int = 100) -> List[Customer]
    
    # Update operations with null handling
    async def update_customer(self, customer_id: UUID, allow_null_values: bool = False, **kwargs) -> Optional[Customer]
    async def update_customer_email(self, customer_id: UUID, email: str) -> Optional[Customer]
```

##### `claim_repository.py` - Claim Operations
**Responsibilities**:
- Claim-specific database operations
- Flight information validation
- Status workflow management
- Date range queries
- Customer relationship handling

**Specialized Methods**:
```python
class ClaimRepository(BaseRepository[Claim]):
    # Claim-specific queries
    async def get_by_customer_id(self, customer_id: UUID, skip: int = 0, limit: int = 100) -> List[Claim]
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Claim]
    async def get_by_incident_type(self, incident_type: str, skip: int = 0, limit: int = 100) -> List[Claim]
    async def get_by_flight_number(self, flight_number: str, skip: int = 0, limit: int = 100) -> List[Claim]
    async def get_by_date_range(self, start_date: date, end_date: date, skip: int = 0, limit: int = 100) -> List[Claim]
    
    # Business logic operations
    async def get_pending_claims(self, skip: int = 0, limit: int = 100) -> List[Claim]
    async def get_claims_with_compensation(self, skip: int = 0, limit: int = 100) -> List[Claim]
    async def update_claim_status(self, claim_id: UUID, status: str, notes: Optional[str] = None) -> Optional[Claim]
    async def update_compensation(self, claim_id: UUID, amount: float, currency: str = "EUR") -> Optional[Claim]
    async def get_claims_summary(self) -> dict
```

### API Layer (`routers/`)

#### `customers.py` - Customer API Endpoints
**Responsibilities**:
- Customer CRUD API endpoints
- Request validation and response serialization
- Business rule enforcement (email uniqueness)
- Search functionality
- Proper HTTP status code handling

**Endpoint Categories**:

##### Basic CRUD Operations
```python
@router.post("/", response_model=CustomerResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_customer(customer_data: CustomerCreateSchema, db: AsyncSession = Depends(get_db))

@router.get("/{customer_id}", response_model=CustomerResponseSchema)
async def get_customer(customer_id: UUID, db: AsyncSession = Depends(get_db))

@router.get("/", response_model=List[CustomerResponseSchema])
async def list_customers(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db))
```

##### Update Operations (PUT vs PATCH)
```python
@router.put("/{customer_id}", response_model=CustomerResponseSchema)
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdateSchema,  # All fields required
    db: AsyncSession = Depends(get_db)
):
    # Complete replacement logic
    updated_customer = await repo.update_customer(
        customer_id=customer_id,
        allow_null_values=True,  # Allow setting fields to null
        **customer_data.dict()
    )

@router.patch("/{customer_id}", response_model=CustomerResponseSchema)
async def patch_customer(
    customer_id: UUID,
    customer_data: CustomerPatchSchema,  # Optional fields only
    db: AsyncSession = Depends(get_db)
):
    # Partial update logic - filter out None values
    update_data = {k: v for k, v in customer_data.dict().items() if v is not None}
    updated_customer = await repo.update_customer(
        customer_id=customer_id,
        allow_null_values=False,  # Preserve existing values
        **update_data
    )
```

##### Search Operations
```python
@router.get("/search/by-email/{email}", response_model=List[CustomerResponseSchema])
async def search_customers_by_email(email: str, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db))

@router.get("/search/by-name/{name}", response_model=List[CustomerResponseSchema])
async def search_customers_by_name(name: str, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db))
```

#### `claims.py` - Claim API Endpoints
**Responsibilities**:
- Claim CRUD API endpoints
- Flight information validation
- Customer relationship management
- Status workflow enforcement
- Multi-endpoint claim submission

**Key Endpoints**:

##### Claim Creation
```python
@router.post("/", response_model=ClaimResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_claim(claim_data: ClaimCreateSchema, db: AsyncSession = Depends(get_db))
# Creates claim for existing customer

@router.post("/submit", response_model=ClaimResponseSchema, status_code=status.HTTP_201_CREATED)
async def submit_claim_with_customer(claim_request: ClaimRequestSchema, db: AsyncSession = Depends(get_db))
# Creates customer if needed, then creates claim
```

##### Claim Queries
```python
@router.get("/", response_model=List[ClaimResponseSchema])
async def list_claims(
    skip: int = 0, 
    limit: int = 100,
    status: str = None,           # Optional status filter
    customer_id: UUID = None,     # Optional customer filter
    db: AsyncSession = Depends(get_db)
)

@router.get("/customer/{customer_id}", response_model=List[ClaimResponseSchema])
async def get_customer_claims(customer_id: UUID, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db))

@router.get("/status/{status}", response_model=List[ClaimResponseSchema])
async def get_claims_by_status(status: str, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db))
```

#### `health.py` - System Health Endpoints
**Responsibilities**:
- API health monitoring
- Database connectivity checks
- System information reporting
- Service dependency validation

**Health Check Levels**:
```python
@router.get("/health", response_model=HealthResponseSchema)
async def health_check(db: AsyncSession = Depends(get_db))
# Basic health check with database connectivity

@router.get("/health/db")
async def database_health(db: AsyncSession = Depends(get_db))
# Detailed database information (version, name, user)

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db))
# Comprehensive system health (Python version, platform, environment)
```

#### `admin_claims.py` - Admin Claim Management (Phase 1)
**Responsibilities**:
- Admin dashboard claim operations
- Status workflow management
- Claim assignment to reviewers
- Compensation calculations and updates
- Note management (internal and customer-facing)
- Status history tracking
- Bulk operations
- Analytics and reporting

**Authentication**: Requires `X-Admin-ID` header (Phase 3 will implement JWT)

**Key Endpoints**:
- `GET /admin/claims` - List claims with advanced filtering
- `GET /admin/claims/{claim_id}` - Get full claim details
- `PUT /admin/claims/{claim_id}/status` - Update claim status (triggers email)
- `PUT /admin/claims/{claim_id}/assign` - Assign to reviewer
- `PUT /admin/claims/{claim_id}/compensation` - Set compensation amount
- `POST /admin/claims/{claim_id}/notes` - Add note
- `GET /admin/claims/{claim_id}/history` - View status history
- `POST /admin/claims/bulk-action` - Bulk status updates/assignments
- `GET /admin/claims/analytics/summary` - Dashboard analytics
- `POST /admin/claims/calculate-compensation` - EU261/2004 calculator
- `GET /admin/claims/{claim_id}/status-transitions` - Valid next statuses

**Integration**:
- Uses `AdminClaimRepository` for complex queries
- Uses `ClaimWorkflowService` for status validation
- Uses `CompensationService` for EU261/2004 calculations
- Triggers async email notifications via Celery tasks (Phase 2)

#### `admin_files.py` - Admin File Review (Phase 1)
**Responsibilities**:
- Document review and approval
- Document rejection with reasons
- Re-upload request management
- File statistics and reporting
- Document-type based batch processing

**Authentication**: Requires `X-Admin-ID` header

**Key Endpoints**:
- `GET /admin/files/claim/{claim_id}/documents` - List all claim files
- `GET /admin/files/{file_id}/metadata` - Get detailed file info
- `PUT /admin/files/{file_id}/review` - Approve/reject document (triggers email)
- `POST /admin/files/{file_id}/request-reupload` - Request re-upload with deadline
- `GET /admin/files/pending-review` - Get files awaiting review
- `GET /admin/files/by-document-type/{type}` - Filter by document type
- `GET /admin/files/statistics` - File system statistics
- `DELETE /admin/files/{file_id}` - Soft delete file

**Integration**:
- Uses `FileRepository` for file queries
- Triggers async document rejected emails (Phase 2)
- Updates file status and validation_status
- Records reviewer ID and review timestamps

### Services Layer (`services/`)

#### `compensation_service.py` - EU261/2004 Calculations (Phase 1)
**Responsibilities**:
- Flight distance calculation using airport coordinates
- EU261/2004 compensation amount determination
- Distance category classification (short/medium/long haul)
- Extraordinary circumstances detection
- Eligibility verification

**Key Methods**:
```python
class CompensationService:
    @staticmethod
    def calculate_compensation(
        departure_airport: str,
        arrival_airport: str,
        delay_hours: float,
        incident_type: str,
        extraordinary_circumstances: bool = False
    ) -> dict
    # Returns: eligible, amount, currency, distance_km, category, reason

    @staticmethod
    def get_airport_coordinates(iata_code: str) -> tuple[float, float]
    # Airport coordinate lookup

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2) -> float
    # Haversine formula distance calculation

    @staticmethod
    def detect_extraordinary_circumstances(notes: str) -> bool
    # Keyword-based detection (weather, strike, security, etc.)
```

**Compensation Rules**:
- Short haul (< 1500 km): €250
- Medium haul (1500-3500 km): €400
- Long haul (> 3500 km): €600
- Delay threshold: 3+ hours
- No compensation if extraordinary circumstances

**Testing**: 35 comprehensive test cases covering edge cases

#### `claim_workflow_service.py` - Status Workflow Management (Phase 1)
**Responsibilities**:
- Valid status transition enforcement
- Status change audit logging
- Claim assignment management
- Compensation update tracking
- Status-based business rules

**Status Workflow**:
```
draft → submitted → under_review → documents_requested
                                 ↓
                              approved → paid → closed
                                 ↓
                              rejected → closed
```

**Key Methods**:
```python
class ClaimWorkflowService:
    @staticmethod
    async def transition_status(
        session: AsyncSession,
        claim: Claim,
        new_status: str,
        changed_by: UUID,
        change_reason: Optional[str] = None
    ) -> Claim
    # Validates transition, updates status, creates history record

    @staticmethod
    async def assign_claim(
        session: AsyncSession,
        claim: Claim,
        assigned_to: UUID,
        assigned_by: UUID
    )
    # Assigns claim to reviewer

    @staticmethod
    async def set_compensation(
        session: AsyncSession,
        claim: Claim,
        compensation_amount: float,
        set_by: UUID,
        reason: Optional[str] = None
    )
    # Sets compensation with audit trail

    @staticmethod
    def get_valid_next_statuses(current_status: str) -> List[str]
    # Returns allowed next statuses

    @staticmethod
    def get_status_display_info(status: str) -> dict
    # Returns: display_name, description, color
```

#### `email_service.py` - Email Notifications (Phase 2)
**Responsibilities**:
- Async SMTP email sending
- HTML email template rendering
- Three notification types
- Error handling and logging

**Key Methods**:
```python
class EmailService:
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    )
    # Generic async email sender using aiosmtplib

    @staticmethod
    async def send_claim_submitted_email(
        customer_email: str,
        customer_name: str,
        claim_id: str,
        flight_number: str,
        airline: str
    )
    # Sends claim confirmation with flight details

    @staticmethod
    async def send_status_update_email(
        customer_email: str,
        customer_name: str,
        claim_id: str,
        old_status: str,
        new_status: str,
        flight_number: str,
        airline: str,
        change_reason: Optional[str],
        compensation_amount: Optional[float]
    )
    # Sends dynamic color-coded status update

    @staticmethod
    async def send_document_rejected_email(
        customer_email: str,
        customer_name: str,
        claim_id: str,
        document_type: str,
        rejection_reason: str,
        flight_number: str,
        airline: str
    )
    # Sends document rejection with tips
```

**Configuration**:
- Uses Gmail SMTP (smtp.gmail.com:587)
- Custom "From" address: noreply@claimplane.com
- TLS encryption
- Configurable via environment variables

### Async Task Processing (Phase 2)

#### `celery_app.py` - Celery Configuration
**Responsibilities**:
- Celery app initialization
- Redis broker configuration
- Task discovery and registration
- Retry policy configuration
- Task time limits

**Configuration**:
```python
celery_app = Celery(
    'flight_claim_worker',
    broker=config.CELERY_BROKER_URL,    # Redis
    backend=config.CELERY_RESULT_BACKEND # Redis
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_time_limit=30 * 60,  # 30 minute timeout
    task_default_retry_delay=60,
    task_max_retries=3
)

# Auto-discover tasks in app.tasks
celery_app.autodiscover_tasks(['app.tasks'])
```

#### `tasks/claim_tasks.py` - Email Notification Tasks
**Responsibilities**:
- Async email task execution
- Retry logic with exponential backoff
- Error logging
- Async function wrapping

**Key Tasks**:
```python
@celery_app.task(name="send_claim_submitted_email", bind=True, max_retries=3)
def send_claim_submitted_email(self, customer_email, customer_name, claim_id, flight_number, airline)
# Queued after claim creation

@celery_app.task(name="send_status_update_email", bind=True, max_retries=3)
def send_status_update_email(self, customer_email, customer_name, claim_id, old_status, new_status, ...)
# Queued after status change

@celery_app.task(name="send_document_rejected_email", bind=True, max_retries=3)
def send_document_rejected_email(self, customer_email, customer_name, claim_id, document_type, rejection_reason, ...)
# Queued after document rejection
```

**Retry Strategy**:
- Max retries: 3
- Exponential backoff: 60s, 120s, 240s
- Logs all failures for monitoring

### Email Templates (`templates/emails/`)

#### HTML Email Templates (Phase 2)
**Responsibilities**:
- Professional branded emails
- Dynamic content rendering
- Mobile-responsive design
- Color-coded status indicators

**Templates**:

##### `claim_submitted.html`
- **Purpose**: Claim submission confirmation
- **Style**: Green header, welcoming tone
- **Content**: Claim ID, flight details, next steps
- **CTA**: Track claim status link

##### `status_updated.html`
- **Purpose**: Status change notification
- **Style**: Dynamic color (green=approved, red=rejected, blue=in progress, orange=documents needed)
- **Content**: Old/new status, reason, compensation (if applicable), flight details
- **Conditional**: Shows compensation section only for approved claims

##### `document_rejected.html`
- **Purpose**: Document rejection notification
- **Style**: Orange warning header
- **Content**: Document type, rejection reason, re-upload instructions
- **Tips**: Helpful tips for submitting valid documents

**Rendering**: Uses Jinja2 for template rendering with variable substitution

### Error Handling

#### `exceptions.py` - Custom Exception Definitions
**Responsibilities**:
- Domain-specific exception types
- HTTP status code mapping
- Error message standardization
- Exception hierarchy management

**Exception Hierarchy**:
```python
class FlightClaimException(Exception):
    """Base exception for flight claim system"""
    def __init__(self, message: str, status_code: int = 500)

class NotFoundException(FlightClaimException):
    """Resource not found (404)"""

class ValidationException(FlightClaimException):
    """Validation errors (400)"""

class ConflictException(FlightClaimException):
    """Resource conflicts (409)"""

class DatabaseException(FlightClaimException):
    """Database errors (500)"""
```

#### `middleware.py` - Error Handling Middleware
**Responsibilities**:
- Global exception handling
- Error response formatting
- HTTP status code mapping
- Detailed error information for debugging

**Exception Handlers**:
```python
async def flight_claim_exception_handler(request: Request, exc: FlightClaimException)
# Handle custom business logic exceptions

async def validation_exception_handler(request: Request, exc: Union[RequestValidationError, ValidationError])
# Handle Pydantic validation errors

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError)
# Handle database-related exceptions (integrity, foreign key, connection)

async def general_exception_handler(request: Request, exc: Exception)
# Handle unexpected system exceptions
```

## Infrastructure Files

### `Dockerfile` - Container Configuration
**Purpose**: Application containerization
- Multi-stage build for optimized image size
- Python 3.11 slim base image
- Dependency installation and caching
- Application code copying
- Runtime user setup
- Health check configuration

### `docker-compose.yml` - Multi-Container Setup (Updated Phase 2)
**Services**:
- **db**: PostgreSQL 15 database with persistent storage
- **redis**: Redis 7 for Celery message broker and result backend
- **celery_worker**: Background task worker for async email processing
- **api**: FastAPI application container
- **nginx**: Reverse proxy for load balancing (optional)

**Phase 2 Additions**:
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5

celery_worker:
  build: .
  command: celery -A app.celery_app worker --loglevel=info
  environment:
    - REDIS_URL=redis://redis:6379
    - SMTP_HOST=smtp.gmail.com
    - SMTP_PORT=587
    - SMTP_USERNAME=${SMTP_USERNAME}
    - SMTP_PASSWORD=${SMTP_PASSWORD}
    - SMTP_FROM_EMAIL=noreply@claimplane.com
  depends_on:
    - redis
    - db
```

**Key Features**:
- Health checks for service dependencies
- Volume mounting for development
- Environment variable configuration for SMTP
- Network isolation and communication
- Shared environment between API and Celery worker

### `nginx.conf` - Reverse Proxy Configuration
**Responsibilities**:
- Load balancing to API instances
- Static file serving
- Request/response header management
- Connection timeout configuration
- Upstream server health monitoring

### `requirements.txt` - Dependency Management (Updated Phase 2)
**Categories**:
- **Web Framework**: FastAPI, Uvicorn
- **Database**: SQLAlchemy, AsyncPG, Alembic
- **Validation**: Pydantic, email-validator
- **Security**: python-jose, passlib, cryptography (Fernet)
- **File Management**: python-magic (libmagic), PyPDF2
- **File Storage**: Nextcloud WebDAV integration
- **Task Queue (Phase 2)**: Celery, Redis
- **Email (Phase 2)**: aiosmtplib, Jinja2
- **Development**: pytest, httpx
- **Utilities**: python-dotenv, structlog

**Phase 2 Additions**:
```txt
celery==5.3.4
redis==5.0.1
aiosmtplib==3.0.1
jinja2==3.1.2
```

## Documentation Structure (`docs/`)

### Technical Documentation
- `system-architecture-overview.md` - Complete architecture documentation
- `database-schema.md` - Database design and relationships
- `api-flow-diagrams.md` - Request/response flow diagrams
- `project-structure.md` - This comprehensive structure guide

### Legacy Documentation
- `mvp_plan.md` - Original project planning
- `db_schema.md` - Initial database design
- Various implementation and testing guides

## Design Patterns and Principles

### Repository Pattern Implementation
- **Separation of Concerns**: Data access isolated from business logic
- **Testability**: Easy mocking of data layer for unit tests
- **Consistency**: Standardized CRUD operations across entities
- **Flexibility**: Easy to swap data sources or add caching

### Dependency Injection
- **Database Sessions**: Automatic session management with cleanup
- **Repository Instances**: Clean dependency resolution
- **Configuration**: Environment-based configuration injection

### Clean Architecture Layers
1. **Presentation Layer**: FastAPI routers and middleware
2. **Business Logic Layer**: Pydantic schemas and validation
3. **Data Access Layer**: Repository pattern implementation
4. **Data Layer**: SQLAlchemy models and database

### Error Handling Strategy
- **Layered Exception Handling**: Different handlers for different exception types
- **Consistent Response Format**: Standardized error response structure
- **Information Security**: Sanitized error messages in production
- **Debugging Support**: Detailed error information for development

This project structure provides excellent separation of concerns, maintainability, testability, and scalability for the Flight Claim System.