# Easy Air Claim API - Complete Documentation

## Overview

This document provides comprehensive documentation for the Easy Air Claim API, a FastAPI-based backend service that implements the OpenAPI 3.1.0 specification for handling flight delay compensation claims under EU Regulation 261/2004.

## Base URL
```
http://localhost:8000/api
```

## Authentication

The API uses JWT (JSON Web Token) based authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

**Endpoint:** `POST /api/auth/login-json`

**Request:**
```json
{
  "email": "user@example.com",
  "bookingReference": "ABC123456"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## API Endpoints

### 1. Claims Management

#### Submit Flight Details
**Endpoint:** `POST /api/flight-details`

Submit flight information for a compensation claim.

**Request Body:**
```json
{
  "flightNumber": "LH1234",
  "plannedDepartureDate": "2024-01-15",
  "actualDepartureTime": "2024-01-15T14:30:00Z"
}
```

**Response:**
```json
{
  "message": "Flight details recorded."
}
```

**Validation Rules:**
- `flightNumber`: Must match pattern `^[A-Z]{2}\d{3,4}$` (e.g., LH1234, BA4567)
- `plannedDepartureDate`: Must be in the past (for claims) and within 3 years
- `actualDepartureTime`: Optional, must be valid ISO 8601 datetime

**Error Responses:**
- `400 Bad Request`: Invalid flight number format or date validation failed
- `401 Unauthorized`: Missing or invalid authentication token

#### Submit Personal Information
**Endpoint:** `POST /api/personal-info`

Submit passenger personal information for the claim.

**Request Body:**
```json
{
  "fullName": "John Doe",
  "email": "john.doe@example.com",
  "bookingReference": "ABC123456"
}
```

**Response:**
```json
{
  "message": "Personal information recorded."
}
```

**Validation Rules:**
- `fullName`: Required, 1-255 characters
- `email`: Must be valid email format
- `bookingReference`: Minimum 6 characters, alphanumeric only

#### Upload Supporting Documents
**Endpoint:** `POST /api/upload`

Upload supporting documents for the claim.

**Request:** Multipart form data
- `boardingPass`: Required, boarding pass scan/photo (PDF, JPG, PNG, max 5MB)
- `receipt`: Optional, expense receipt (PDF, JPG, PNG, max 5MB)

**Response:**
```json
{
  "message": "Files uploaded."
}
```

**File Requirements:**
- Maximum file size: 5MB per file
- Allowed formats: PDF, JPEG, JPG, PNG
- Maximum 5 files total per claim

#### Get Claim Status
**Endpoint:** `GET /api/claim-status`

Retrieve the current status of a specific claim.

**Query Parameters:**
- `claimId`: Required, the unique claim identifier

**Response:**
```json
{
  "claimId": "CL123456",
  "status": "under_review",
  "lastUpdated": "2024-01-20T10:30:00Z"
}
```

**Possible Status Values:**
- `submitted`: Claim has been received
- `under_review`: Claim is being processed
- `approved`: Compensation has been approved
- `rejected`: Claim was rejected
- `resolved`: Claim processing is complete

#### Get User Claims
**Endpoint:** `GET /api/claims`

Retrieve all claims for the authenticated user.

**Response:**
```json
[
  {
    "claimId": "CL123456",
    "status": "under_review",
    "lastUpdated": "2024-01-20T10:30:00Z"
  },
  {
    "claimId": "CL789012",
    "status": "approved",
    "lastUpdated": "2024-01-18T15:45:00Z"
  }
]
```

#### Create Complete Claim
**Endpoint:** `POST /api/claims`

Create a complete claim with all information at once.

**Request Body:**
```json
{
  "flightNumber": "LH1234",
  "plannedDepartureDate": "2024-01-15",
  "actualDepartureTime": "2024-01-15T14:30:00Z",
  "fullName": "John Doe",
  "email": "john.doe@example.com",
  "bookingReference": "ABC123456"
}
```

**Response:**
```json
{
  "claimId": "CL123456",
  "status": "submitted",
  "lastUpdated": "2024-01-20T10:30:00Z"
}
```

### 2. Authentication

#### User Login (JSON)
**Endpoint:** `POST /api/auth/login-json`

Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "bookingReference": "ABC123456"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token Expiration:** 30 minutes

#### User Login (OAuth2)
**Endpoint:** `POST /api/auth/login`

OAuth2 password flow authentication.

**Request:** Form data
- `username`: User email
- `password`: Booking reference

**Response:** Same as JSON login

#### Get Current User
**Endpoint:** `GET /api/auth/me`

Get current authenticated user information.

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "bookingReference": "ABC123456",
  "isAdmin": false,
  "createdAt": "2024-01-15T10:00:00Z"
}
```

#### Refresh Token
**Endpoint:** `POST /api/auth/refresh`

Refresh the access token before it expires.

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Chat Functionality

#### Send Chat Message
**Endpoint:** `POST /api/chat/send`

Send a message to the chatbot and receive a response.

**Request Body:**
```json
{
  "sessionId": "sess_abc123def456",
  "message": "How much compensation can I get?"
}
```

**Response:**
```json
{
  "success": true,
  "reply": "Under EU Regulation 261/2004, you may be entitled to compensation of €250-€600...",
  "intent": "compensation",
  "confidence": 0.9
}
```

