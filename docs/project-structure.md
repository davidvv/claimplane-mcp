# Project Structure Guide

## Flight Claim System - Complete Project Organization

This document provides a comprehensive overview of the Flight Claim System's project structure, explaining the purpose and responsibility of each module, directory, and file within the codebase.

## Project Root Structure

```
flight_claim/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization with version
│   ├── main.py                  # FastAPI application entry point
│   ├── database.py              # Database configuration and session management
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic validation schemas
│   ├── exceptions.py            # Custom exception definitions
│   ├── middleware.py            # Error handling middleware
│   ├── repositories/            # Data access layer
│   │   ├── __init__.py         # Repository exports
│   │   ├── base.py             # Generic base repository
│   │   ├── customer_repository.py  # Customer data operations
│   │   └── claim_repository.py     # Claim data operations
│   └── routers/                 # API route handlers
│       ├── __init__.py         # Router exports
│       ├── customers.py        # Customer API endpoints
│       ├── claims.py          # Claim API endpoints
│       └── health.py          # System health endpoints
├── docs/                        # Project documentation
│   ├── system-architecture-overview.md  # Architecture documentation
│   ├── database-schema.md              # Database design documentation
│   ├── api-flow-diagrams.md            # API flow documentation
│   ├── project-structure.md            # This file
│   ├── mvp_plan.md                     # Original MVP planning
│   ├── db_schema.md                    # Legacy schema documentation
│   └── [other legacy docs]
├── API/                         # API specification files
│   └── openapi.yaml            # Complete OpenAPI specification
├── requirements.txt             # Python dependency specifications
├── Dockerfile                   # Container build configuration
├── docker-compose.yml          # Multi-container deployment setup
├── nginx.conf                  # Nginx reverse proxy configuration
├── .env                        # Environment variables (not committed)
├── .gitignore                  # Git ignore patterns
├── README.md                   # Project overview and quick start
├── init_db.py                  # Database initialization script
└── [test files]                # Various testing scripts
```

## Application Package (`app/`)

### Core Application Files

#### `__init__.py`
```python
"""Flight Claim System API"""
__version__ = "1.0.0"
```

**Purpose**: Package initialization and version management
- Defines the application version used throughout the system
- Enables import of the app package
- Centralizes version information for consistency

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

##### Claim Model
```python
class Claim(Base):
    __tablename__ = "claims"
    
    # Status and incident type enums
    INCIDENT_TYPES = ["delay", "cancellation", "denied_boarding", "baggage_delay"]
    STATUS_TYPES = ["draft", "submitted", "under_review", "approved", "rejected", "paid", "closed"]
    
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
    
    # Audit timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="claims")
    
    # Validation methods for business rules
    @validates('incident_type', 'status', 'departure_airport', 'arrival_airport', 'flight_number')
    def validate_fields(self, key, value):
        # Field-specific validation logic
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

### `docker-compose.yml` - Multi-Container Setup
**Services**:
- **db**: PostgreSQL 15 database with persistent storage
- **api**: FastAPI application container
- **nginx**: Reverse proxy for load balancing

**Key Features**:
- Health checks for service dependencies
- Volume mounting for development
- Environment variable configuration
- Network isolation and communication

### `nginx.conf` - Reverse Proxy Configuration
**Responsibilities**:
- Load balancing to API instances
- Static file serving
- Request/response header management
- Connection timeout configuration
- Upstream server health monitoring

### `requirements.txt` - Dependency Management
**Categories**:
- **Web Framework**: FastAPI, Uvicorn
- **Database**: SQLAlchemy, AsyncPG, Alembic  
- **Validation**: Pydantic, email-validator
- **Security**: python-jose, passlib
- **Development**: pytest, httpx
- **Utilities**: python-dotenv, structlog

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