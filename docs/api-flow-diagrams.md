# API Flow Diagrams

## Flight Claim System - Request/Response Flow Documentation

This document provides detailed visual representations of how HTTP requests flow through the Flight Claim System, from initial request to final response, including all CRUD operations, validation steps, and error handling paths.

## Overview: General Request Flow

```mermaid
graph TD
    CLIENT[HTTP Client] --> NGINX[Nginx Reverse Proxy<br/>Port 80]
    NGINX --> FASTAPI[FastAPI Application<br/>Port 8000]
    FASTAPI --> MIDDLEWARE[Error Handling<br/>Middleware]
    MIDDLEWARE --> CORS[CORS Middleware]
    CORS --> ROUTER{Route Resolution}
    
    ROUTER -->|/customers| CUSTOMER_ROUTER[Customer Router]
    ROUTER -->|/claims| CLAIM_ROUTER[Claim Router]
    ROUTER -->|/health| HEALTH_ROUTER[Health Router]
    
    CUSTOMER_ROUTER --> VALIDATION[Pydantic Schema<br/>Validation]
    CLAIM_ROUTER --> VALIDATION
    HEALTH_ROUTER --> VALIDATION
    
    VALIDATION -->|Valid| REPOSITORY[Repository Layer]
    VALIDATION -->|Invalid| ERROR_HANDLER[Error Handler]
    
    REPOSITORY --> DATABASE[(PostgreSQL<br/>Database)]
    DATABASE --> REPOSITORY
    
    REPOSITORY --> RESPONSE[Response Schema<br/>Serialization]
    ERROR_HANDLER --> ERROR_RESPONSE[Error Response]
    
    RESPONSE --> CLIENT
    ERROR_RESPONSE --> CLIENT
```

## Customer Operations Flow

### POST /customers - Create Customer

```mermaid
sequenceDiagram
    participant Client
    participant Nginx
    participant FastAPI
    participant CustomerRouter
    participant CustomerCreateSchema
    participant CustomerRepository
    participant Database
    participant CustomerResponseSchema

    Client->>Nginx: POST /customers<br/>Content-Type: application/json
    Nginx->>FastAPI: Forward Request
    FastAPI->>CustomerRouter: Route to create_customer()
    
    CustomerRouter->>CustomerCreateSchema: Validate Request Body
    alt Validation Success
        CustomerCreateSchema->>CustomerRouter: Valid CustomerCreateSchema object
        CustomerRouter->>CustomerRepository: Check email exists
        CustomerRepository->>Database: SELECT * FROM customers WHERE email = ?
        Database-->>CustomerRepository: Query result
        
        alt Email Not Exists
            CustomerRepository->>Database: INSERT INTO customers (...)
            Database-->>CustomerRepository: New customer record
            CustomerRepository-->>CustomerRouter: Customer object
            CustomerRouter->>CustomerResponseSchema: Serialize response
            CustomerResponseSchema-->>CustomerRouter: Response dict
            CustomerRouter-->>FastAPI: 201 Created + Customer data
        else Email Exists
            CustomerRouter-->>FastAPI: 400 Bad Request<br/>"Email already exists"
        end
    else Validation Error
        CustomerCreateSchema-->>CustomerRouter: ValidationError
        CustomerRouter-->>FastAPI: 422 Unprocessable Entity
    end
    
    FastAPI-->>Nginx: HTTP Response
    Nginx-->>Client: Final Response
```

### GET /customers/{customer_id} - Get Customer

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant CustomerRouter
    participant CustomerRepository
    participant Database
    participant CustomerResponseSchema

    Client->>FastAPI: GET /customers/{customer_id}
    FastAPI->>CustomerRouter: Route to get_customer(customer_id)
    
    CustomerRouter->>CustomerRepository: get_by_id(customer_id)
    CustomerRepository->>Database: SELECT * FROM customers WHERE id = ?
    Database-->>CustomerRepository: Customer record or None
    
    alt Customer Found
        CustomerRepository-->>CustomerRouter: Customer object
        CustomerRouter->>CustomerResponseSchema: Serialize customer
        CustomerResponseSchema-->>CustomerRouter: Response dict
        CustomerRouter-->>FastAPI: 200 OK + Customer data
    else Customer Not Found
        CustomerRepository-->>CustomerRouter: None
        CustomerRouter-->>FastAPI: 404 Not Found<br/>"Customer not found"
    end
    
    FastAPI-->>Client: HTTP Response
