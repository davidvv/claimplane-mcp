# Data Flow Visualization

## Flight Claim System - Complete Request Journey

This document provides detailed visual representations of how data flows through the Flight Claim System, from the initial HTTP request through all system layers to the PostgreSQL database and back to the client.

## Overview: Complete System Data Flow

```mermaid
graph TB
    subgraph "Client Layer"
        CLIENT[HTTP Client<br/>Browser, curl, Mobile App]
    end

    subgraph "Infrastructure Layer"
        LB[Load Balancer<br/>Nginx :80]
    end

    subgraph "Application Layer"
        FASTAPI[FastAPI App<br/>:8000]
        
        subgraph "Middleware Stack"
            CORS[CORS Middleware]
            ERROR[Error Handling<br/>Middleware]
            AUTH[Authentication<br/>Middleware]
        end
        
        subgraph "Router Layer"
            CUSTOMER_ROUTER[Customer Router<br/>/customers]
            CLAIM_ROUTER[Claim Router<br/>/claims]
            HEALTH_ROUTER[Health Router<br/>/health]
        end
        
        subgraph "Validation Layer"
            PYDANTIC[Pydantic Schemas<br/>Request Validation]
            SERIALIZER[Response<br/>Serialization]
        end
    end

    subgraph "Business Logic Layer"
        subgraph "Repository Pattern"
            CUSTOMER_REPO[Customer Repository<br/>CRUD Operations]
            CLAIM_REPO[Claim Repository<br/>CRUD Operations]
            BASE_REPO[Base Repository<br/>Generic Operations]
        end
    end

    subgraph "Data Access Layer"
        SESSION[SQLAlchemy<br/>Async Session]
        CONNECTION_POOL[Connection Pool<br/>20 connections]
        ORM[SQLAlchemy ORM<br/>Query Builder]
    end

    subgraph "Database Layer"
        POSTGRES[(PostgreSQL 15<br/>Database)]
        
        subgraph "Tables"
            CUSTOMERS_TABLE[(customers table)]
            CLAIMS_TABLE[(claims table)]
            INDEXES[(Indexes & Constraints)]
        end
    end

    CLIENT --> LB
    LB --> FASTAPI
    FASTAPI --> CORS
    CORS --> ERROR
    ERROR --> AUTH
    AUTH --> CUSTOMER_ROUTER
    AUTH --> CLAIM_ROUTER
    AUTH --> HEALTH_ROUTER
    
    CUSTOMER_ROUTER --> PYDANTIC
    CLAIM_ROUTER --> PYDANTIC
    HEALTH_ROUTER --> PYDANTIC
    
    PYDANTIC --> CUSTOMER_REPO
    PYDANTIC --> CLAIM_REPO
    
    CUSTOMER_REPO --> BASE_REPO
    CLAIM_REPO --> BASE_REPO
    
    BASE_REPO --> SESSION
    SESSION --> CONNECTION_POOL
    CONNECTION_POOL --> ORM
    ORM --> POSTGRES
    
    POSTGRES --> CUSTOMERS_TABLE
    POSTGRES --> CLAIMS_TABLE
    POSTGRES --> INDEXES
    
    CUSTOMERS_TABLE -.-> SERIALIZER
    CLAIMS_TABLE -.-> SERIALIZER
    SERIALIZER -.-> CLIENT
```

## Detailed Request Flow Analysis

### 1. HTTP Request Entry Point

```mermaid
sequenceDiagram
    participant Client
    participant Nginx
    participant FastAPI
    participant Middleware

    Note over Client: User initiates request
    Client->>Nginx: HTTP Request<br/>POST /customers
    Note over Nginx: Load balancing<br/>SSL termination<br/>Request routing
    
    Nginx->>FastAPI: Forward to<br/>http://api:8000/customers
    Note over FastAPI: ASGI application<br/>receives request
    
    FastAPI->>Middleware: Process through<br/>middleware stack
    Note over Middleware: CORS, Auth, Error handling
    
    Middleware-->>FastAPI: Processed request
    FastAPI-->>Client: Continue to router...
```

### 2. Middleware Processing Pipeline

