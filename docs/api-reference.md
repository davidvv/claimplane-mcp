# API Reference Documentation

## Flight Claim System API - Complete Endpoint Reference

This document provides comprehensive documentation for all API endpoints in the Flight Claim System, including request/response schemas, validation rules, status codes, and practical examples.

## API Overview

- **Base URL**: `http://localhost` (Docker) or `http://localhost:8000` (direct)
- **Content Type**: `application/json`
- **Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- **API Version**: v0.2.0 (Phase 2 Complete)

## Authentication

### Customer Endpoints

Currently, customer endpoints do not require authentication. All customer-facing endpoints (`/customers`, `/claims`, `/files`) are publicly accessible for development purposes.

### Admin Endpoints (Phase 1)

Admin endpoints (`/admin/claims/*`, `/admin/files/*`) require authentication via the `X-Admin-ID` header:

**Header Format**:
```
X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000
```

All admin endpoints will return `401 Unauthorized` if this header is missing or invalid.

**Production Roadmap**:
Phase 3 will implement proper authentication:
- JWT token-based authentication
- Role-based access control (RBAC)
- OAuth2 integration
- API Key authentication

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

---

## Email Notifications (Phase 2)

The system automatically sends email notifications to customers when certain events occur. Email notifications are processed asynchronously via Celery task queue.

### Automatic Email Triggers

| Event | Endpoint | Email Type | Details |
|-------|----------|------------|---------|
| Claim Submitted | `POST /claims` or `POST /claims/submit` | Claim Submitted | Sent immediately after claim creation |
| Status Updated | `PUT /admin/claims/{claim_id}/status` | Status Update | Sent when admin changes claim status (approved, rejected, etc.) |
| Document Rejected | `PUT /admin/files/{file_id}/review` | Document Rejected | Sent when admin rejects a document with reason |

### Email Templates

All emails use professional HTML templates with flight claim branding:
- **Claim Submitted**: Confirmation with claim ID and flight details
- **Status Update**: Dynamic color-coded email based on status (green=approved, red=rejected, blue=in progress)
- **Document Rejected**: Orange warning with rejection reason and tips for re-upload

### Configuration

Email notifications can be disabled via environment variable:
```bash
NOTIFICATIONS_ENABLED=false  # Set to disable email notifications
```

SMTP settings are configured in docker-compose.yml and app/config.py.

---

## Admin - Claims Management

All admin claim endpoints require the `X-Admin-ID` header for authentication.

### List Claims

**Endpoint**: `GET /admin/claims`

**Description**: List all claims with advanced filtering, sorting, and pagination. Supports search across multiple fields.

**Headers**:
```
X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000
```

**Query Parameters**:
- `skip` (integer, optional): Records to skip (default: 0)
- `limit` (integer, optional): Maximum records (default: 100, max: 1000)
- `status` (string, optional): Filter by claim status
- `airline` (string, optional): Filter by airline name
- `incident_type` (string, optional): Filter by incident type
- `assigned_to` (UUID, optional): Filter by assigned admin
- `date_from` (ISO date, optional): Filter claims from date
- `date_to` (ISO date, optional): Filter claims to date
- `search` (string, optional): Search customer name, email, flight number
- `sort_by` (string, optional): Sort field (default: `submitted_at`)
- `sort_order` (string, optional): `asc` or `desc` (default: `desc`)

**Success Response** (200 OK):
```json
{
  "claims": [
    {
      "id": "770f8400-e29b-41d4-a716-446655440001",
      "customerId": "550e8400-e29b-41d4-a716-446655440000",
      "customerName": "John Doe",
      "customerEmail": "john@example.com",
      "flightNumber": "AA123",
      "airline": "American Airlines",
      "departureAirport": "JFK",
      "arrivalAirport": "LAX",
      "incidentType": "delay",
      "status": "under_review",
      "assignedTo": "660f9511-f30c-52e5-b827-557766551111",
      "calculatedCompensation": 600.00,
      "submittedAt": "2024-01-15T16:00:00Z"
    }
  ],
  "total": 145,
  "skip": 0,
  "limit": 100
}
```