```

### PUT /customers/{customer_id} - Update Customer (Complete)

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant CustomerRouter
    participant CustomerUpdateSchema
    participant CustomerRepository
    participant Database

    Client->>FastAPI: PUT /customers/{customer_id}<br/>Complete customer data
    FastAPI->>CustomerRouter: Route to update_customer()
    
    CustomerRouter->>CustomerUpdateSchema: Validate complete request body
    alt Validation Success
        CustomerUpdateSchema->>CustomerRouter: Valid CustomerUpdateSchema
        CustomerRouter->>CustomerRepository: get_by_id(customer_id)
        CustomerRepository->>Database: SELECT * FROM customers WHERE id = ?
        
        alt Customer Exists
            Database-->>CustomerRepository: Customer record
            CustomerRepository-->>CustomerRouter: Customer object
            
            Note over CustomerRouter: Check email uniqueness if changed
            CustomerRouter->>CustomerRepository: get_by_email(new_email)
            
            alt Email Available or Same
                CustomerRouter->>CustomerRepository: update_customer(allow_null_values=True)
                CustomerRepository->>Database: UPDATE customers SET ... WHERE id = ?
                Database-->>CustomerRepository: Updated customer
                CustomerRepository-->>CustomerRouter: Customer object
                CustomerRouter-->>FastAPI: 200 OK + Updated customer
            else Email Exists
                CustomerRouter-->>FastAPI: 400 Bad Request<br/>"Email already exists"
            end
        else Customer Not Found
            CustomerRouter-->>FastAPI: 404 Not Found
        end
    else Validation Error
        CustomerUpdateSchema-->>CustomerRouter: ValidationError
        CustomerRouter-->>FastAPI: 422 Unprocessable Entity
    end
    
    FastAPI-->>Client: HTTP Response
```

### PATCH /customers/{customer_id} - Partial Update

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant CustomerRouter
    participant CustomerPatchSchema
    participant CustomerRepository
    participant Database

    Client->>FastAPI: PATCH /customers/{customer_id}<br/>Partial customer data
    FastAPI->>CustomerRouter: Route to patch_customer()
    
    CustomerRouter->>CustomerPatchSchema: Validate partial request body
    alt Validation Success
        CustomerPatchSchema->>CustomerRouter: Valid CustomerPatchSchema
        CustomerRouter->>CustomerRepository: get_by_id(customer_id)
        
        alt Customer Exists
            CustomerRepository-->>CustomerRouter: Customer object
            
            Note over CustomerRouter: Filter non-null fields only
            CustomerRouter->>CustomerRouter: build_update_data()<br/>Exclude None values
            
            alt Has Fields to Update
                CustomerRouter->>CustomerRepository: update_customer(allow_null_values=False)
                Note over CustomerRepository: Only update provided fields
                CustomerRepository->>Database: UPDATE customers SET field1=?, field2=?
                Database-->>CustomerRepository: Updated customer
                CustomerRepository-->>CustomerRouter: Customer object
                CustomerRouter-->>FastAPI: 200 OK + Updated customer
            else No Fields to Update
                CustomerRouter-->>FastAPI: 200 OK + Existing customer
            end
        else Customer Not Found
            CustomerRouter-->>FastAPI: 404 Not Found
        end
    else Validation Error
        CustomerPatchSchema-->>CustomerRouter: ValidationError
        CustomerRouter-->>FastAPI: 422 Unprocessable Entity
    end
    
    FastAPI-->>Client: HTTP Response
```

## Claim Operations Flow

### POST /claims - Create Claim

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant ClaimRouter
    participant ClaimCreateSchema
    participant CustomerRepository
    participant ClaimRepository
    participant Database

    Client->>FastAPI: POST /claims<br/>Claim data with customer_id
    FastAPI->>ClaimRouter: Route to create_claim()
    
    ClaimRouter->>ClaimCreateSchema: Validate request body
    alt Validation Success
        ClaimCreateSchema->>ClaimRouter: Valid ClaimCreateSchema
        
        Note over ClaimRouter: Verify customer exists
        ClaimRouter->>CustomerRepository: get_by_id(customer_id)
        CustomerRepository->>Database: SELECT * FROM customers WHERE id = ?
        
        alt Customer Exists
            Database-->>CustomerRepository: Customer record
            CustomerRepository-->>ClaimRouter: Customer object
            
            ClaimRouter->>ClaimRepository: create_claim(...)
            ClaimRepository->>Database: INSERT INTO claims (...)<br/>WITH airport codes normalized
            Database-->>ClaimRepository: New claim record
            ClaimRepository-->>ClaimRouter: Claim object
            ClaimRouter-->>FastAPI: 201 Created + Claim data
        else Customer Not Found
            CustomerRepository-->>ClaimRouter: None
            ClaimRouter-->>FastAPI: 404 Not Found<br/>"Customer not found"
        end
    else Validation Error
        ClaimCreateSchema-->>ClaimRouter: ValidationError
        ClaimRouter-->>FastAPI: 422 Unprocessable Entity
    end
    
    FastAPI-->>Client: HTTP Response
```