```mermaid
graph LR
    REQUEST[Incoming Request] --> CORS_MW[CORS Middleware]
    CORS_MW --> |"Access-Control headers"| ERROR_MW[Error Handling Middleware]
    ERROR_MW --> |"Exception wrapping"| CUSTOM_MW[Custom Middleware]
    CUSTOM_MW --> |"Business logic checks"| ROUTER[Route Resolution]
    
    CORS_MW -.-> |"CORS Error"| CORS_RESPONSE[CORS Error Response]
    ERROR_MW -.-> |"Exception"| ERROR_RESPONSE[Error Response]
    
    ROUTER --> ENDPOINT[Endpoint Handler]
```

### 3. Router and Validation Flow

```mermaid
sequenceDiagram
    participant Router as Customer Router
    participant Schema as Pydantic Schema
    participant Validator as Field Validators
    participant Repository as Customer Repository

    Router->>Schema: Validate request body
    Schema->>Validator: Apply field validation
    
    alt Validation Success
        Validator->>Schema: Valid data
        Schema->>Router: CustomerCreateSchema
        Router->>Repository: Call repository method
    else Validation Error
        Validator->>Schema: ValidationError
        Schema->>Router: 422 Unprocessable Entity
        Router-->>Router: Return error response
    end
```

### 4. Repository Pattern Data Flow

```mermaid
graph TB
    subgraph "Repository Layer Architecture"
        ENDPOINT[API Endpoint] --> REPO_INTERFACE[Repository Interface]
        
        REPO_INTERFACE --> CUSTOMER_REPO[CustomerRepository]
        REPO_INTERFACE --> CLAIM_REPO[ClaimRepository]
        
        CUSTOMER_REPO --> BASE_REPO[BaseRepository]
        CLAIM_REPO --> BASE_REPO
        
        BASE_REPO --> SESSION_INJECT[Session Injection]
        SESSION_INJECT --> CRUD_OPERATIONS[CRUD Operations]
        
        CRUD_OPERATIONS --> CREATE[create()]
        CRUD_OPERATIONS --> READ[get_by_id()]
        CRUD_OPERATIONS --> UPDATE[update()]
        CRUD_OPERATIONS --> DELETE[delete()]
        
        CREATE --> DB_OPERATION[Database Operation]
        READ --> DB_OPERATION
        UPDATE --> DB_OPERATION
        DELETE --> DB_OPERATION
    end
```

### 5. Database Transaction Flow

```mermaid
sequenceDiagram
    participant Repo as Repository
    participant Session as SQLAlchemy Session
    participant Pool as Connection Pool
    participant DB as PostgreSQL

    Note over Repo: Business logic operation
    Repo->>Session: Begin transaction
    Session->>Pool: Request connection
    Pool->>DB: Establish connection
    
    Note over Repo: CRUD operation
    Repo->>Session: session.add(instance)
    Session->>Session: Track changes
    
    Repo->>Session: session.flush()
    Session->>DB: Send SQL (no commit)
    DB-->>Session: Return results
    
    Repo->>Session: session.refresh(instance)
    Session->>DB: Fetch updated values
    DB-->>Session: Return fresh data
    
    Repo->>Session: session.commit()
    Session->>DB: COMMIT transaction
    DB-->>Session: Transaction confirmed
    
    Session->>Pool: Return connection
    Pool-->>Repo: Operation complete
```

## CRUD Operation Data Flows

### Create Customer Flow

```mermaid
graph TD
    START[POST /customers] --> VALIDATE[Pydantic Validation]
    VALIDATE --> |Valid| EMAIL_CHECK[Check Email Uniqueness]
    VALIDATE --> |Invalid| VALIDATION_ERROR[422 Validation Error]
    
    EMAIL_CHECK --> |Unique| CREATE_CUSTOMER[Create Customer Instance]
    EMAIL_CHECK --> |Exists| DUPLICATE_ERROR[400 Duplicate Email]
    
    CREATE_CUSTOMER --> DB_INSERT[INSERT INTO customers]
    DB_INSERT --> |Success| RESPONSE_SERIALIZE[Serialize Response]
    DB_INSERT --> |Error| DB_ERROR[500 Database Error]
    
    RESPONSE_SERIALIZE --> SUCCESS_RESPONSE[201 Created]
```

