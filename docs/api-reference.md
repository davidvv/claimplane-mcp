# API Reference Documentation

## Flight Claim System API - Complete Endpoint Reference

This document provides comprehensive documentation for all API endpoints in the Flight Claim System, including request/response schemas, validation rules, status codes, and practical examples.

## API Overview

- **Base URL**: `http://localhost` (Docker) or `http://localhost:8000` (direct)
- **Content Type**: `application/json`
- **Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- **API Version**: 1.0.0

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible for development purposes. In production, consider implementing:
- API Key authentication
- JWT token-based authentication
- OAuth2 integration

## Response Format

All API responses follow a consistent structure:

### Success Response
```json
{
  "id": "uuid",
  "field": "value",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_TYPE",
    "message": "Human-readable error message",
    "details": ["Specific error details"]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Customer Endpoints

### Create Customer

**Endpoint**: `POST /customers`

**Description**: Creates a new customer with profile information.

**Request Schema**:
```json
{
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "phone": "+1234567890",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "postalCode": "10001",
    "country": "USA"
  }
}
```

**Field Validations**:
- `email`: Valid email format, unique across system
- `firstName`: Required, max 50 characters
- `lastName`: Required, max 50 characters  
- `phone`: Optional, max 20 characters
- `address`: Optional nested object

**Success Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "phone": "+1234567890",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "postalCode": "10001",
    "country": "USA"
  },
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Email already exists
- `422 Unprocessable Entity`: Validation errors

**cURL Example**:
```bash
curl -X POST "http://localhost/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "phone": "+1234567890",
    "address": {
      "street": "123 Main St",
      "city": "New York",
      "postalCode": "10001",
      "country": "USA"
    }
  }'
```

---

### Get Customer by ID

**Endpoint**: `GET /customers/{customer_id}`

**Description**: Retrieves a specific customer by their unique identifier.

**Path Parameters**:
- `customer_id` (UUID, required): Customer's unique identifier

**Success Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "phone": "+1234567890",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "postalCode": "10001",
    "country": "USA"
  },
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Customer does not exist

**cURL Example**:
```bash
curl "http://localhost/customers/550e8400-e29b-41d4-a716-446655440000"
```

---

### List Customers

**Endpoint**: `GET /customers`

**Description**: Retrieves a paginated list of all customers.

**Query Parameters**:
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (default: 100, max: 100)

**Success Response** (200 OK):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user1@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "phone": "+1234567890",
    "address": {
      "street": "123 Main St",
      "city": "New York",
      "postalCode": "10001",
      "country": "USA"
    },
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z"
  },
  {
    "id": "660f9511-f30c-52e5-b827-557766551111",
    "email": "user2@example.com",
    "firstName": "Jane",
    "lastName": "Smith",
    "phone": null,
    "address": null,
    "createdAt": "2024-01-15T11:15:00Z",
    "updatedAt": "2024-01-15T11:15:00Z"
  }
]
```

**cURL Example**:
```bash
# Get first 10 customers
curl "http://localhost/customers?skip=0&limit=10"

# Get next 10 customers  
curl "http://localhost/customers?skip=10&limit=10"
```

---

### Update Customer (Complete)

**Endpoint**: `PUT /customers/{customer_id}`

**Description**: Completely updates a customer. All fields are required and any omitted fields will be set to null.

**Path Parameters**:
- `customer_id` (UUID, required): Customer's unique identifier

**Request Schema**:
```json
{
  "email": "updated@example.com",
  "firstName": "Updated",
  "lastName": "Name",
  "phone": "+9876543210",
  "address": {
    "street": "456 Oak Ave",
    "city": "Los Angeles", 
    "postalCode": "90210",
    "country": "USA"
  }
}
```

**Field Requirements**:
- All fields from create schema are required
- Email must be unique (can be same as current)
- Address can be null to remove address information

**Success Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "updated@example.com",
  "firstName": "Updated",
  "lastName": "Name", 
  "phone": "+9876543210",
  "address": {
    "street": "456 Oak Ave",
    "city": "Los Angeles",
    "postalCode": "90210", 
    "country": "USA"
  },
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T14:45:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Email already exists for another customer
- `404 Not Found`: Customer does not exist
- `422 Unprocessable Entity`: Validation errors