**cURL Example**:
```bash
# List all claims
curl "http://localhost/admin/claims" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"

# Filter by status and airline
curl "http://localhost/admin/claims?status=under_review&airline=American%20Airlines" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"

# Search with date range
curl "http://localhost/admin/claims?search=john&date_from=2024-01-01&date_to=2024-01-31" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### Get Claim Detail

**Endpoint**: `GET /admin/claims/{claim_id}`

**Description**: Get comprehensive claim information including customer details, files, notes, and status history.

**Path Parameters**:
- `claim_id` (UUID, required): Claim's unique identifier

**Success Response** (200 OK):
```json
{
  "id": "770f8400-e29b-41d4-a716-446655440001",
  "customer": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "phone": "+1234567890"
  },
  "flightNumber": "AA123",
  "airline": "American Airlines",
  "departureDate": "2024-02-15",
  "departureAirport": "JFK",
  "arrivalAirport": "LAX",
  "incidentType": "delay",
  "status": "under_review",
  "assignedTo": "660f9511-f30c-52e5-b827-557766551111",
  "calculatedCompensation": 600.00,
  "currency": "EUR",
  "files": [
    {
      "id": "880f8400-e29b-41d4-a716-446655440002",
      "documentType": "boarding_pass",
      "fileName": "boarding_pass.pdf",
      "fileSize": 245678,
      "status": "approved",
      "uploadedAt": "2024-01-15T16:30:00Z"
    }
  ],
  "notes": [
    {
      "id": "990f8400-e29b-41d4-a716-446655440003",
      "noteText": "Customer provided all required documents",
      "isInternal": true,
      "authorId": "660f9511-f30c-52e5-b827-557766551111",
      "createdAt": "2024-01-16T10:00:00Z"
    }
  ],
  "statusHistory": [
    {
      "id": "aa0f8400-e29b-41d4-a716-446655440004",
      "previousStatus": "submitted",
      "newStatus": "under_review",
      "changedBy": "660f9511-f30c-52e5-b827-557766551111",
      "changeReason": "Starting review process",
      "changedAt": "2024-01-16T09:00:00Z"
    }
  ],
  "submittedAt": "2024-01-15T16:00:00Z",
  "updatedAt": "2024-01-16T10:00:00Z"
}
```

**cURL Example**:
```bash
curl "http://localhost/admin/claims/770f8400-e29b-41d4-a716-446655440001" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### Update Claim Status

**Endpoint**: `PUT /admin/claims/{claim_id}/status`

**Description**: Update claim status with workflow validation and audit trail. Automatically sends email notification to customer.

**Path Parameters**:
- `claim_id` (UUID, required): Claim's unique identifier

**Request Schema**:
```json
{
  "new_status": "approved",
  "change_reason": "All documents verified, compensation approved"
}
```

**Valid Status Values**:
- `draft`, `submitted`, `under_review`, `documents_requested`, `approved`, `rejected`, `paid`, `closed`

**Valid Status Transitions**:
The system enforces valid workflow transitions. Use `GET /admin/claims/{claim_id}/status-transitions` to see valid next statuses.

**Success Response** (200 OK):
Returns full claim detail (same as GET /admin/claims/{claim_id})

**Email Notification**:
Automatically sends status update email to customer with:
- Old and new status
- Change reason
- Compensation amount (if approved)
- Flight details

**cURL Example**:
```bash
curl -X PUT "http://localhost/admin/claims/770f8400-e29b-41d4-a716-446655440001/status" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "approved",
    "change_reason": "All documents verified"
  }'
```

---

### Assign Claim

**Endpoint**: `PUT /admin/claims/{claim_id}/assign`

**Description**: Assign claim to a specific admin reviewer.

**Request Schema**:
```json
{
  "assigned_to": "660f9511-f30c-52e5-b827-557766551111"
}
```

**cURL Example**:
```bash
curl -X PUT "http://localhost/admin/claims/770f8400-e29b-41d4-a716-446655440001/assign" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "assigned_to": "660f9511-f30c-52e5-b827-557766551111"
  }'
```

---

### Set Compensation

**Endpoint**: `PUT /admin/claims/{claim_id}/compensation`

**Description**: Manually set or update compensation amount for a claim.

**Request Schema**:
```json
{
  "compensation_amount": 600.00,
  "reason": "EU261/2004 calculation for 3000+ km delay"
}
```

**cURL Example**:
```bash
curl -X PUT "http://localhost/admin/claims/770f8400-e29b-41d4-a716-446655440001/compensation" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "compensation_amount": 600.00,
    "reason": "EU261/2004 calculation for 3000+ km delay"
  }'
```

---

### Add Claim Note

**Endpoint**: `POST /admin/claims/{claim_id}/notes`