### Update Customer Flow (PUT vs PATCH)

```mermaid
graph TD
    UPDATE_REQUEST[Update Request] --> METHOD_CHECK{HTTP Method?}
    
    METHOD_CHECK --> |PUT| PUT_VALIDATION[All fields required<br/>CustomerUpdateSchema]
    METHOD_CHECK --> |PATCH| PATCH_VALIDATION[Optional fields<br/>CustomerPatchSchema]
    
    PUT_VALIDATION --> PUT_PROCESSING[Process all fields<br/>allow_null_values=True]
    PATCH_VALIDATION --> PATCH_FILTERING[Filter non-null fields<br/>allow_null_values=False]
    
    PUT_PROCESSING --> CUSTOMER_EXISTS[Check Customer Exists]
    PATCH_FILTERING --> CUSTOMER_EXISTS
    
    CUSTOMER_EXISTS --> |Not Found| NOT_FOUND[404 Not Found]
    CUSTOMER_EXISTS --> |Found| EMAIL_UNIQUE[Check Email Uniqueness]
    
    EMAIL_UNIQUE --> |Conflict| EMAIL_CONFLICT[400 Email Exists]
    EMAIL_UNIQUE --> |Unique| UPDATE_DB[UPDATE customers SET...]
    
    UPDATE_DB --> |PUT| UPDATE_ALL[Update all fields<br/>including nulls]
    UPDATE_DB --> |PATCH| UPDATE_PARTIAL[Update only<br/>provided fields]
    
    UPDATE_ALL --> COMMIT_TRANSACTION[Commit Transaction]
    UPDATE_PARTIAL --> COMMIT_TRANSACTION
    
    COMMIT_TRANSACTION --> SERIALIZE_RESPONSE[Serialize Updated Customer]
    SERIALIZE_RESPONSE --> SUCCESS[200 OK]
```

### Complex Claim Creation Flow

```mermaid
sequenceDiagram
    participant Client
    participant ClaimRouter
    participant CustomerRepo
    participant ClaimRepo
    participant Database

    Client->>ClaimRouter: POST /claims/submit<br/>(Customer + Claim data)
    
    Note over ClaimRouter: Validate request schema
    ClaimRouter->>ClaimRouter: Validate ClaimRequestSchema
    
    Note over ClaimRouter: Check if customer exists
    ClaimRouter->>CustomerRepo: get_by_email(email)
    CustomerRepo->>Database: SELECT * FROM customers WHERE email = ?
    
    alt Customer Exists
        Database-->>CustomerRepo: Customer record
        CustomerRepo-->>ClaimRouter: Existing customer
        Note over ClaimRouter: Use existing customer
    else Customer Not Found
        CustomerRepo-->>ClaimRouter: None
        Note over ClaimRouter: Create new customer
        ClaimRouter->>CustomerRepo: create_customer(...)
        CustomerRepo->>Database: INSERT INTO customers (...)
        Database-->>CustomerRepo: New customer record
        CustomerRepo-->>ClaimRouter: New customer
    end
    
    Note over ClaimRouter: Create claim with customer ID
    ClaimRouter->>ClaimRepo: create_claim(customer_id, flight_info, ...)
    ClaimRepo->>Database: INSERT INTO claims (customer_id, flight_number, ...)
    Database-->>ClaimRepo: New claim record
    
    ClaimRepo-->>ClaimRouter: Created claim
    ClaimRouter-->>Client: 201 Created + Claim response
```

## Data Transformation Pipeline

### Request Data Transformation

```mermaid
graph LR
    subgraph "Request Pipeline"
        JSON[Raw JSON<br/>camelCase] --> PYDANTIC[Pydantic Schema<br/>Field aliases]
        PYDANTIC --> VALIDATION[Field Validation<br/>Type conversion]
        VALIDATION --> PYTHON_DICT[Python Dict<br/>snake_case]
        PYTHON_DICT --> SQLALCHEMY[SQLAlchemy Model<br/>Database format]
        SQLALCHEMY --> SQL[SQL Parameters<br/>Parameterized query]
    end
```

### Response Data Transformation