### POST /claims/submit - Submit Claim with Customer Info

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant ClaimRouter
    participant ClaimRequestSchema
    participant CustomerRepository
    participant ClaimRepository
    participant Database

    Client->>FastAPI: POST /claims/submit<br/>Customer + Claim data
    FastAPI->>ClaimRouter: Route to submit_claim_with_customer()
    
    ClaimRouter->>ClaimRequestSchema: Validate request body
    alt Validation Success
        ClaimRequestSchema->>ClaimRouter: Valid ClaimRequestSchema
        
        Note over ClaimRouter: Check if customer exists by email
        ClaimRouter->>CustomerRepository: get_by_email(email)
        CustomerRepository->>Database: SELECT * FROM customers WHERE email = ?
        
        alt Customer Exists
            Database-->>CustomerRepository: Customer record
            CustomerRepository-->>ClaimRouter: Existing customer
        else Customer Not Found
            CustomerRepository-->>ClaimRouter: None
            Note over ClaimRouter: Create new customer
            ClaimRouter->>CustomerRepository: create_customer(...)
            CustomerRepository->>Database: INSERT INTO customers (...)
            Database-->>CustomerRepository: New customer record
            CustomerRepository-->>ClaimRouter: New customer object
        end
        
        Note over ClaimRouter: Create claim with customer ID
        ClaimRouter->>ClaimRepository: create_claim(customer_id, ...)
        ClaimRepository->>Database: INSERT INTO claims (...)
        Database-->>ClaimRepository: New claim record
        ClaimRepository-->>ClaimRouter: Claim object
        ClaimRouter-->>FastAPI: 201 Created + Claim data
    else Validation Error
        ClaimRequestSchema-->>ClaimRouter: ValidationError
        ClaimRouter-->>FastAPI: 422 Unprocessable Entity
    end
    
    FastAPI-->>Client: HTTP Response
```

## PUT vs PATCH Implementation Flow

### Key Differences in Repository Layer

```mermaid
graph TD
    REQUEST[HTTP Request] --> METHOD_CHECK{HTTP Method?}
    
    METHOD_CHECK -->|PUT| PUT_VALIDATION[PUT Schema Validation<br/>All fields required]
    METHOD_CHECK -->|PATCH| PATCH_VALIDATION[PATCH Schema Validation<br/>Optional fields only]
    
    PUT_VALIDATION --> PUT_REPOSITORY[Repository.update_customer<br/>allow_null_values=True]
    PATCH_VALIDATION --> PATCH_FILTER[Filter None values<br/>Only update provided fields]
    
    PATCH_FILTER --> PATCH_REPOSITORY[Repository.update_customer<br/>allow_null_values=False]
    
    PUT_REPOSITORY --> PUT_UPDATE[Update ALL fields<br/>Set None values to NULL]
    PATCH_REPOSITORY --> PATCH_UPDATE[Update ONLY provided fields<br/>Preserve existing values]
    
    PUT_UPDATE --> DATABASE[(Database)]
    PATCH_UPDATE --> DATABASE
    
    DATABASE --> RESPONSE[Updated Record Response]
```

### Repository Update Logic

```mermaid
graph TD
    UPDATE_CALL[update_customer called] --> NULL_CHECK{allow_null_values?}
    
    NULL_CHECK -->|True - PUT| ALL_FIELDS[update_data = kwargs<br/>Include None values]
    NULL_CHECK -->|False - PATCH| FILTER_FIELDS[update_data = filter None values]
    
    ALL_FIELDS --> APPLY_UPDATE[Apply all provided fields<br/>None values become NULL]
    FILTER_FIELDS --> APPLY_PARTIAL[Apply only non-None fields<br/>Preserve existing data]
    
    APPLY_UPDATE --> COMMIT[session.commit]
    APPLY_PARTIAL --> COMMIT
    
    COMMIT --> RETURN[Return updated entity]