**cURL Example**:
```bash
curl -X PUT "http://localhost/customers/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "updated@example.com",
    "firstName": "Updated",
    "lastName": "Name",
    "phone": "+9876543210",
    "address": {
      "street": "456 Oak Ave",
      "city": "Los Angeles",
      "postalCode": "90210",
      "country": "USA"
    }
  }'
```

---

### Update Customer (Partial)

**Endpoint**: `PATCH /customers/{customer_id}`

**Description**: Partially updates a customer. Only provided fields are updated, existing values are preserved for omitted fields.

**Path Parameters**:
- `customer_id` (UUID, required): Customer's unique identifier

**Request Schema** (all fields optional):
```json
{
  "email": "newemail@example.com",
  "firstName": "NewFirst",
  "phone": "+1111111111"
}
```

**Field Behavior**:
- Only provided fields are updated
- `null` values are ignored (field remains unchanged)
- Empty strings `""` are converted to `null` and ignored
- Existing values preserved for omitted fields

**Success Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newemail@example.com",
  "firstName": "NewFirst",
  "lastName": "Doe",
  "phone": "+1111111111",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "postalCode": "10001",
    "country": "USA"
  },
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T15:20:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Email already exists for another customer
- `404 Not Found`: Customer does not exist
- `422 Unprocessable Entity`: Validation errors

**cURL Examples**:
```bash
# Update only email
curl -X PATCH "http://localhost/customers/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"email": "newemail@example.com"}'

# Update multiple fields
curl -X PATCH "http://localhost/customers/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "NewFirst",
    "phone": "+1111111111",
    "address": {
      "street": "789 New Street",
      "city": "Chicago",
      "postalCode": "60601",
      "country": "USA"
    }
  }'
```

---

### Search Customers

**Endpoint**: `GET /customers/search/by-email/{email}`

**Description**: Searches customers by email address (partial matching).

**Path Parameters**:
- `email` (string, required): Email search term

**Query Parameters**:
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (default: 100)