```mermaid
graph LR
    subgraph "Response Pipeline"
        DB_RESULT[Database Result<br/>Raw SQL result] --> ORM_INSTANCE[SQLAlchemy Instance<br/>Python object]
        ORM_INSTANCE --> PYDANTIC_RESPONSE[Pydantic Response Schema<br/>Validation + serialization]
        PYDANTIC_RESPONSE --> JSON_RESPONSE[JSON Response<br/>camelCase for client]
        JSON_RESPONSE --> HTTP_RESPONSE[HTTP Response<br/>Status code + headers]
    end
```

### Field Mapping Examples

```mermaid
graph TB
    subgraph "Customer Data Transformation"
        CLIENT_JSON["{<br/>  'firstName': 'John',<br/>  'lastName': 'Doe',<br/>  'email': 'john@example.com'<br/>}"]
        
        PYDANTIC_SCHEMA["CustomerCreateSchema<br/>first_name = Field(alias='firstName')<br/>last_name = Field(alias='lastName')"]
        
        PYTHON_DICT["{<br/>  'first_name': 'John',<br/>  'last_name': 'Doe',<br/>  'email': 'john@example.com'<br/>}"]
        
        SQL_QUERY["INSERT INTO customers<br/>(first_name, last_name, email)<br/>VALUES ($1, $2, $3)"]
        
        DB_RESULT["customers table:<br/>first_name | last_name | email<br/>John       | Doe       | john@..."]
        
        RESPONSE_JSON["{<br/>  'firstName': 'John',<br/>  'lastName': 'Doe',<br/>  'email': 'john@example.com',<br/>  'createdAt': '2024-01-15T10:30:00Z'<br/>}"]
        
        CLIENT_JSON --> PYDANTIC_SCHEMA
        PYDANTIC_SCHEMA --> PYTHON_DICT
        PYTHON_DICT --> SQL_QUERY
        SQL_QUERY --> DB_RESULT
        DB_RESULT --> RESPONSE_JSON
    end
```

## Error Flow Visualization

### Exception Propagation Flow

```mermaid
graph TD
    ERROR_SOURCE[Error Source] --> ERROR_TYPE{Error Type?}
    
    ERROR_TYPE --> |Pydantic| VALIDATION_ERROR[ValidationError]
    ERROR_TYPE --> |SQLAlchemy| DB_ERROR[SQLAlchemyError]
    ERROR_TYPE --> |Custom| BUSINESS_ERROR[FlightClaimException]
    ERROR_TYPE --> |System| SYSTEM_ERROR[General Exception]
    
    VALIDATION_ERROR --> VALIDATION_HANDLER[validation_exception_handler]
    DB_ERROR --> DB_ERROR_TYPE{Database Error Type}
    BUSINESS_ERROR --> BUSINESS_HANDLER[flight_claim_exception_handler]
    SYSTEM_ERROR --> GENERAL_HANDLER[general_exception_handler]
    
    DB_ERROR_TYPE --> |Integrity| INTEGRITY_HANDLER[409 Conflict]
    DB_ERROR_TYPE --> |Foreign Key| FK_HANDLER[400 Bad Request]
    DB_ERROR_TYPE --> |Connection| CONN_HANDLER[500 Internal Server Error]
    
    VALIDATION_HANDLER --> FORMAT_ERROR[Format Error Response]
    INTEGRITY_HANDLER --> FORMAT_ERROR
    FK_HANDLER --> FORMAT_ERROR
    CONN_HANDLER --> FORMAT_ERROR
    BUSINESS_HANDLER --> FORMAT_ERROR
    GENERAL_HANDLER --> FORMAT_ERROR
    
    FORMAT_ERROR --> ERROR_RESPONSE[Standardized Error Response]
    ERROR_RESPONSE --> CLIENT[Return to Client]
```

### Error Response Structure Flow

```mermaid
graph LR
    subgraph "Error Response Formation"
        EXCEPTION[Exception Raised] --> HANDLER[Exception Handler]
        HANDLER --> STATUS_CODE[Determine Status Code]
        STATUS_CODE --> ERROR_MESSAGE[Format Error Message]
        ERROR_MESSAGE --> ERROR_DETAILS[Extract Error Details]
        ERROR_DETAILS --> TIMESTAMP[Add Timestamp]
        TIMESTAMP --> JSON_RESPONSE[JSON Error Response]
        
        JSON_RESPONSE --> STRUCTURE["{<br/>  'success': false,<br/>  'error': {<br/>    'code': 'ERROR_TYPE',<br/>    'message': '...',<br/>    'details': [...]<br/>  },<br/>  'timestamp': '...'<br/>}"]
    end
```

