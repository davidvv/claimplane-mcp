# Flight Claim System - Project Architecture & Essential Files
**Date:** 2025-11-30  
**Version:** 1.0  
**Purpose:** Comprehensive guide to project structure, dataflow, and essential components

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [Data Flow](#data-flow)
5. [Essential Files & Directories](#essential-files--directories)
6. [Key Components](#key-components)
7. [Database Schema](#database-schema)
8. [API Endpoints](#api-endpoints)
9. [Authentication Flow](#authentication-flow)
10. [File Processing Pipeline](#file-processing-pipeline)

---

## Project Overview

**Flight Claim System** is a full-stack web application for managing EU261/2004 flight compensation claims. It enables customers to submit claims, upload supporting documents, and track claim status through an admin interface.

### Key Features
- **Passwordless Authentication** - Magic link login via email
- **Flight Compensation Calculation** - EU261/2004 regulation compliance
- **Document Management** - Secure file upload, encryption, and storage
- **Email Notifications** - Automated status updates and confirmations
- **Admin Dashboard** - Claim management and document review
- **Background Tasks** - Async processing via Celery
- **File Validation** - MIME type checking, virus scanning, content validation

### Business Domain
- **Customers** - Users submitting flight compensation claims
- **Claims** - Flight compensation requests with status tracking
- **Flights** - Flight information (number, airline, dates, airports)
- **Documents** - Supporting files (boarding passes, invoices, etc.)
- **Compensation** - Calculated amounts based on EU261/2004

---

## Technology Stack

### Backend
- **Framework:** FastAPI (Python async web framework)
- **Database:** PostgreSQL 15 (async via asyncpg)
- **Task Queue:** Celery (background job processing)
- **Message Broker:** Redis (Celery broker & caching)
- **File Storage:** Nextcloud (WebDAV integration)
- **Authentication:** JWT tokens + Magic links
- **Encryption:** Fernet (symmetric file encryption)
- **Email:** aiosmtplib (async SMTP)
- **Validation:** Pydantic (data validation)

### Frontend
- **Framework:** React 18 (TypeScript)
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **State Management:** React hooks + localStorage
- **UI Components:** Custom + shadcn/ui

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Web Server:** Nginx (reverse proxy)
- **Database:** PostgreSQL (Docker)
- **Cache/Queue:** Redis (Docker)
- **File Storage:** Nextcloud (Docker)

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  React Frontend (TypeScript)                             │   │
│  │  - Claim Form (Multi-step)                               │   │
│  │  - Document Upload                                       │   │
│  │  - Status Tracking                                       │   │
│  │  - Admin Dashboard                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Nginx (Reverse Proxy)                                   │   │
│  │  - SSL/TLS Termination                                   │   │
│  │  - Load Balancing                                        │   │
│  │  - Static File Serving                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Application                                     │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ Routers (API Endpoints)                            │  │   │
│  │  │ - /auth (Authentication)                           │  │   │
│  │  │ - /claims (Claim Management)                       │  │   │
│  │  │ - /files (Document Upload/Download)                │  │   │
│  │  │ - /flights (Flight Data)                           │  │   │
│  │  │ - /eligibility (Compensation Eligibility)          │  │   │
│  │  │ - /admin (Admin Operations)                        │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ Services (Business Logic)                          │  │   │
│  │  │ - AuthService (JWT, Magic Links)                   │  │   │
│  │  │ - FileService (Upload/Download)                    │  │   │
│  │  │ - EncryptionService (File Encryption)              │  │   │
│  │  │ - EmailService (Notifications)                     │  │   │
│  │  │ - CompensationService (EU261 Calculations)         │  │   │
│  │  │ - ClaimWorkflowService (Status Management)         │  │   │
│  │  │ - NextcloudService (File Storage)                  │  │   │
│  │  │ - FileValidationService (Security Checks)          │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL Database                                     │   │
│  │  - Users, Customers, Claims                             │   │
│  │  - Flights, Documents, Compensation                     │   │
│  │  - Audit Logs, Access Logs                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  EXTERNAL SERVICES LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Nextcloud (File Storage)                                │   │
│  │  - WebDAV API for file operations                        │   │
│  │  - Encrypted file storage                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SMTP Server (Email)                                     │   │
│  │  - Async email notifications                            │   │
│  │  - HTML templates                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  BACKGROUND PROCESSING LAYER                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Celery Worker                                           │   │
│  │  - Async task processing                                │   │
│  │  - Email sending                                         │   │
│  │  - File validation                                       │   │
│  │  - Claim status updates                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Redis                                                   │   │
│  │  - Task queue (Celery broker)                            │   │
│  │  - Result backend                                        │   │
│  │  - Caching                                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Claim Submission Flow

```
Customer Submits Claim
    ↓
Frontend: Multi-step form (Flight → Eligibility → Passenger → Review)
    ↓
POST /claims/create
    ↓
AuthService: Verify JWT token
    ↓
ClaimService: Create claim record
    ↓
PostgreSQL: Store claim data
    ↓
EmailService: Send confirmation email (async via Celery)
    ↓
Response: Claim ID + Status
    ↓
Frontend: Show success page
```

### 2. Document Upload Flow

```
Customer Uploads Document
    ↓
Frontend: File selection + drag-drop
    ↓
POST /files/upload
    ↓
FileValidationService: 
  - Check file size
  - Validate MIME type
  - Scan for viruses (optional)
  - Validate content
    ↓
EncryptionService: Encrypt file
    ↓
NextcloudService: Upload to Nextcloud via WebDAV
    ↓
FileService: Store metadata in PostgreSQL
    ↓
Response: File ID + Status
    ↓
Frontend: Update document list
```

### 3. Authentication Flow (Magic Link)

```
Customer Requests Login
    ↓
POST /auth/request-magic-link
    ↓
AuthService: Generate magic link token
    ↓
PostgreSQL: Store token with expiration
    ↓
EmailService: Send magic link email (async)
    ↓
Response: "Check your email"
    ↓
Customer Clicks Link
    ↓
GET /auth/verify-magic-link?token=xxx
    ↓
AuthService: Verify token + expiration
    ↓
AuthService: Create JWT access token
    ↓
Response: JWT token + Redirect to dashboard
    ↓
Frontend: Store JWT in localStorage
```

### 4. Claim Status Update Flow

```
Admin Updates Claim Status
    ↓
PUT /admin/claims/{claim_id}/status
    ↓
AuthService: Verify admin role
    ↓
ClaimWorkflowService: Validate status transition
    ↓
PostgreSQL: Update claim status
    ↓
EmailService: Send status update email (async via Celery)
    ↓
Response: Updated claim
    ↓
Frontend: Refresh claim details
```

### 5. File Download Flow

```
Customer/Admin Downloads Document
    ↓
GET /files/{file_id}/download
    ↓
AuthService: Verify access permissions
    ↓
FileService: Retrieve file metadata
    ↓
NextcloudService: Download from Nextcloud
    ↓
EncryptionService: Decrypt file
    ↓
Response: File bytes + Content-Type header
    ↓
Frontend: Trigger browser download
```

---

## Essential Files & Directories

### Backend Application Structure

```
app/
├── __init__.py                          # Package initialization
├── main.py                              # FastAPI app entry point
├── config.py                            # Configuration management
├── database.py                          # Database setup & session
├── models.py                            # SQLAlchemy ORM models
├── schemas.py                           # Pydantic request/response schemas
├── exceptions.py                        # Custom exception classes
├── middleware.py                        # FastAPI middleware setup
├── celery_app.py                        # Celery configuration
│
├── routers/                             # API endpoint handlers
│   ├── __init__.py
│   ├── auth.py                          # Authentication endpoints
│   ├── claims.py                        # Claim management endpoints
│   ├── files.py                         # File upload/download endpoints
│   ├── customers.py                     # Customer management endpoints
│   ├── flights.py                       # Flight data endpoints
│   ├── eligibility.py                   # Eligibility check endpoints
│   ├── health.py                        # Health check endpoints
│   ├── admin_claims.py                  # Admin claim management
│   └── admin_files.py                   # Admin file management
│
├── services/                            # Business logic layer
│   ├── __init__.py
│   ├── auth_service.py                  # JWT & magic link authentication
│   ├── email_service.py                 # Email notifications
│   ├── file_service.py                  # File operations (upload/download)
│   ├── file_validation_service.py       # File security validation
│   ├── encryption_service.py            # Fernet file encryption
│   ├── nextcloud_service.py             # Nextcloud WebDAV integration
│   ├── compensation_service.py          # EU261/2004 calculations
│   ├── claim_workflow_service.py        # Claim status management
│   └── password_service.py              # Password hashing (bcrypt)
│
├── tasks/                               # Celery background tasks
│   ├── __init__.py
│   └── claim_tasks.py                   # Async claim processing
│
├── templates/                           # Email templates
│   └── emails/
│       ├── claim_submitted.html         # Claim confirmation email
│       ├── magic_link_login.html        # Magic link email
│       ├── status_updated.html          # Status update email
│       └── document_rejected.html       # Document rejection email
│
└── tests/                               # Test suite
    ├── conftest.py                      # Pytest configuration
    ├── test_*.py                        # Individual test files
    └── README.md                        # Testing documentation
```

### Frontend Structure

```
frontend_Claude45/
├── src/
│   ├── main.tsx                         # React entry point
│   ├── App.tsx                          # Root component
│   ├── index.css                        # Global styles
│   │
│   ├── pages/                           # Page components
│   │   ├── Home.tsx                     # Landing page
│   │   ├── Auth.tsx                     # Login page
│   │   ├── Status.tsx                   # Claim status page
│   │   ├── Success.tsx                  # Success page
│   │   ├── MyClaims.tsx                 # Claims list page
│   │   ├── ClaimForm/                   # Multi-step claim form
│   │   │   ├── ClaimFormPage.tsx
│   │   │   ├── Step1_Flight.tsx
│   │   │   ├── Step2_Eligibility.tsx
│   │   │   ├── Step3_Passenger.tsx
│   │   │   └── Step4_Review.tsx
│   │   ├── Admin/                       # Admin pages
│   │   │   ├── AdminDashboard.tsx
│   │   │   └── ClaimDetailPage.tsx
│   │   └── Auth/
│   │       └── MagicLinkPage.tsx
│   │
│   ├── components/                      # Reusable components
│   │   ├── FileUploadZone.tsx           # Drag-drop file upload
│   │   ├── Stepper.tsx                  # Multi-step form stepper
│   │   └── ui/                          # UI component library
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Input.tsx
│   │       ├── Label.tsx
│   │       ├── Badge.tsx
│   │       ├── DropdownMenu.tsx
│   │       └── ...
│   │
│   ├── services/                        # API & business logic
│   │   ├── api.ts                       # Axios HTTP client
│   │   ├── auth.ts                      # Authentication service
│   │   ├── claims.ts                    # Claims API calls
│   │   ├── documents.ts                 # Document API calls
│   │   ├── flights.ts                   # Flight API calls
│   │   ├── eligibility.ts               # Eligibility API calls
│   │   ├── customers.ts                 # Customer API calls
│   │   ├── admin.ts                     # Admin API calls
│   │   └── ...
│   │
│   ├── hooks/                           # Custom React hooks
│   │   ├── useDarkMode.ts               # Dark mode toggle
│   │   └── useLocalStorageForm.ts       # Form state persistence
│   │
│   ├── types/                           # TypeScript types
│   │   └── api.ts                       # API response types
│   │
│   ├── schemas/                         # Validation schemas
│   │   └── validation.ts                # Zod validation schemas
│   │
│   └── vite-env.d.ts                    # Vite environment types
│
├── public/                              # Static assets
├── index.html                           # HTML entry point
├── vite.config.ts                       # Vite configuration
├── tsconfig.json                        # TypeScript configuration
├── tailwind.config.ts                   # Tailwind CSS configuration
├── postcss.config.js                    # PostCSS configuration
├── .env.example                         # Environment template
├── Dockerfile                           # Docker image
├── nginx.conf                           # Nginx configuration
└── package.json                         # Dependencies
```

### Configuration & Infrastructure

```
Root Directory:
├── .env.example                         # Environment variables template
├── .env                                 # Actual environment (git-ignored)
├── .gitignore                           # Git ignore rules
├── requirements.txt                     # Python dependencies
├── Dockerfile                           # Backend Docker image
├── docker-compose.yml                   # Multi-container setup
├── nginx.conf                           # Nginx reverse proxy config
├── README.md                            # Project documentation
│
├── scripts/                             # Utility scripts
│   ├── create_admin_user.py             # Create admin user
│   ├── generate_secrets.py              # Generate secure keys
│   ├── init_file_validation_rules.py    # Initialize validation rules
│   ├── setup_nextcloud.sh               # Nextcloud setup
│   └── setup_production_env.sh          # Production setup
│
├── docs/                                # Documentation
│   ├── api-reference.md                 # API documentation
│   ├── database-schema.md               # Database schema
│   ├── security-configuration.md        # Security guide
│   ├── troubleshooting-guide.md         # Troubleshooting
│   ├── ADMIN_INTERFACE.md               # Admin guide
│   ├── ADMIN_USER_MANAGEMENT.md         # Admin user guide
│   ├── FRONTEND_API_GUIDANCE.md         # Frontend integration
│   ├── SECURITY_AUDIT_v0.2.0.md         # Security audit
│   └── testing/                         # Testing documentation
│
├── API/                                 # API specification
│   └── openapi.yaml                     # OpenAPI/Swagger spec
│
├── .claude/                             # Claude AI configuration
├── AGENTS.md                            # Development guidelines
├── CLAUDE.md                            # Claude guidelines
└── ROADMAP.md                           # Project roadmap
```

---

## Key Components

### 1. Authentication Service (`app/services/auth_service.py`)
**Purpose:** Handle user authentication, JWT tokens, and magic links

**Key Methods:**
- `create_access_token()` - Generate JWT access token
- `verify_access_token()` - Validate JWT token
- `create_magic_link_token()` - Generate magic link token
- `verify_magic_link_token()` - Validate magic link
- `register_user()` - Create new user account
- `login_user()` - Authenticate user

**Flow:**
1. User requests magic link → Token generated & stored
2. Email sent with link
3. User clicks link → Token verified
4. JWT access token created
5. User authenticated for session

### 2. File Service (`app/services/file_service.py`)
**Purpose:** Handle file upload, download, and management

**Key Methods:**
- `upload_file()` - Upload and encrypt file
- `download_file()` - Download and decrypt file
- `delete_file()` - Soft delete file
- `get_file_info()` - Retrieve file metadata
- `get_files_by_claim()` - List files for claim

**Features:**
- Streaming upload for large files
- Automatic encryption with Fernet
- Nextcloud integration
- File validation before upload
- Access logging

### 3. Nextcloud Service (`app/services/nextcloud_service.py`)
**Purpose:** Integrate with Nextcloud for file storage

**Key Methods:**
- `upload_file()` - Upload file via WebDAV
- `download_file()` - Download file via WebDAV
- `delete_file()` - Delete file from Nextcloud
- `verify_upload_integrity()` - Verify uploaded file
- `create_share()` - Create share link

**Features:**
- Retry logic with exponential backoff
- Error classification and handling
- Integrity verification
- Timeout management

### 4. Email Service (`app/services/email_service.py`)
**Purpose:** Send email notifications

**Key Methods:**
- `send_email()` - Send email via SMTP
- `send_claim_submitted_email()` - Claim confirmation
- `send_magic_link_login_email()` - Magic link email
- `send_status_update_email()` - Status change notification
- `send_document_rejected_email()` - Document rejection notice

**Features:**
- HTML + plain text templates
- Jinja2 template rendering
- Async SMTP (aiosmtplib)
- Gmail app-specific password support

### 5. Compensation Service (`app/services/compensation_service.py`)
**Purpose:** Calculate flight compensation per EU261/2004

**Key Methods:**
- `calculate_compensation()` - Calculate compensation amount
- `get_base_compensation()` - Get base amount by distance
- `check_extraordinary_circumstances()` - Check exemptions
- `calculate_distance()` - Calculate flight distance

**EU261/2004 Rules:**
- €250 for flights ≤1500km
- €400 for flights 1500-3500km
- €600 for flights >3500km
- Reduced by 50% for extraordinary circumstances

### 6. Claim Workflow Service (`app/services/claim_workflow_service.py`)
**Purpose:** Manage claim status transitions

**Status Flow:**
```
submitted → under_review → approved/rejected → paid
                         ↓
                    document_requested
                         ↓
                    resubmitted
```

**Key Methods:**
- `validate_status_transition()` - Check valid transitions
- `transition_status()` - Update claim status
- `assign_claim()` - Assign to admin
- `set_compensation()` - Set compensation amount

---

## Database Schema

### Core Tables

**customers**
- id (UUID, PK)
- email (String, unique)
- first_name, last_name
- phone_number
- created_at, updated_at

**claims**
- id (UUID, PK)
- customer_id (FK → customers)
- flight_id (FK → flights)
- status (enum: submitted, under_review, approved, rejected, paid)
- compensation_amount (Decimal)
- created_at, updated_at

**flights**
- id (UUID, PK)
- flight_number (String)
- airline (String)
- departure_airport, arrival_airport
- departure_date, arrival_date
- aircraft_type

**claim_files**
- id (UUID, PK)
- claim_id (FK → claims)
- file_name (String)
- file_type (String)
- file_size (Integer)
- nextcloud_path (String)
- encrypted (Boolean)
- created_at, updated_at

**users** (Admin users)
- id (UUID, PK)
- email (String, unique)
- password_hash (String)
- role (enum: admin, superadmin)
- created_at, updated_at

---

## API Endpoints

### Authentication
- `POST /auth/request-magic-link` - Request magic link
- `GET /auth/verify-magic-link` - Verify magic link
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Logout user

### Claims
- `POST /claims/create` - Create new claim
- `GET /claims/{claim_id}` - Get claim details
- `GET /claims/customer/{customer_id}` - List customer claims
- `PUT /claims/{claim_id}` - Update claim

### Files
- `POST /files/upload` - Upload document
- `GET /files/{file_id}/download` - Download document
- `DELETE /files/{file_id}` - Delete document
- `GET /files/claim/{claim_id}` - List claim documents

### Admin
- `GET /admin/claims` - List all claims
- `PUT /admin/claims/{claim_id}/status` - Update claim status
- `PUT /admin/claims/{claim_id}/compensation` - Set compensation
- `GET /admin/files` - List all files

---

## Authentication Flow

### Magic Link Authentication

```
1. User enters email
   ↓
2. POST /auth/request-magic-link
   ↓
3. Backend generates token (48-hour expiration)
   ↓
4. Email sent with link: /auth/magic-link?token=xxx
   ↓
5. User clicks link
   ↓
6. GET /auth/verify-magic-link?token=xxx
   ↓
7. Backend verifies token
   ↓
8. JWT access token created
   ↓
9. Frontend stores JWT in localStorage
   ↓
10. User authenticated for session
```

### JWT Token Structure

```
Header: {
  "alg": "HS256",
  "typ": "JWT"
}

Payload: {
  "sub": "user_id",
  "email": "user@example.com",
  "role": "customer",
  "exp": 1234567890,
  "iat": 1234567800
}

Signature: HMACSHA256(header.payload, SECRET_KEY)
```

---

## File Processing Pipeline

### Upload Pipeline

```
1. File Selected
   ↓
2. Frontend Validation
   - Check file size
   - Check file type
   ↓
3. POST /files/upload
   ↓
4. Backend Validation
   - Verify file size
   - Detect MIME type
   - Scan for viruses (optional)
   - Validate content
   ↓
5. Encryption
   - Generate random IV
   - Encrypt with Fernet
   ↓
6. Upload to Nextcloud
   - WebDAV PUT request
   - Retry on failure
   ↓
7. Verify Integrity
   - Download and compare hash
   - Verify file size
   ↓
8. Store Metadata
   - Save to PostgreSQL
   - Record file path
   ↓
9. Response
   - Return file ID
   - Return status
```

### Download Pipeline

```
1. GET /files/{file_id}/download
   ↓
2. Verify Access
   - Check user permissions
   - Check claim ownership
   ↓
3. Retrieve Metadata
   - Get file info from DB
   - Get Nextcloud path
   ↓
4. Download from Nextcloud
   - WebDAV GET request
   - Stream large files
   ↓
5. Decrypt
   - Retrieve encryption key
   - Decrypt with Fernet
   ↓
6. Log Access
   - Record download in audit log
   ↓
7. Response
   - Set Content-Type header
   - Stream file bytes
   ↓
8. Browser
   - Download file
```

---

## Development Workflow

### Local Setup
1. Clone repository
2. Copy `.env.example` to `.env`
3. Update `.env` with local values
4. Run `docker-compose up -d`
5. Run migrations: `python init_db.py`
6. Start frontend: `cd frontend_Claude45 && npm run dev`

### Running Tests
```bash
# All tests
pytest

# Specific test
pytest tests/test_auth_endpoints.py::test_login

# With coverage
pytest --cov=app --cov-report=html
```

### Running Celery Worker
```bash
celery -A app.celery_app worker --loglevel=info
```

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI spec: `http://localhost:8000/openapi.json`

---

## Deployment Considerations

### Production Checklist
- [ ] Generate new SECRET_KEY
- [ ] Generate new FILE_ENCRYPTION_KEY
- [ ] Configure production database
- [ ] Configure production email (SMTP)
- [ ] Configure Nextcloud with production credentials
- [ ] Set ENVIRONMENT=production
- [ ] Enable SECURITY_HEADERS_ENABLED
- [ ] Configure CORS_ORIGINS for production domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure backup strategy for database
- [ ] Configure backup strategy for encrypted files
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting appropriately

### Scaling Considerations
- Database: Use managed PostgreSQL (AWS RDS, Azure Database)
- File Storage: Use managed Nextcloud or S3-compatible storage
- Cache/Queue: Use managed Redis (AWS ElastiCache, Azure Cache)
- API: Use load balancer with multiple FastAPI instances
- Frontend: Use CDN for static assets
- Email: Use transactional email service (SendGrid, AWS SES)

---

## Security Considerations

### Data Protection
- Files encrypted with Fernet (symmetric encryption)
- Passwords hashed with bcrypt
- JWT tokens signed with HS256
- HTTPS/TLS for all communications

### Access Control
- Magic link authentication (no passwords)
- JWT token-based authorization
- Role-based access control (customer, admin)
- Claim ownership verification

### File Security
- MIME type validation
- File content validation
- Virus scanning (optional ClamAV)
- Secure file deletion
- Access logging

### API Security
- Rate limiting on uploads/downloads
- CORS configuration
- Security headers (HSTS, CSP, X-Frame-Options)
- Input validation with Pydantic
- SQL injection prevention (ORM)

---

## Monitoring & Logging

### Application Logs
- Location: stdout (Docker logs)
- Level: Configurable via LOG_LEVEL
- Format: JSON (recommended for production)

### Database Logs
- PostgreSQL query logs
- Slow query logs
- Connection pool monitoring

### Task Logs
- Celery worker logs
- Task execution times
- Failed task tracking

### Access Logs
- File access audit trail
- API request logs
- Admin action logs

---

## Troubleshooting Guide

### Common Issues

**Database Connection Failed**
- Check DATABASE_URL format
- Verify PostgreSQL is running
- Check credentials
- Check firewall/network

**Email Not Sending**
- Check SMTP credentials
- Verify SMTP_HOST and SMTP_PORT
- For Gmail: Use app-specific password
- Check NOTIFICATIONS_ENABLED=true

**File Upload Fails**
- Check Nextcloud is running
- Verify NEXTCLOUD credentials
- Check disk space
- Check file size limits

**Celery Tasks Not Running**
- Check Redis is running
- Verify REDIS_URL
- Check celery worker is started
- Check task logs

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [EU261/2004 Regulation](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32004R0261)
- [React Documentation](https://react.dev/)
- [Nextcloud WebDAV API](https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/index.html)

---

**Last Updated:** 2025-11-30  
**Maintained By:** Development Team  
**Status:** Active