**Description**: Add internal or customer-facing note to a claim.

**Request Schema**:
```json
{
  "note_text": "Customer called to inquire about status. Explained review timeline.",
  "is_internal": true
}
```

**Field Details**:
- `is_internal`: `true` = visible only to admins, `false` = visible to customer

**Success Response** (201 Created):
```json
{
  "id": "990f8400-e29b-41d4-a716-446655440003",
  "claimId": "770f8400-e29b-41d4-a716-446655440001",
  "authorId": "660f9511-f30c-52e5-b827-557766551111",
  "noteText": "Customer called to inquire about status",
  "isInternal": true,
  "createdAt": "2024-01-16T10:00:00Z"
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost/admin/claims/770f8400-e29b-41d4-a716-446655440001/notes" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "note_text": "Customer called to inquire about status",
    "is_internal": true
  }'
```

---

### Get Claim Notes

**Endpoint**: `GET /admin/claims/{claim_id}/notes`

**Description**: Retrieve all notes for a claim.

**Query Parameters**:
- `include_internal` (boolean, optional): Include internal notes (default: true)

**cURL Example**:
```bash
curl "http://localhost/admin/claims/770f8400-e29b-41d4-a716-446655440001/notes?include_internal=true" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### Get Status History

**Endpoint**: `GET /admin/claims/{claim_id}/history`

**Description**: Get complete audit trail of status changes for a claim.

**Success Response** (200 OK):
```json
[
  {
    "id": "aa0f8400-e29b-41d4-a716-446655440004",
    "claimId": "770f8400-e29b-41d4-a716-446655440001",
    "previousStatus": "submitted",
    "newStatus": "under_review",
    "changedBy": "660f9511-f30c-52e5-b827-557766551111",
    "changeReason": "Starting review process",
    "changedAt": "2024-01-16T09:00:00Z"
  },
  {
    "id": "bb0f8400-e29b-41d4-a716-446655440005",
    "claimId": "770f8400-e29b-41d4-a716-446655440001",
    "previousStatus": "under_review",
    "newStatus": "approved",
    "changedBy": "660f9511-f30c-52e5-b827-557766551111",
    "changeReason": "All documents verified",
    "changedAt": "2024-01-17T14:30:00Z"
  }
]
```

**cURL Example**:
```bash
curl "http://localhost/admin/claims/770f8400-e29b-41d4-a716-446655440001/history" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### Bulk Actions

**Endpoint**: `POST /admin/claims/bulk-action`

**Description**: Perform bulk operations on multiple claims simultaneously.

**Supported Actions**:
- `status_update`: Update status for multiple claims
- `assign`: Assign multiple claims to a reviewer

**Request Schema (Status Update)**:
```json
{
  "claim_ids": [
    "770f8400-e29b-41d4-a716-446655440001",
    "880f8400-e29b-41d4-a716-446655440002"
  ],
  "action": "status_update",
  "parameters": {
    "new_status": "under_review",
    "change_reason": "Batch processing started"
  }
}
```

**Request Schema (Bulk Assign)**:
```json
{
  "claim_ids": [
    "770f8400-e29b-41d4-a716-446655440001",
    "880f8400-e29b-41d4-a716-446655440002"
  ],
  "action": "assign",
  "parameters": {
    "assigned_to": "660f9511-f30c-52e5-b827-557766551111"
  }
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "affected_count": 2,
  "message": "Successfully performed status_update on 2 claims",
  "errors": []
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost/admin/claims/bulk-action" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_ids": ["770f8400-e29b-41d4-a716-446655440001"],
    "action": "status_update",
    "parameters": {
      "new_status": "under_review",
      "change_reason": "Batch processing"
    }
  }'
```

---

### Analytics Summary

**Endpoint**: `GET /admin/claims/analytics/summary`

**Description**: Get dashboard analytics including claim counts by status, compensation totals, and trends.

**Success Response** (200 OK):
```json
{
  "total_claims": 245,
  "claims_by_status": {
    "submitted": 45,
    "under_review": 32,
    "approved": 89,
    "rejected": 23,
    "paid": 56
  },
  "total_compensation_approved": 145600.00,
  "total_compensation_paid": 98200.00,
  "average_processing_time_days": 7.3,
  "claims_by_incident_type": {
    "delay": 120,
    "cancellation": 85,
    "denied_boarding": 25,
    "baggage_delay": 15
  }
}
```