## Performance Data Flow Analysis

### Connection Pool Flow

```mermaid
sequenceDiagram
    participant App as Application
    participant Pool as Connection Pool
    participant DB as Database

    Note over Pool: Pool initialized with<br/>20 permanent connections
    
    App->>Pool: Request connection
    
    alt Connection Available
        Pool->>App: Return existing connection
        App->>DB: Execute query
        DB-->>App: Return results
        App->>Pool: Return connection to pool
    else Pool Exhausted
        Pool->>DB: Create new connection<br/>(up to max_overflow=30)
        DB-->>Pool: New connection
        Pool->>App: Return new connection
        App->>DB: Execute query
        DB-->>App: Return results
        App->>Pool: Return connection
        Note over Pool: Connection may be closed<br/>if over pool_size
    else Max Connections Reached
        Pool-->>App: ConnectionPoolTimeout
        App-->>App: Handle timeout error
    end
```

### Query Optimization Flow

```mermaid
graph TB
    QUERY_REQUEST[Query Request] --> CACHE_CHECK[Check Query Plan Cache]
    CACHE_CHECK --> |Hit| CACHED_PLAN[Use Cached Plan]
    CACHE_CHECK --> |Miss| PLAN_GENERATION[Generate Query Plan]
    
    PLAN_GENERATION --> INDEX_CHECK[Check Available Indexes]
    INDEX_CHECK --> OPTIMIZATION[Query Optimization]
    OPTIMIZATION --> EXECUTION_PLAN[Final Execution Plan]
    
    CACHED_PLAN --> EXECUTE_QUERY[Execute Query]
    EXECUTION_PLAN --> EXECUTE_QUERY
    
    EXECUTE_QUERY --> RESULT_SET[Return Result Set]
    RESULT_SET --> CACHE_RESULT[Cache Results if Applicable]
    CACHE_RESULT --> RESPONSE[Return to Application]
```

## Monitoring and Observability Flow

### Request Tracing Flow

```mermaid
graph TD
    REQUEST_START[Request Initiated] --> REQUEST_ID[Generate Request ID]
    REQUEST_ID --> LOG_REQUEST[Log Request Details]
    LOG_REQUEST --> MIDDLEWARE_TRACE[Middleware Tracing]
    MIDDLEWARE_TRACE --> ROUTER_TRACE[Router Tracing]
    ROUTER_TRACE --> REPO_TRACE[Repository Tracing]
    REPO_TRACE --> DB_TRACE[Database Query Tracing]
    DB_TRACE --> RESPONSE_TRACE[Response Tracing]
    RESPONSE_TRACE --> PERFORMANCE_METRICS[Collect Performance Metrics]
    PERFORMANCE_METRICS --> LOG_COMPLETION[Log Request Completion]
```

### Health Check Data Flow

```mermaid
sequenceDiagram
    participant Client
    participant HealthRouter
    participant Database
    participant SystemInfo

    Client->>HealthRouter: GET /health/detailed
    
    HealthRouter->>Database: Test connectivity<br/>SELECT 1
    
    alt Database Available
        Database-->>HealthRouter: Query successful
        HealthRouter->>SystemInfo: Collect system metrics
        SystemInfo-->>HealthRouter: Python version, platform, etc.
        
        HealthRouter-->>Client: 200 OK<br/>{<br/>  "status": "healthy",<br/>  "database": {"status": "healthy"},<br/>  "system": {...}<br/>}
    else Database Error
        Database-->>HealthRouter: Connection failed
        HealthRouter-->>Client: 503 Service Unavailable<br/>{<br/>  "status": "unhealthy",<br/>  "database": {"status": "failed"}<br/>}
    end
```

This comprehensive data flow visualization demonstrates how requests traverse every layer of the Flight Claim System, providing complete transparency into the system's operation from HTTP entry to database persistence and back.