#### Create Chat Session
**Endpoint:** `POST /api/chat/sessions`

Create a new chat session.

**Response:**
```json
{
  "sessionId": "sess_abc123def456",
  "createdAt": "2024-01-20T10:30:00Z"
}
```

#### Get Chat History
**Endpoint:** `GET /api/chat/sessions/{session_id}/history`

Retrieve message history for a chat session.

**Response:**
```json
[
  {
    "sender": "user",
    "message": "Hello, I need help with my claim",
    "timestamp": "2024-01-20T10:25:00Z"
  },
  {
    "sender": "bot",
    "message": "Hello! I'm here to help you with your flight compensation claim.",
    "timestamp": "2024-01-20T10:25:05Z"
  }
]
```

### 4. Admin Functions

#### List All Claims
**Endpoint:** `GET /api/admin/claims`

List all claims (admin only).

**Query Parameters:**
- `skip`: Number of claims to skip (default: 0)
- `limit`: Maximum claims to return (default: 100, max: 1000)
- `status_filter`: Filter by claim status (optional)

**Response:**
```json
{
  "claims": [
    {
      "claimId": "CL123456",
      "userName": "John Doe",
      "flightNumber": "LH1234",
      "status": "under_review",
      "submittedAt": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### Update Claim Status
**Endpoint:** `PATCH /api/admin/claims/{claim_id}/status`

Update the status of a claim (admin only).

**Request Body:**
```json
{
  "status": "approved"
}
```

**Response:**
```json
{
  "message": "Claim status updated."
}
```

**Valid Status Values:** `submitted`, `under_review`, `approved`, `rejected`, `resolved`

#### Get System Statistics
**Endpoint:** `GET /api/admin/stats`

Get system-wide statistics (admin only).

**Response:**
```json
{
  "totalClaims": 150,
  "claimsByStatus": {
    "submitted": 25,
    "under_review": 50,
    "approved": 40,
    "rejected": 20,
    "resolved": 15
  },
  "recentClaims30Days": 30,
  "timestamp": "2024-01-20T10:30:00Z"
}
```

## Error Handling

All endpoints return consistent error responses:

**Error Response Format:**
```json
{
  "message": "Detailed error message"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Data Models

### FlightDetails Schema
```json
{
  "flightNumber": "string",      // Pattern: ^[A-Z]{2}\d{3,4}$
  "plannedDepartureDate": "date", // Format: YYYY-MM-DD
  "actualDepartureTime": "datetime" // Optional, ISO 8601 format
}
```

### PersonalInfo Schema
```json
{
  "fullName": "string",           // 1-255 characters
  "email": "string",              // Valid email format
  "bookingReference": "string"   // Minimum 6 characters
}
```

### ClaimStatus Schema
```json
{
  "claimId": "string",            // Unique claim identifier
  "status": "string",             // Claim status
  "lastUpdated": "datetime"       // ISO 8601 format
}
```

## Rate Limiting

- Standard API endpoints: 60 requests per minute
- Authentication endpoints: 30 requests per minute
- Admin endpoints: 120 requests per minute

## File Upload Specifications

**Supported Formats:**
- PDF documents
- JPEG images (.jpg, .jpeg)
- PNG images

**Size Limits:**
- Maximum file size: 5MB per file
- Maximum files per claim: 5

**Storage:**
- Files are stored in the `uploads/` directory
- Each file gets a unique generated filename
- Original filename and metadata are preserved

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    booking_reference VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Claims Table
```sql
CREATE TABLE claims (
    id SERIAL PRIMARY KEY,
    claim_id VARCHAR(20) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    booking_reference VARCHAR(255) NOT NULL,
    flight_number VARCHAR(10) NOT NULL,
    planned_departure_date DATE NOT NULL,
    actual_departure_time TIMESTAMP,
    disruption_type VARCHAR(50),
    incident_description TEXT,
    declaration_accepted BOOLEAN DEFAULT FALSE,
    consent_accepted BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'submitted',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Development Setup

### Quick Start
```bash
# Clone repository
git clone https://github.com/flightclaim/api.git
cd flight_claim_api

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Install dependencies
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Run development server
python run.py
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/flight_claim_db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=5

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_claims.py

# Run with coverage
pytest --cov=app
```

### Test Data
The API includes sample data for testing:
- Test user: `test@example.com` with booking reference `ABC123`
- Sample claims with various statuses
- Sample chat responses

## Production Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t flight-claim-api .
docker run -p 8000:8000 flight-claim-api
```

### Production Considerations
1. Use environment-specific configuration
2. Set up SSL/TLS certificates
3. Configure proper logging
4. Set up monitoring and alerting
5. Use managed database services
6. Implement proper backup strategies
7. Configure rate limiting appropriately

## Support

For API support and questions:
- Create an issue in the GitHub repository
- Email: team@flightclaim.com
- API Documentation: http://localhost:8000/docs
- OpenAPI Schema: http://localhost:8000/openapi.json

## Changelog

### Version 1.0.0
- Initial release with full OpenAPI 3.1.0 compliance
- Complete authentication system with JWT
- File upload functionality
- Admin dashboard capabilities
- Chatbot integration
- Comprehensive logging and monitoring