**cURL Example**:
```bash
curl "http://localhost/admin/claims/analytics/summary" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### Calculate Compensation

**Endpoint**: `POST /admin/claims/calculate-compensation`

**Description**: Calculate EU261/2004 compensation for a hypothetical claim (reference tool).

**Request Schema**:
```json
{
  "departure_airport": "JFK",
  "arrival_airport": "LAX",
  "delay_hours": 4.5,
  "incident_type": "delay",
  "extraordinary_circumstances": false
}
```

**Success Response** (200 OK):
```json
{
  "eligible": true,
  "compensation_amount": 600.00,
  "currency": "EUR",
  "distance_km": 3974,
  "distance_category": "long",
  "regulation": "EU261/2004",
  "reason": "Flight delay over 3 hours for long-haul flight"
}
```

**Distance Categories**:
- Short: < 1500 km → €250
- Medium: 1500-3500 km → €400
- Long: > 3500 km → €600

**cURL Example**:
```bash
curl -X POST "http://localhost/admin/claims/calculate-compensation" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "departure_airport": "JFK",
    "arrival_airport": "LAX",
    "delay_hours": 4.5,
    "incident_type": "delay",
    "extraordinary_circumstances": false
  }'
```

---

### Get Valid Status Transitions

**Endpoint**: `GET /admin/claims/{claim_id}/status-transitions`

**Description**: Get valid next statuses for a claim based on current status and workflow rules.

**Success Response** (200 OK):
```json
{
  "current_status": "under_review",
  "valid_next_statuses": ["documents_requested", "approved", "rejected"],
  "status_info": {
    "display_name": "Under Review",
    "description": "Claim is being processed by admin team",
    "color": "blue"
  }
}
```

**cURL Example**:
```bash
curl "http://localhost/admin/claims/770f8400-e29b-41d4-a716-446655440001/status-transitions" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

## Admin - File Management

All admin file endpoints require the `X-Admin-ID` header for authentication.

### List Claim Documents

**Endpoint**: `GET /admin/files/claim/{claim_id}/documents`

**Description**: List all documents/files associated with a specific claim.

**Path Parameters**:
- `claim_id` (UUID, required): Claim's unique identifier

**Success Response** (200 OK):
```json
[
  {
    "id": "880f8400-e29b-41d4-a716-446655440002",
    "claimId": "770f8400-e29b-41d4-a716-446655440001",
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "documentType": "boarding_pass",
    "fileName": "boarding_pass.pdf",
    "mimeType": "application/pdf",
    "fileSize": 245678,
    "status": "approved",
    "validationStatus": "approved",
    "rejectionReason": null,
    "reviewedBy": "660f9511-f30c-52e5-b827-557766551111",
    "reviewedAt": "2024-01-16T11:00:00Z",
    "uploadedAt": "2024-01-15T16:30:00Z"
  },
  {
    "id": "990f8400-e29b-41d4-a716-446655440003",
    "claimId": "770f8400-e29b-41d4-a716-446655440001",
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "documentType": "id_document",
    "fileName": "passport.jpg",
    "mimeType": "image/jpeg",
    "fileSize": 512340,
    "status": "uploaded",
    "validationStatus": "pending",
    "rejectionReason": null,
    "reviewedBy": null,
    "reviewedAt": null,
    "uploadedAt": "2024-01-15T16:35:00Z"
  }
]
```

**cURL Example**:
```bash
curl "http://localhost/admin/files/claim/770f8400-e29b-41d4-a716-446655440001/documents" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### Get File Metadata

**Endpoint**: `GET /admin/files/{file_id}/metadata`

**Description**: Get detailed metadata for a file including security scan results and access logs.

**Path Parameters**:
- `file_id` (UUID, required): File's unique identifier

**Success Response** (200 OK):
```json
{
  "id": "880f8400-e29b-41d4-a716-446655440002",
  "claimId": "770f8400-e29b-41d4-a716-446655440001",
  "customerId": "550e8400-e29b-41d4-a716-446655440000",
  "documentType": "boarding_pass",
  "fileName": "boarding_pass.pdf",
  "originalFileName": "My_Boarding_Pass_2024.pdf",
  "mimeType": "application/pdf",
  "fileSize": 245678,
  "status": "approved",
  "validationStatus": "approved",
  "rejectionReason": null,
  "securityScanned": true,
  "virusScanResult": "clean",
  "contentHash": "sha256:a1b2c3d4e5f6...",
  "encryptionStatus": "encrypted",
  "reviewedBy": "660f9511-f30c-52e5-b827-557766551111",
  "reviewedAt": "2024-01-16T11:00:00Z",
  "uploadedAt": "2024-01-15T16:30:00Z",
  "expiresAt": null
}
```

**cURL Example**:
```bash
curl "http://localhost/admin/files/880f8400-e29b-41d4-a716-446655440002/metadata" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### Review File (Approve/Reject)