**Success Response** (200 OK):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "phone": "+1234567890",
    "address": null,
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z"
  }
]
```

**cURL Example**:
```bash
curl "http://localhost/customers/search/by-email/john"
```

---

**Endpoint**: `GET /customers/search/by-name/{name}`

**Description**: Searches customers by first or last name (partial matching).

**Path Parameters**:
- `name` (string, required): Name search term

**cURL Example**:
```bash
curl "http://localhost/customers/search/by-name/doe"
```

## Claim Endpoints

### Create Claim

**Endpoint**: `POST /claims`

**Description**: Creates a new claim for an existing customer.

**Request Schema**:
```json
{
  "customerId": "550e8400-e29b-41d4-a716-446655440000",
  "flightInfo": {
    "flightNumber": "AA123",
    "airline": "American Airlines",
    "departureDate": "2024-02-15",
    "departureAirport": "JFK",
    "arrivalAirport": "LAX"
  },
  "incidentType": "delay",
  "notes": "Flight was delayed by 4 hours due to weather conditions"
}
```

**Field Validations**:
- `customerId`: Must reference existing customer
- `flightNumber`: 3-10 characters, must contain digits
- `departureAirport`/`arrivalAirport`: Exactly 3 characters (IATA codes)
- `incidentType`: Must be one of: `delay`, `cancellation`, `denied_boarding`, `baggage_delay`
- `notes`: Optional text field

**Success Response** (201 Created):
```json
{
  "id": "770f8400-e29b-41d4-a716-446655440001",
  "customerId": "550e8400-e29b-41d4-a716-446655440000",
  "flightNumber": "AA123",
  "airline": "American Airlines",
  "departureDate": "2024-02-15",
  "departureAirport": "JFK",
  "arrivalAirport": "LAX",
  "incidentType": "delay",
  "status": "submitted",
  "compensationAmount": null,
  "currency": "EUR",
  "notes": "Flight was delayed by 4 hours due to weather conditions",
  "submittedAt": "2024-01-15T16:00:00Z",
  "updatedAt": "2024-01-15T16:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Customer does not exist
- `422 Unprocessable Entity`: Validation errors

**cURL Example**:
```bash
curl -X POST "http://localhost/claims" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightInfo": {
      "flightNumber": "AA123",
      "airline": "American Airlines", 
      "departureDate": "2024-02-15",
      "departureAirport": "JFK",
      "arrivalAirport": "LAX"
    },
    "incidentType": "delay",
    "notes": "Flight was delayed by 4 hours due to weather conditions"
  }'
```

---

### Submit Claim with Customer Info

**Endpoint**: `POST /claims/submit`

**Description**: Creates a claim and customer in one request. Creates customer if they don't exist by email.

**Request Schema**:
```json
{
  "customerInfo": {
    "email": "passenger@example.com",
    "firstName": "Jane",
    "lastName": "Smith",
    "phone": "+1234567890",
    "address": {
      "street": "789 Pine St",
      "city": "Miami",
      "postalCode": "33101",
      "country": "USA"
    }
  },
  "flightInfo": {
    "flightNumber": "UA456",
    "airline": "United Airlines",
    "departureDate": "2024-03-10",
    "departureAirport": "MIA",
    "arrivalAirport": "ORD"
  },
  "incidentType": "cancellation",
  "notes": "Flight was cancelled with less than 2 hours notice"
}
```

**Behavior**:
- If customer exists by email: Uses existing customer
- If customer doesn't exist: Creates new customer
- Then creates claim for the customer

**Success Response** (201 Created):
```json
{
  "id": "880f8400-e29b-41d4-a716-446655440002",
  "customerId": "660f9511-f30c-52e5-b827-557766551111",
  "flightNumber": "UA456",
  "airline": "United Airlines",
  "departureDate": "2024-03-10", 
  "departureAirport": "MIA",
  "arrivalAirport": "ORD",
  "incidentType": "cancellation",
  "status": "submitted",
  "compensationAmount": null,
  "currency": "EUR",
  "notes": "Flight was cancelled with less than 2 hours notice",
  "submittedAt": "2024-01-15T17:30:00Z",
  "updatedAt": "2024-01-15T17:30:00Z"
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost/claims/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "customerInfo": {
      "email": "passenger@example.com",
      "firstName": "Jane",
      "lastName": "Smith",
      "phone": "+1234567890"
    },
    "flightInfo": {
      "flightNumber": "UA456",
      "airline": "United Airlines",
      "departureDate": "2024-03-10",
      "departureAirport": "MIA", 
      "arrivalAirport": "ORD"
    },
    "incidentType": "cancellation",
    "notes": "Flight was cancelled with less than 2 hours notice"
  }'
```

---

### Get Claim by ID

**Endpoint**: `GET /claims/{claim_id}`

**Description**: Retrieves a specific claim by its unique identifier.

**Path Parameters**:
- `claim_id` (UUID, required): Claim's unique identifier

**Success Response** (200 OK):
```json
{
  "id": "770f8400-e29b-41d4-a716-446655440001",
  "customerId": "550e8400-e29b-41d4-a716-446655440000",
  "flightNumber": "AA123",
  "airline": "American Airlines",
  "departureDate": "2024-02-15",
  "departureAirport": "JFK",
  "arrivalAirport": "LAX",
  "incidentType": "delay",
  "status": "submitted",
  "compensationAmount": null,
  "currency": "EUR",
  "notes": "Flight was delayed by 4 hours due to weather conditions",
  "submittedAt": "2024-01-15T16:00:00Z",
  "updatedAt": "2024-01-15T16:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Claim does not exist

**cURL Example**:
```bash
curl "http://localhost/claims/770f8400-e29b-41d4-a716-446655440001"
```

---

### List Claims

**Endpoint**: `GET /claims`

**Description**: Retrieves a paginated list of claims with optional filtering.

**Query Parameters**:
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (default: 100)
- `status` (string, optional): Filter by claim status
- `customer_id` (UUID, optional): Filter by customer ID

**Success Response** (200 OK):
```json
[
  {
    "id": "770f8400-e29b-41d4-a716-446655440001",
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightNumber": "AA123",
    "airline": "American Airlines",
    "departureDate": "2024-02-15",
    "departureAirport": "JFK",
    "arrivalAirport": "LAX",
    "incidentType": "delay",
    "status": "submitted",
    "compensationAmount": null,
    "currency": "EUR",
    "notes": "Flight was delayed by 4 hours",
    "submittedAt": "2024-01-15T16:00:00Z",
    "updatedAt": "2024-01-15T16:00:00Z"
  }
]
```

**cURL Examples**:
```bash
# Get all claims
curl "http://localhost/claims"

# Get claims by status
curl "http://localhost/claims?status=submitted"

# Get claims for specific customer
curl "http://localhost/claims?customer_id=550e8400-e29b-41d4-a716-446655440000"

# Combined filtering with pagination
curl "http://localhost/claims?status=approved&skip=0&limit=20"
```

---

### Get Customer Claims

**Endpoint**: `GET /claims/customer/{customer_id}`

**Description**: Retrieves all claims for a specific customer.

**Path Parameters**:
- `customer_id` (UUID, required): Customer's unique identifier

**Query Parameters**:
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (default: 100)

**Success Response** (200 OK):
```json
[
  {
    "id": "770f8400-e29b-41d4-a716-446655440001",
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightNumber": "AA123",
    "airline": "American Airlines",
    "departureDate": "2024-02-15",
    "departureAirport": "JFK", 
    "arrivalAirport": "LAX",
    "incidentType": "delay",
    "status": "submitted",
    "compensationAmount": null,
    "currency": "EUR",
    "notes": "Flight was delayed by 4 hours",
    "submittedAt": "2024-01-15T16:00:00Z",
    "updatedAt": "2024-01-15T16:00:00Z"
  }
]
```

**Error Responses**:
- `404 Not Found`: Customer does not exist

**cURL Example**:
```bash
curl "http://localhost/claims/customer/550e8400-e29b-41d4-a716-446655440000"
```

---

### Update Claim (Complete)

**Endpoint**: `PUT /claims/{claim_id}`

**Description**: Completely updates a claim. All fields are required.

**Path Parameters**:
- `claim_id` (UUID, required): Claim's unique identifier

**Request Schema**:
```json
{
  "customerId": "550e8400-e29b-41d4-a716-446655440000",
  "flightInfo": {
    "flightNumber": "AA123",
    "airline": "American Airlines",
    "departureDate": "2024-02-15",
    "departureAirport": "JFK",
    "arrivalAirport": "LAX"
  },
  "incidentType": "delay",
  "notes": "Updated flight delay information"
}
```

**Success Response** (200 OK):
```json
{
  "id": "770f8400-e29b-41d4-a716-446655440001",
  "customerId": "550e8400-e29b-41d4-a716-446655440000",
  "flightNumber": "AA123",
  "airline": "American Airlines",
  "departureDate": "2024-02-15",
  "departureAirport": "JFK",
  "arrivalAirport": "LAX",
  "incidentType": "delay",
  "status": "submitted",
  "compensationAmount": null,
  "currency": "EUR",
  "notes": "Updated flight delay information",
  "submittedAt": "2024-01-15T16:00:00Z",
  "updatedAt": "2024-01-15T18:45:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Claim or customer does not exist
- `422 Unprocessable Entity`: Validation errors

**cURL Example**:
```bash
curl -X PUT "http://localhost/claims/770f8400-e29b-41d4-a716-446655440001" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightInfo": {
      "flightNumber": "AA123",
      "airline": "American Airlines",
      "departureDate": "2024-02-15",
      "departureAirport": "JFK",
      "arrivalAirport": "LAX"
    },
    "incidentType": "delay", 
    "notes": "Updated flight delay information"
  }'
```

---

### Update Claim (Partial)

**Endpoint**: `PATCH /claims/{claim_id}`

**Description**: Partially updates a claim. Only provided fields are updated.

**Path Parameters**:
- `claim_id` (UUID, required): Claim's unique identifier

**Request Schema** (all fields optional):
```json
{
  "incidentType": "cancellation",
  "notes": "Flight was actually cancelled, not delayed"
}
```

**Success Response** (200 OK):
```json
{
  "id": "770f8400-e29b-41d4-a716-446655440001",
  "customerId": "550e8400-e29b-41d4-a716-446655440000",
  "flightNumber": "AA123",
  "airline": "American Airlines",
  "departureDate": "2024-02-15",
  "departureAirport": "JFK",
  "arrivalAirport": "LAX",
  "incidentType": "cancellation",
  "status": "submitted",
  "compensationAmount": null,
  "currency": "EUR",
  "notes": "Flight was actually cancelled, not delayed",
  "submittedAt": "2024-01-15T16:00:00Z",
  "updatedAt": "2024-01-15T19:15:00Z"
}
```

**cURL Example**:
```bash
curl -X PATCH "http://localhost/claims/770f8400-e29b-41d4-a716-446655440001" \
  -H "Content-Type: application/json" \
  -d '{
    "incidentType": "cancellation",
    "notes": "Flight was actually cancelled, not delayed"
  }'
```

---

### Get Claims by Status

**Endpoint**: `GET /claims/status/{status}`

**Description**: Retrieves claims filtered by status.

**Path Parameters**:
- `status` (string, required): Claim status to filter by

**Valid Status Values**:
- `draft` - Claim being prepared
- `submitted` - Claim submitted for review
- `under_review` - Being processed  
- `approved` - Claim approved for payment
- `rejected` - Claim denied
- `paid` - Compensation paid
- `closed` - Claim process completed

**Query Parameters**:
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (default: 100)

**cURL Example**:
```bash
curl "http://localhost/claims/status/submitted"
```

## Health Check Endpoints

### Basic Health Check

**Endpoint**: `GET /health`

**Description**: Basic health check with database connectivity verification.

**Success Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T20:00:00Z",
  "version": "1.0.0"
}
```

**Error Response** (503 Service Unavailable):
```json
{
  "detail": "Database connection failed: connection error details"
}
```

**cURL Example**:
```bash
curl "http://localhost/health"
```

---

### Database Health Check

**Endpoint**: `GET /health/db`

**Description**: Detailed database connectivity and information check.

**Success Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T20:00:00Z",
  "database": {
    "version": "PostgreSQL 15.3 on x86_64-pc-linux-gnu",
    "name": "flight_claim",
    "user": "postgres"
  }
}
```

**cURL Example**:
```bash
curl "http://localhost/health/db"
```

---

### Detailed Health Check

**Endpoint**: `GET /health/detailed`

**Description**: Comprehensive system health information.

**Success Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T20:00:00Z",
  "version": "1.0.0",
  "system": {
    "python_version": "3.11.6 (main, Oct  8 2023, 05:06:43) [GCC 13.2.0]",
    "platform": "linux",
    "environment": "development"
  },
  "database": {
    "status": "healthy",
    "url": "postgresql+asyncpg://***:***@db:5432/flight_claim"
  }
}
```

**cURL Example**:
```bash
curl "http://localhost/health/detailed"
```

## System Information Endpoints

### Root Endpoint

**Endpoint**: `GET /`

**Description**: Basic API information and navigation.

**Success Response** (200 OK):
```json
{
  "message": "Flight Claim System API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

**cURL Example**:
```bash
curl "http://localhost/"
```

---

### API Information

**Endpoint**: `GET /info`

**Description**: Detailed API information and features.

**Success Response** (200 OK):
```json
{
  "name": "Flight Claim System API",
  "version": "1.0.0",
  "description": "API for managing flight compensation claims",
  "environment": "development",
  "features": [
    "Customer management",
    "Claim submission and tracking",
    "Flight incident reporting", 
    "Compensation calculation"
  ]
}
```

**cURL Example**:
```bash
curl "http://localhost/info"
```

## Common HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH operations |
| 201 | Created | Successful POST operations |
| 400 | Bad Request | Business logic errors (duplicate email, etc.) |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation errors |
| 500 | Internal Server Error | Unexpected server errors |
| 503 | Service Unavailable | Database connectivity issues |

## Error Response Examples

### Validation Error (422)
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "message": "field required",
        "type": "value_error.missing"
      },
      {
        "field": "firstName",
        "message": "ensure this value has at most 50 characters",
        "type": "value_error.any_str.max_length"
      }
    ]
  },
  "timestamp": "2024-01-15T20:30:00Z"
}
```

### Duplicate Entry Error (409)
```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_ENTRY",
    "message": "A record with this information already exists",
    "details": ["duplicate key value violates unique constraint \"uq_customers_email\""]
  },
  "timestamp": "2024-01-15T20:30:00Z"
}
```

### Not Found Error (404)
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND_ERROR",
    "message": "Customer with id 550e8400-e29b-41d4-a716-446655440000 not found",
    "details": []
  },
  "timestamp": "2024-01-15T20:30:00Z"
}
```

This comprehensive API reference provides all the information needed to integrate with the Flight Claim System API effectively.