```

## Error Handling Flow

### Comprehensive Error Processing

```mermaid
graph TD
    REQUEST[Incoming Request] --> CORS_CHECK[CORS Validation]
    CORS_CHECK -->|Pass| ROUTE_RESOLUTION[Route Resolution]
    CORS_CHECK -->|Fail| CORS_ERROR[CORS Error Response]
    
    ROUTE_RESOLUTION -->|Found| SCHEMA_VALIDATION[Pydantic Schema Validation]
    ROUTE_RESOLUTION -->|Not Found| NOT_FOUND_ERROR[404 Not Found]
    
    SCHEMA_VALIDATION -->|Valid| BUSINESS_LOGIC[Business Logic Processing]
    SCHEMA_VALIDATION -->|Invalid| VALIDATION_ERROR[422 Validation Error]
    
    BUSINESS_LOGIC --> DATABASE_OP{Database Operation}
    
    DATABASE_OP -->|Success| SUCCESS_RESPONSE[200/201 Success Response]
    DATABASE_OP -->|Integrity Error| CONSTRAINT_ERROR[409 Conflict Error]
    DATABASE_OP -->|Foreign Key Error| FOREIGN_KEY_ERROR[400 Bad Request]
    DATABASE_OP -->|Connection Error| DB_CONNECTION_ERROR[500 Internal Server Error]
    
    VALIDATION_ERROR --> ERROR_MIDDLEWARE[Error Handling Middleware]
    CONSTRAINT_ERROR --> ERROR_MIDDLEWARE
    FOREIGN_KEY_ERROR --> ERROR_MIDDLEWARE
    DB_CONNECTION_ERROR --> ERROR_MIDDLEWARE
    
    ERROR_MIDDLEWARE --> FORMATTED_ERROR[Formatted Error Response<br/>JSON with details]
    
    SUCCESS_RESPONSE --> CLIENT[Client Response]
    FORMATTED_ERROR --> CLIENT
    CORS_ERROR --> CLIENT
    NOT_FOUND_ERROR --> CLIENT
```

### Error Response Format

```mermaid
graph LR
    subgraph "Error Response Structure"
        SUCCESS[success: false]
        ERROR_OBJECT[error: object]
        TIMESTAMP[timestamp: ISO 8601]
    end
    
    subgraph "Error Object Details"
        CODE[code: ERROR_TYPE]
        MESSAGE[message: Human readable]
        DETAILS[details: Array of specifics]
    end
    
    ERROR_OBJECT --> CODE
    ERROR_OBJECT --> MESSAGE
    ERROR_OBJECT --> DETAILS
```

## Health Check Flow

### Simple Health Check

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant HealthRouter
    participant Database

    Client->>FastAPI: GET /health
    FastAPI->>HealthRouter: Route to health_check()
    HealthRouter->>Database: Execute "SELECT 1"
    
    alt Database Available
        Database-->>HealthRouter: Success result
        HealthRouter-->>FastAPI: 200 OK<br/>{"status": "healthy", ...}
    else Database Error
        Database-->>HealthRouter: Connection error
        HealthRouter-->>FastAPI: 503 Service Unavailable<br/>{"error": "Database connection failed"}
    end
    
    FastAPI-->>Client: Health status response
```

## Search Operations Flow

### Customer Search by Email

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant CustomerRouter
    participant CustomerRepository
    participant Database

    Client->>FastAPI: GET /customers/search/by-email/{email}
    FastAPI->>CustomerRouter: Route to search_customers_by_email()
    CustomerRouter->>CustomerRepository: search_by_email(email, skip, limit)
    CustomerRepository->>Database: SELECT * FROM customers<br/>WHERE email ILIKE '%{email}%'<br/>LIMIT {limit} OFFSET {skip}
    Database-->>CustomerRepository: List of matching customers
    CustomerRepository-->>CustomerRouter: Customer objects list
    CustomerRouter->>CustomerRouter: Serialize each customer
    CustomerRouter-->>FastAPI: 200 OK + List of customers
    FastAPI-->>Client: JSON array of customers
```

## Pagination Flow

### List Operations with Pagination

```mermaid
graph TD
    REQUEST[GET /customers?skip=20&limit=10] --> VALIDATE[Validate Query Parameters]
    VALIDATE --> REPOSITORY[CustomerRepository.get_all]
    REPOSITORY --> SQL[SELECT * FROM customers<br/>OFFSET 20 LIMIT 10]
    SQL --> RESULTS[Database Results]
    RESULTS --> SERIALIZE[Serialize Each Customer]
    SERIALIZE --> RESPONSE[JSON Array Response]
```

## Transaction Management

### Database Transaction Flow

```mermaid
graph TD
    START[Start Request Processing] --> SESSION[Get Database Session]
    SESSION --> BEGIN[Begin Transaction]
    BEGIN --> OPERATION[Perform Database Operation]
    
    OPERATION --> SUCCESS{Operation Success?}
    SUCCESS -->|Yes| FLUSH[session.flush]
    SUCCESS -->|No| ERROR[Handle Error]
    
    FLUSH --> REFRESH[session.refresh]
    REFRESH --> COMMIT[session.commit]
    COMMIT --> CLEANUP[Close Session]
    
    ERROR --> ROLLBACK[session.rollback]
    ROLLBACK --> CLEANUP
    
    CLEANUP --> RESPONSE[Return Response]
```

This comprehensive flow documentation shows exactly how requests are processed through each layer of the Flight Claim System, from HTTP entry to database operations and back to the client response.