**Endpoint**: `PUT /admin/files/{file_id}/review`

**Description**: Approve or reject a document. Automatically sends email notification if rejected.

**Path Parameters**:
- `file_id` (UUID, required): File's unique identifier

**Request Schema (Approve)**:
```json
{
  "approved": true
}
```

**Request Schema (Reject)**:
```json
{
  "approved": false,
  "rejection_reason": "Document is not legible. Please upload a clearer image."
}
```

**Success Response** (200 OK):
Returns file metadata (same as GET /admin/files/{file_id}/metadata)

**Email Notification**:
When `approved: false`, automatically sends document rejected email to customer with:
- Document type
- Rejection reason
- Tips for re-uploading
- Flight and claim details

**cURL Example**:
```bash
# Approve document
curl -X PUT "http://localhost/admin/files/880f8400-e29b-41d4-a716-446655440002/review" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'

# Reject document
curl -X PUT "http://localhost/admin/files/880f8400-e29b-41d4-a716-446655440002/review" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "approved": false,
    "rejection_reason": "Document is not legible"
  }'
```

---

### Request File Re-upload

**Endpoint**: `POST /admin/files/{file_id}/request-reupload`

**Description**: Request customer to re-upload a document with a specific deadline.

**Path Parameters**:
- `file_id` (UUID, required): File's unique identifier

**Request Schema**:
```json
{
  "reason": "Document quality is too low. Please upload a higher resolution image.",
  "deadline_days": 7
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Re-upload request created successfully",
  "file_id": "880f8400-e29b-41d4-a716-446655440002",
  "deadline": "2024-01-22T16:30:00Z",
  "reason": "Document quality is too low"
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost/admin/files/880f8400-e29b-41d4-a716-446655440002/request-reupload" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Document quality is too low",
    "deadline_days": 7
  }'
```

---

### Get Pending Review Files

**Endpoint**: `GET /admin/files/pending-review`

**Description**: Get all files awaiting admin review (uploaded but not yet reviewed).

**Success Response** (200 OK):
Returns array of files (same format as List Claim Documents)

**cURL Example**:
```bash
curl "http://localhost/admin/files/pending-review" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### Get Files by Document Type

**Endpoint**: `GET /admin/files/by-document-type/{document_type}`

**Description**: Get all files of a specific document type (useful for batch reviewing).

**Path Parameters**:
- `document_type` (string, required): Document type to filter

**Valid Document Types**:
- `boarding_pass`
- `id_document`
- `receipt`
- `bank_statement`
- `flight_ticket`
- `delay_certificate`
- `cancellation_notice`
- `other`

**cURL Example**:
```bash
curl "http://localhost/admin/files/by-document-type/boarding_pass" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### File Statistics

**Endpoint**: `GET /admin/files/statistics`

**Description**: Get comprehensive statistics about files in the system.

**Success Response** (200 OK):
```json
{
  "status_counts": {
    "uploaded": 45,
    "validated": 12,
    "approved": 189,
    "rejected": 23
  },
  "document_type_counts": {
    "boarding_pass": 220,
    "id_document": 215,
    "flight_ticket": 180,
    "receipt": 95
  },
  "validation_status_counts": {
    "pending": 45,
    "approved": 189,
    "rejected": 23
  },
  "total_size_bytes": 524288000,
  "total_size_mb": 500.00,
  "pending_review_count": 45
}
```

**cURL Example**:
```bash
curl "http://localhost/admin/files/statistics" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### Delete File

**Endpoint**: `DELETE /admin/files/{file_id}`

**Description**: Soft delete a file (marks as deleted, doesn't physically remove).

**Path Parameters**:
- `file_id` (UUID, required): File's unique identifier

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "File 880f8400-e29b-41d4-a716-446655440002 marked as deleted",
  "deleted_at": "2024-01-17T10:00:00Z"
}
```

**cURL Example**:
```bash
curl -X DELETE "http://localhost/admin/files/880f8400-e29b-41d4-a716-446655440002" \
  -H "X-Admin-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

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