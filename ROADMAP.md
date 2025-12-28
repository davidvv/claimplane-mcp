# Development Roadmap

**Last Updated**: 2025-12-28
**Current Version**: v0.3.0 (Phase 3 Complete, Phase 4.5 In Progress - JWT Cookie Migration)
**Status**: MVP Phase - Security Hardening for Public Launch 🔒
**Strategy**: Business value first (#2 → #3 → #4 → GDPR)
**Deployment URL**: https://eac.dvvcloud.work (Cloudflare Tunnel + OAuth)

This roadmap outlines the next development phases for the flight claim management platform, prioritized for MVP launch.

---

## 🎯 NEXT STEPS - START HERE

**Current State**: Security Hardening In Progress 🔒 (v0.3.0+)
- ✅ Admin Dashboard & Claim Workflow (Phase 1)
- ✅ Async Task Processing & Email Notifications (Phase 2)
- ✅ JWT Authentication & Authorization System (Phase 3) 🎉
- ⏳ Customer Account Management & GDPR Compliance (Phase 4) - 80% Complete
- ⏳ **Pre-Production Security Fixes (Phase 4.5)** - 93% Complete ⬅️ **IN PROGRESS**
  - ✅ SQL Injection fixed
  - ✅ CORS Wildcard fixed
  - ✅ Blacklist Bypass fixed
  - ✅ Rate Limiting fixed (with Cloudflare support)
  - ⚠️ SMTP Credentials (user action required)
  - ⏳ JWT Token Storage (localStorage → HTTP-only cookies) **NEW PRIORITY**
  - ⏸️ HTTPS (handled by Cloudflare during testing)
  - ⏸️ Security Headers (handled by Cloudflare during testing)

**Phase 3 Status**: ✅ **COMPLETED** (2025-11-03) 🔐
- ✅ Complete JWT authentication infrastructure
- ✅ Auth service with token generation, refresh, revocation
- ✅ 9 authentication endpoints (register, login, refresh, logout, password reset, etc.)
- ✅ Role-based access control (RBAC) dependencies
- ✅ Password hashing with bcrypt (12 rounds)
- ✅ Database models (Customer enhanced, RefreshToken, PasswordResetToken)
- ✅ Security improvements: Fixes 10/26 vulnerabilities automatically
- ✅ All routers updated to use JWT authentication
- ✅ Ownership verification (customers can only access their own data)
- ✅ Admin-only endpoints properly protected
- ✅ End-to-end testing completed
- 📄 **See [PHASE3_COMPLETION_PLAN.md](PHASE3_COMPLETION_PLAN.md) for complete details**

**What's Implemented**:
1. ✅ JWT-based authentication system (access + refresh tokens)
2. ✅ User registration and login endpoints
3. ✅ Password reset flow with email verification
4. ✅ Role-based access control (RBAC) with customer/admin/superadmin roles
5. ✅ JWT middleware and dependencies
6. ✅ Token refresh mechanism with rotation
7. ✅ Device tracking and audit logging
8. ✅ All routers migrated from header-based to JWT authentication
9. ✅ Ownership verification (IDOR protection)
10. ✅ `/me` endpoints for self-service customer operations

**Security Improvements**:
- ✅ Complete Authentication Bypass fixed (CVSS 9.8)
- ✅ IDOR Vulnerabilities fixed (CVSS 8.8)
- ✅ Missing Authorization Checks fixed (CVSS 7.5)
- ✅ Password Policy implemented (CVSS 5.0)
- ✅ Session Timeout implemented (CVSS 6.5)
- ✅ CSRF Protection (Bearer tokens immune to CSRF)
- ✅ Rate Limiting Framework (token-based user identification)
- ✅ Audit Logging enhanced (login tracking, device info)
- ✅ MFA Infrastructure ready (auth system extensible)
- ✅ Account Lockout capability (token revocation)

**Next Priority**:
1. **IMMEDIATE**: Migrate JWT tokens to HTTP-only cookies (security patch → v0.3.1)
2. Complete Phase 4 (Customer Account Management)
3. Phase 5 (Multi-Passenger Claims)

---

## 🌐 Cloudflare Tunnel Deployment (2025-12-08)

**Status**: ✅ **COMPLETED AND LIVE**
**URL**: https://eac.dvvcloud.work
**Access**: Cloudflare OAuth authentication required (team only)

### Deployment Summary

Successfully deployed the application through Cloudflare Tunnel for production testing. This milestone enables secure, remote access to the platform with OAuth protection during the testing phase.

### Implementation Details

#### Frontend Configuration
- **Vite Host Allowlist**: Added `eac.dvvcloud.work` to `server.allowedHosts` in vite.config.ts:17
- **Vite Proxy**: Comprehensive proxy configuration for all API endpoints (lines 18-89)
  - Routes API requests from frontend (port 3000) → backend (port 80)
  - Endpoints proxied: `/auth/*`, `/claims`, `/files`, `/customers`, `/flights`, `/eligibility`, `/account`, `/admin`, `/health`
  - Each proxy uses `changeOrigin: true` for proper header forwarding

#### Backend Configuration
- **CORS Origins**: Updated to include Cloudflare domain in app/config.py:41
  - Default: `http://localhost:3000,http://localhost:8081,https://eac.dvvcloud.work`
- **FastAPI Redirects**: Set `redirect_slashes=False` in app/main.py to prevent CORS issues with automatic redirects
- **Email Templates**: All email links now use `https://eac.dvvcloud.work` via FRONTEND_URL environment variable

#### Docker Configuration
- **Environment Variables**: Updated docker-compose.yml with Cloudflare domain defaults
  - `FRONTEND_URL: ${FRONTEND_URL:-https://eac.dvvcloud.work}` (lines 68, 96)
- **Container Recreation**: Learned that `docker compose restart` doesn't reload .env files
  - Proper workflow: `docker compose down && docker compose up -d`

#### URL Updates
- **.env Files**: Updated all environment files with Cloudflare domain
  - Backend: `/home/david/easyAirClaim/easyAirClaim/.env`
  - Frontend: `/home/david/easyAirClaim/easyAirClaim/frontend_Claude45/.env`
- **API Client**: Changed fallback from `localhost:8000` to empty string (uses Vite proxy)
  - Location: frontend_Claude45/src/services/api.ts:10

#### Flight API Enhancement
- **Flexible Validation**: Made flight lookup accept any format for testing (app/routers/flights.py)
  - Previously: Rejected non-standard formats like `AA123`
  - Now: Accepts all flight numbers with graceful fallback

### Architecture

**Request Flow**:
```
Browser → Cloudflare Tunnel (OAuth) → Vite Dev Server (port 3000) → Proxy → FastAPI Backend (port 80)
```

**Key Design Decisions**:
1. Vite proxy acts as bridge between frontend and backend
2. All API requests go through proxy (no direct backend access from browser)
3. Cloudflare handles HTTPS termination and OAuth authentication
4. Frontend served on port 3000, backend on port 80 (Docker internal)

### Testing Results

✅ **Magic Link Authentication**: Email sending and verification working end-to-end
✅ **Claim Submission Flow**: Flight lookup, eligibility check, claim submission all functional
✅ **File Operations**: Document upload and download working through tunnel
✅ **Admin Functions**: Superadmin accounts created and functional
✅ **Email Notifications**: Credential emails successfully delivered via Gmail SMTP

### Known Limitations

- **Vite Proxy Required**: Frontend must run through Vite dev server (not direct nginx)
- **Environment Variable Updates**: Require full container recreation (down/up, not restart)
- **OAuth Protection**: Currently team-only access (will be public after testing phase)
- **Mock Flight Data**: Flight API still using test data (not connected to real flight database)

### Files Modified

1. `vite.config.ts` - Added allowedHosts and comprehensive proxy config (lines 17-89)
2. `app/main.py` - Set redirect_slashes=False to prevent CORS issues
3. `docker-compose.yml` - Updated FRONTEND_URL defaults (lines 68, 96)
4. `.env` - Updated FRONTEND_URL to Cloudflare domain
5. `frontend_Claude45/.env` - Updated VITE_API_BASE_URL to Cloudflare domain
6. `app/config.py` - Added Cloudflare domain to CORS defaults
7. `.env.example` - Updated with Cloudflare domain for documentation
8. `frontend_Claude45/.env.example` - Updated with Cloudflare domain
9. `app/routers/flights.py` - Made flight validation flexible for testing
10. `frontend_Claude45/src/services/claims.ts` - Added trailing slash to /claims/ call
11. `frontend_Claude45/src/services/api.ts` - Changed fallback to empty string
12. `scripts/send_admin_credentials.py` - Created admin credential email sender

### Git Commits

1. **b9a0446** - `feat(deployment): integrate Cloudflare tunnel support`
2. **5164028** - `fix(flights): accept all flight numbers in mock API`
3. **d51d464** - `fix(config): update hardcoded URLs to support Cloudflare tunnel`
4. **efc283c** - `fix(proxy): add missing API endpoint proxies`
5. **3252c3a** - `feat(admin): add admin credentials email sender script`

### Superadmin Accounts

Created two superadmin accounts for testing:
- **David Vences Vaquero** (vences.david@icloud.com) - Credentials sent via email ✅
- **Florian Luhn** (florian.luhn@gmail.com) - Credentials sent via email ✅

Both accounts use magic link authentication (passwordless).

### Next Steps for Production

- [ ] **IMMEDIATE**: Complete Phase 4.5.14 (JWT HTTP-only cookie migration) → v0.3.1
- [ ] **IMMEDIATE**: Implement Phase 4.6 (Cookie Consent Banner) - GDPR requirement
- [ ] Complete Phase 4 (GDPR compliance and customer account management)
- [ ] Evaluate HTTPS requirements if removing Cloudflare tunnel
- [ ] Consider security headers implementation (currently handled by Cloudflare)
- [ ] Update to production frontend build (currently dev server)
- [ ] Remove OAuth requirement for public access (blocked by cookie consent)
- [ ] Configure production email templates
- [ ] Set up monitoring and logging

### Security Considerations

**Current Setup (Testing Phase)**:
- ✅ HTTPS via Cloudflare Tunnel
- ✅ OAuth authentication (team access only)
- ✅ Rate limiting implemented (Phase 4.5)
- ✅ SQL injection fixed (Phase 4.5)
- ✅ CORS properly configured
- ✅ JWT authentication active

**Future Considerations**:
- May need direct HTTPS if removing Cloudflare (GDPR concerns)
- Security headers currently handled by Cloudflare
- Production build required before public launch

---

## Phase 1: Admin Dashboard & Claim Workflow Management

**Priority**: HIGHEST
**Status**: ✅ **COMPLETED** (2025-10-29)
**Estimated Effort**: 2-3 weeks
**Actual Effort**: 1 session
**Business Value**: Critical - enables core revenue-generating workflow

**📄 See [PHASE1_SUMMARY.md](PHASE1_SUMMARY.md) for complete implementation details.**

### Overview
Build the administrative interface and backend logic to review, process, and manage flight compensation claims. This is the core business function that allows the platform to generate revenue.

### Features to Implement

#### 1.1 Admin Claim Management Endpoints

**File**: `app/routers/admin_claims.py` (new)

- [ ] `GET /admin/claims` - List all claims with filtering
  - Filter by: status, date range, airline, incident type, assigned reviewer
  - Pagination with configurable page size
  - Sorting by: submission date, departure date, compensation amount
  - Search by: customer name, email, flight number, claim ID

- [ ] `GET /admin/claims/{claim_id}` - Get detailed claim with all files
  - Include customer information
  - Include all uploaded documents
  - Include claim history/audit trail
  - Include calculated compensation details

- [ ] `PUT /admin/claims/{claim_id}/status` - Update claim status
  - Valid transitions: submitted → under_review → approved/rejected → paid → closed
  - Validate status transitions (can't go from rejected to approved directly)
  - Require reason for rejection
  - Auto-timestamp status changes

- [ ] `PUT /admin/claims/{claim_id}/assign` - Assign claim to reviewer
  - Track assigned_to (reviewer user ID)
  - Track assigned_at timestamp
  - Support reassignment

- [ ] `PUT /admin/claims/{claim_id}/compensation` - Set compensation amount
  - Manual override for special cases
  - Audit trail of amount changes
  - Support partial compensation

- [ ] `POST /admin/claims/{claim_id}/notes` - Add internal notes
  - Private notes (not visible to customer)
  - Track note author and timestamp
  - Support attachments

- [ ] `POST /admin/claims/bulk-action` - Bulk operations
  - Bulk status update
  - Bulk assignment
  - Bulk export to CSV/Excel

#### 1.2 Compensation Calculation Engine

**File**: `app/services/compensation_service.py` (new)

Implement EU Regulation 261/2004 calculation logic:

- [ ] Distance-based compensation tiers
  - < 1,500 km: €250
  - 1,500 - 3,500 km: €400
  - > 3,500 km: €600

- [ ] Delay threshold logic
  - < 3 hours: No compensation
  - 3+ hours: Full compensation based on distance
  - Calculate delay from scheduled vs actual arrival time

- [ ] Extraordinary circumstances detection
  - Weather-related cancellations (reduced/no compensation)
  - Technical issues (full compensation)
  - Air traffic control issues (case-by-case)
  - Flag for manual review

- [ ] Partial compensation rules
  - Flights > 3,500 km with 3-4 hour delay: 50% compensation
  - Alternative flight offered: potential reduction

- [ ] Calculate distance between airports
  - Use IATA airport code database
  - Great circle distance calculation
  - Cache airport coordinates

#### 1.3 Document Review Interface (Backend)

**File**: `app/routers/admin_files.py` (new)

- [ ] `GET /admin/claims/{claim_id}/documents` - List all documents for a claim
  - Group by document type
  - Show validation status
  - Show security scan results

- [ ] `PUT /admin/files/{file_id}/review` - Approve/reject document
  - Mark as approved/rejected
  - Add rejection reason
  - Require re-upload if rejected
  - Track reviewer and review timestamp

- [ ] `GET /admin/files/{file_id}/metadata` - Get detailed file metadata
  - Upload timestamp
  - File size and type
  - Hash for integrity
  - Access logs
  - Security scan results

- [ ] `POST /admin/files/{file_id}/request-reupload` - Request document re-upload
  - Notify customer
  - Specify reason
  - Set deadline

#### 1.4 Database Schema Updates

**File**: `app/models.py` (update)

Add new fields to `Claim` model:

```python
assigned_to = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
assigned_at = Column(DateTime(timezone=True), nullable=True)
reviewed_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
reviewed_at = Column(DateTime(timezone=True), nullable=True)
rejection_reason = Column(Text, nullable=True)
calculated_compensation = Column(Numeric(10, 2), nullable=True)
flight_distance_km = Column(Numeric(10, 2), nullable=True)
delay_hours = Column(Numeric(5, 2), nullable=True)
extraordinary_circumstances = Column(String(255), nullable=True)
```

Add new `ClaimNote` model:

```python
class ClaimNote(Base):
    __tablename__ = "claim_notes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    author_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    note_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True)  # Internal vs customer-facing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Add new `ClaimStatusHistory` model for audit trail:

```python
class ClaimStatusHistory(Base):
    __tablename__ = "claim_status_history"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    change_reason = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### 1.5 Repositories

**File**: `app/repositories/admin_claim_repository.py` (new)

- [ ] Query methods for admin views
- [ ] Bulk operation support
- [ ] Complex filtering and sorting
- [ ] Analytics queries (claims by status, by airline, etc.)

#### 1.6 Status Transition Validation

**File**: `app/services/claim_workflow_service.py` (new)

- [ ] Define valid status transition rules
- [ ] Validate transitions before applying
- [ ] Handle side effects (notifications, logging, etc.)
- [ ] Status change authorization (who can change what)

### Testing Requirements

- [ ] Unit tests for compensation calculation
- [ ] Integration tests for status transitions
- [ ] Test bulk operations
- [ ] Test invalid status transitions
- [ ] Test compensation edge cases

### Success Criteria

- ✅ Admin can view all claims in a filterable list
- ✅ Admin can review documents and approve/reject them
- ✅ Admin can calculate compensation automatically based on EU261/2004
- ✅ Admin can update claim status with proper audit trail
- ✅ All status changes are logged in status history
- ✅ Invalid status transitions are prevented

---

## Phase 2: Async Task Processing & Notification System

**Priority**: HIGH
**Status**: ✅ **COMPLETED** (2025-11-02)
**Estimated Effort**: 1-2 weeks
**Actual Effort**: 2 sessions (implementation + bug fixes)
**Business Value**: High - improves UX and enables automation

**📄 Documentation:**
- [PHASE2_SUMMARY.md](PHASE2_SUMMARY.md) - Complete implementation details
- [PHASE2_COMPLETION.md](PHASE2_COMPLETION.md) - Final completion report with test results
- [Testing Guide](docs/testing/PHASE2_TESTING_GUIDE.md) - Detailed testing procedures

**✅ What Was Delivered:**
- Celery + Redis async task processing
- SMTP email service with professional templates
- Claim submitted email (tested ✅)
- Status update emails: under_review, approved, paid (tested ✅)
- Document rejection email (implemented, untested due to file upload bugs)
- Critical bug fixes: load_dotenv, SMTP TLS, async greenlet_spawn

**📊 Test Results:**
- 4/4 tested email scenarios working
- 100% success rate
- Average delivery time: 1.7 seconds
- Zero task failures

### Overview
Implemented asynchronous task processing using Celery and built a comprehensive email notification system to keep customers informed about their claim status throughout the lifecycle.

### Features to Implement

#### 2.1 Celery Setup

**File**: `app/celery_app.py` (new)

- [ ] Configure Celery with Redis broker
- [ ] Set up task routing and queues
  - `notifications` queue for email/SMS
  - `processing` queue for heavy operations
  - `scheduled` queue for periodic tasks
- [ ] Configure retry policies
- [ ] Set up task monitoring and logging
- [ ] Add Flower for task monitoring (optional)

**File**: `docker-compose.yml` (update)

- [ ] Add Redis service
- [ ] Add Celery worker service
- [ ] Add Celery beat service (for scheduled tasks)
- [ ] Configure environment variables

#### 2.2 Email Service

**File**: `app/services/email_service.py` (new)

- [ ] Choose email provider (SendGrid, AWS SES, or SMTP)
- [ ] Configure email templates
  - Claim submitted confirmation
  - Claim status update
  - Document rejection notice
  - Compensation approved
  - Payment processed
  - Welcome email
  - Password reset (for Phase 3)

- [ ] Implement email sending with attachments
- [ ] HTML and plain text versions
- [ ] Email queuing and retry logic
- [ ] Unsubscribe functionality

**File**: `app/templates/emails/` (new directory)

- [ ] Create Jinja2 email templates
- [ ] Use HTML templates with proper styling
- [ ] Include company branding/logo
- [ ] Make templates multilingual-ready

#### 2.3 Notification System

**File**: `app/services/notification_service.py` (new)

- [ ] Unified notification interface
- [ ] Support multiple channels (email, SMS, in-app)
- [ ] Notification preferences per customer
- [ ] Notification history/audit trail

**File**: `app/models.py` (update)

Add `Notification` model:

```python
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # email, sms, in_app
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, sent, failed
    sent_at = Column(DateTime(timezone=True), nullable=True)
    failed_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Add `NotificationPreference` model:

```python
class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    claim_submitted = Column(Boolean, default=True)
    status_updates = Column(Boolean, default=True)
    document_requests = Column(Boolean, default=True)
    payment_notifications = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

#### 2.4 Background Tasks

**File**: `app/tasks/claim_tasks.py` (new)

- [ ] Task: Send claim submission confirmation
- [ ] Task: Send status update notification
- [ ] Task: Send document rejection notification
- [ ] Task: Send compensation approved notification
- [ ] Task: Process document OCR (future enhancement)
- [ ] Task: Generate claim report/PDF

**File**: `app/tasks/file_tasks.py` (new)

- [ ] Task: Virus scan with ClamAV (if enabled)
- [ ] Task: Generate file thumbnails for images
- [ ] Task: Extract text from PDFs (OCR)
- [ ] Task: Verify file integrity periodically

**File**: `app/tasks/scheduled_tasks.py` (new)

- [ ] Task: Send reminder for incomplete claims
- [ ] Task: Auto-close claims after payment
- [ ] Task: Clean up expired files
- [ ] Task: Generate daily/weekly reports
- [ ] Task: Check for claim expiration (statute of limitations)

#### 2.5 Webhook System (Optional)

**File**: `app/services/webhook_service.py` (new)

- [ ] Allow customers to register webhook URLs
- [ ] Send claim status updates to webhooks
- [ ] Retry failed webhook deliveries
- [ ] Webhook authentication (HMAC signatures)

#### 2.6 Integration Points

Update existing code to trigger notifications:

- [ ] `app/routers/claims.py` - Send notification on claim submission
- [ ] `app/routers/admin_claims.py` - Send notification on status change
- [ ] `app/routers/admin_files.py` - Send notification on document rejection
- [ ] `app/services/file_service.py` - Queue virus scan task after upload

### Configuration Updates

**File**: `app/config.py` (update)

```python
# Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@flightclaim.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Flight Claim System")

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Notification Settings
NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"
```

### Testing Requirements

- [ ] Test email sending with different templates
- [ ] Test Celery task execution and retries
- [ ] Test notification preferences
- [ ] Test scheduled tasks
- [ ] Test failure scenarios (email bounce, task failure)

### Success Criteria

- ✅ Customers receive email when claim is submitted
- ✅ Customers receive email when status changes
- ✅ Heavy operations (virus scan, OCR) run in background
- ✅ Failed tasks are retried automatically
- ✅ Scheduled tasks run on time
- ✅ Email templates are professional and branded

---

## Phase 3: Authentication & Authorization System ⬅️ **IN PROGRESS (~90% COMPLETE)**

**Priority**: HIGH - Required before public launch
**Status**: ⏳ **IN PROGRESS** - ~90% Complete (2-3 hours remaining)
**Estimated Effort**: 2-3 weeks (actual: 1 session + 2-3 hours)
**Target Version**: v0.3.0
**Business Value**: Critical for security and public launch
**📄 Progress Tracking**: See [PHASE3_IMPLEMENTATION_STATUS.md](PHASE3_IMPLEMENTATION_STATUS.md)

### Overview
Replace the current header-based authentication (`X-Customer-ID`) with a proper JWT-based authentication system with role-based access control.

### Features to Implement

#### 3.1 User Authentication

**File**: `app/routers/auth.py` (new)

- [ ] `POST /auth/register` - User registration
  - Email validation
  - Password strength requirements
  - Send verification email
  - Create customer record

- [ ] `POST /auth/login` - User login
  - Email/password authentication
  - Return JWT access token + refresh token
  - Track login attempts and lockout after failures

- [ ] `POST /auth/logout` - User logout
  - Invalidate refresh token
  - Add to token blacklist

- [ ] `POST /auth/refresh` - Refresh access token
  - Validate refresh token
  - Issue new access token

- [ ] `POST /auth/forgot-password` - Request password reset
  - Send reset email with token
  - Token expires in 1 hour

- [ ] `POST /auth/reset-password` - Reset password with token
  - Validate token
  - Update password
  - Invalidate all existing tokens

- [ ] `POST /auth/verify-email` - Verify email with token
  - Mark email as verified
  - Enable full account access

- [ ] `POST /auth/resend-verification` - Resend verification email

#### 3.2 JWT Token Management

**File**: `app/services/auth_service.py` (new)

- [ ] Generate JWT access tokens (short-lived: 30 min)
- [ ] Generate refresh tokens (long-lived: 7 days)
- [ ] Token validation and parsing
- [ ] Token blacklisting for logout
- [ ] Extract user info from token

**File**: `app/models.py` (update)

Add `User` model (separate from Customer for authentication):

```python
class User(Base):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=False)  # Activated after email verification
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default="customer")  # customer, admin, reviewer

    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to customer profile
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

Add `RefreshToken` model:

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Add `PasswordResetToken` model:

```python
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### 3.3 Password Security

**File**: `app/services/password_service.py` (new)

- [ ] Hash passwords with bcrypt (passlib already in requirements.txt)
- [ ] Validate password strength
  - Minimum 8 characters
  - At least one uppercase
  - At least one lowercase
  - At least one number
  - At least one special character
- [ ] Check against common password lists
- [ ] Password history (prevent reuse)

#### 3.4 Authorization Middleware

**File**: `app/middleware/auth_middleware.py` (new)

- [ ] JWT validation middleware
- [ ] Extract user from token
- [ ] Attach user to request context
- [ ] Handle expired/invalid tokens

**File**: `app/dependencies.py` (new)

- [ ] `get_current_user` dependency - Require valid JWT
- [ ] `get_current_active_user` dependency - Require active user
- [ ] `require_role(role)` dependency factory - Role-based access
- [ ] `require_verified_email` dependency - Email verification check

#### 3.5 Role-Based Access Control (RBAC)

Define three roles:

1. **Customer**
   - View own claims
   - Submit new claims
   - Upload documents to own claims
   - View own files

2. **Reviewer**
   - View all claims
   - Update claim status
   - Approve/reject documents
   - Add internal notes

3. **Admin**
   - All reviewer permissions
   - Manage users
   - Access analytics
   - Configure system settings
   - Bulk operations

**File**: `app/services/authorization_service.py` (new)

- [ ] Check if user has permission
- [ ] Check resource ownership
- [ ] Role hierarchy (admin > reviewer > customer)

#### 3.6 Update Existing Endpoints

Replace `X-Customer-ID` header with JWT authentication:

- [ ] Update `app/routers/customers.py`
  - Add `current_user` dependency
  - Customers can only access their own data
  - Admins can access all customers

- [ ] Update `app/routers/claims.py`
  - Add `current_user` dependency
  - Customers can only access their own claims
  - Admins/reviewers can access all claims

- [ ] Update `app/routers/files.py`
  - Add `current_user` dependency
  - Verify file ownership on download
  - Admin override for file access

- [ ] Update `app/routers/admin_claims.py` (from Phase 1)
  - Require `reviewer` or `admin` role
  - Track who made changes

#### 3.7 Security Features

**File**: `app/services/security_service.py` (new)

- [ ] Rate limiting for login attempts
- [ ] Account lockout after failed attempts
- [ ] Suspicious activity detection
- [ ] Email notifications for security events
  - New login from unknown device
  - Password changed
  - Account locked

**File**: `app/models.py` (update)

Add `LoginAttempt` model for security monitoring:

```python
class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### 3.8 Migration Strategy

**Critical**: Migrate existing customers to the new auth system:

- [ ] Create migration script `scripts/migrate_to_auth.py`
  - Generate `User` record for each existing `Customer`
  - Set temporary password (force reset on first login)
  - Send email with instructions
  - Mark all as unverified initially

- [ ] Maintain backward compatibility temporarily
  - Support both `X-Customer-ID` header and JWT for 2 weeks
  - Add deprecation warnings
  - Track usage to ensure migration is complete

### Configuration Updates

**File**: `app/config.py` (update)

```python
# JWT Configuration (already exists, just ensure it's used)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))
JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

# Password Security
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"

# Account Security
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
ACCOUNT_LOCKOUT_DURATION_MINUTES = int(os.getenv("ACCOUNT_LOCKOUT_DURATION_MINUTES", "30"))

# Email Verification
EMAIL_VERIFICATION_REQUIRED = os.getenv("EMAIL_VERIFICATION_REQUIRED", "true").lower() == "true"
EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS = int(os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS", "24"))

# Password Reset
PASSWORD_RESET_TOKEN_EXPIRATION_HOURS = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRATION_HOURS", "1"))
```

### Testing Requirements

- [ ] Test registration flow
- [ ] Test login with valid/invalid credentials
- [ ] Test token refresh
- [ ] Test password reset flow
- [ ] Test email verification
- [ ] Test account lockout after failed attempts
- [ ] Test role-based access control
- [ ] Test token expiration and renewal
- [ ] Test logout and token invalidation

### Success Criteria

- ✅ Users can register and login securely
- ✅ JWT tokens are properly validated
- ✅ Role-based access control is enforced
- ✅ Password reset flow works end-to-end
- ✅ Email verification is required
- ✅ Failed login attempts trigger lockout
- ✅ All existing endpoints use JWT instead of headers
- ✅ Existing customers can migrate to new auth system
- ✅ No regression in existing functionality

---

## Phase 4: Customer Account Management & GDPR Compliance ⬅️ **IN PROGRESS**

**Priority**: HIGH - Required for production launch
**Status**: ⏳ **IN PROGRESS** - ~30% Complete
**Estimated Effort**: 1-2 weeks (including cookie consent implementation)
**Business Value**: Critical - enables customer self-service and GDPR compliance
**Blocking**: Phase 4.6 (Cookie Consent) requires Phase 4.5.14 (HTTP-only cookies) to complete first

### Overview
Implement customer account settings page and GDPR-compliant account deletion workflow. Customers should be able to manage their email, password, and request account deletion.

### Features to Implement

#### 4.1 Account Settings Page (Frontend)

**File**: `frontend_Claude45/src/pages/AccountSettings.tsx` (new)

- [ ] Account settings UI with sections:
  - [ ] Email address change (with verification)
  - [ ] Password change (require current password)
  - [ ] Account deletion request
  - [ ] Display account creation date and last login

#### 4.2 Account Management Endpoints (Backend)

**File**: `app/routers/account.py` (new)

- [ ] `PUT /account/email` - Change email address
  - Require current password for verification
  - Send verification email to new address
  - Update email only after verification
  - Invalidate all existing tokens on email change

- [ ] `PUT /account/password` - Change password
  - Require current password
  - Validate new password strength
  - Invalidate all refresh tokens (force re-login on all devices)
  - Send email notification about password change

- [ ] `POST /account/delete-request` - Request account deletion
  - **DO NOT delete immediately** - create deletion request
  - Blacklist email to prevent login
  - Notify admins via email about deletion request
  - Include user info and open claims count
  - Set deletion_requested_at timestamp

- [ ] `GET /admin/deletion-requests` - List account deletion requests
  - Show pending deletion requests with user details
  - Display open claims count
  - Allow admin to approve/reject deletion

#### 4.3 Database Schema Updates

**File**: `app/models.py` (update)

Add fields to `Customer` model:
```python
# Account deletion fields
deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
deletion_reason = Column(Text, nullable=True)
is_blacklisted = Column(Boolean, default=False)
blacklisted_at = Column(DateTime(timezone=True), nullable=True)
```

Add new `AccountDeletionRequest` model:
```python
class AccountDeletionRequest(Base):
    __tablename__ = "account_deletion_requests"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    email = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="pending")  # pending, approved, rejected
    reviewed_by = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # Snapshot of user data at deletion time
    open_claims_count = Column(Integer, default=0)
    total_claims_count = Column(Integer, default=0)
```

#### 4.4 Email Notifications

**File**: `app/tasks/account_tasks.py` (new)

- [ ] Email to customer: Account deletion requested (confirmation)
- [ ] Email to admins: New account deletion request (with user details and claims count)
- [ ] Email to customer: Email changed (security notification)
- [ ] Email to customer: Password changed (security notification)

#### 4.5 Admin Interface for Deletion Requests

**File**: `frontend_Claude45/src/pages/Admin/DeletionRequests.tsx` (new)

- [ ] List pending deletion requests
- [ ] Show customer details and claims summary
- [ ] Approve/reject deletion with notes
- [ ] Manual data deletion workflow documentation

### 🚨 CRITICAL: GDPR Compliance Requirements

**⚠️ IMPORTANT**: Before production launch, complete GDPR data removal process:

#### Required for GDPR Compliance:
1. **Data Inventory**
   - [ ] Document all customer data stored (database, files, logs, backups)
   - [ ] Map data dependencies (claims, files, notes, status history)
   - [ ] Identify third-party data processors (email service, file storage)

2. **Data Deletion Process**
   - [ ] Create admin workflow to manually delete customer data
   - [ ] Delete/anonymize all customer claims
   - [ ] Delete uploaded files from Nextcloud
   - [ ] Remove from email marketing lists
   - [ ] Anonymize audit logs (replace customer_id with "DELETED_USER")
   - [ ] Document deletion process in admin guide

3. **Data Retention Policy**
   - [ ] Define retention periods for different data types
   - [ ] Keep financial records for 7 years (legal requirement)
   - [ ] Anonymize vs. delete decision tree

4. **Right to Data Portability**
   - [ ] `GET /account/export-data` - Export all customer data as JSON/PDF
   - [ ] Include claims, files metadata, account history
   - [ ] GDPR Article 20 compliance

5. **Privacy Policy & Terms**
   - [ ] Update privacy policy with data deletion process
   - [ ] Document 30-day deletion window
   - [ ] Explain data retention for legal compliance

#### 4.6 Cookie Consent & GDPR Compliance 🍪 **REQUIRED**

**Priority**: CRITICAL - Required before public EU launch
**Status**: ⏳ **PENDING** - Blocked by Phase 4.5.14 (HTTP-only cookie migration)
**Regulation**: GDPR Article 7 (Consent), ePrivacy Directive
**Last Updated**: 2025-12-28

**Overview**:
Once JWT tokens are migrated to HTTP-only cookies (Phase 4.5.14), we MUST implement cookie consent for EU customers before public launch. This is a legal requirement under GDPR and ePrivacy Directive.

**Regulatory Requirements**:
- **GDPR Article 7**: Explicit consent required for non-essential cookies
- **ePrivacy Directive**: Consent required before storing cookies (except strictly necessary)
- **GDPR Recital 32**: Pre-ticked boxes are NOT valid consent
- **Penalties**: Up to €20M or 4% of global annual revenue

**Cookie Classification**:
1. **Strictly Necessary** (No consent required):
   - Session cookies for authenticated users
   - Load balancer cookies
   - Security/fraud prevention cookies

2. **Functionality Cookies** (Consent required):
   - User preference storage (theme, language)
   - Form data persistence

3. **Analytics Cookies** (Consent required):
   - Google Analytics or similar (if implemented)

**JWT Authentication Cookies**:
- **Classification**: Strictly necessary (authentication is core functionality)
- **Consent**: NOT required for authentication cookies (they're essential)
- **Transparency**: MUST still disclose in cookie banner and privacy policy
- **Justification**: Article 6(1)(b) - necessary for contract performance

**Tasks**:

**Frontend Implementation**:
- [ ] Choose cookie consent library
  - **Option A**: Cookie Consent by Osano (free, GDPR-compliant)
  - **Option B**: CookieYes (free tier available)
  - **Option C**: Custom implementation (more work, full control)
- [ ] Implement cookie consent banner UI
  - [ ] Show banner on first visit (before setting any non-essential cookies)
  - [ ] Must have "Accept All" and "Reject All" buttons
  - [ ] Must have "Cookie Settings" for granular control
  - [ ] Banner must be closable after choice
  - [ ] Store consent choice in localStorage or cookie
- [ ] Add cookie settings modal/page
  - [ ] List all cookie categories with descriptions
  - [ ] Toggle switches for each category (strictly necessary should be disabled/always on)
  - [ ] Save preferences button
  - [ ] Link to privacy policy
- [ ] Implement consent enforcement
  - [ ] Only load analytics scripts if user consented
  - [ ] Only set non-essential cookies if user consented
  - [ ] Authentication cookies can be set (strictly necessary)
- [ ] Add "Cookie Settings" link in footer
- [ ] Respect user preferences across sessions

**Backend Configuration**:
- [ ] Categorize all cookies in use
  - [ ] `auth_token` - Strictly necessary (JWT access token)
  - [ ] `refresh_token` - Strictly necessary (JWT refresh token)
  - [ ] Any other application cookies
- [ ] Add cookie policy endpoint `GET /legal/cookies`
  - [ ] Return JSON with all cookie details (name, purpose, duration, type)
  - [ ] Used to populate cookie consent UI

**Legal Documentation**:
- [ ] Create Cookie Policy page (`/legal/cookies`)
  - [ ] List all cookies with: name, purpose, duration, type
  - [ ] Explain strictly necessary vs optional cookies
  - [ ] Link to privacy policy
- [ ] Update Privacy Policy
  - [ ] Add section on cookies and tracking
  - [ ] Explain how to manage cookie preferences
  - [ ] Link to cookie policy
  - [ ] Explain data collected via cookies
- [ ] Add "Cookies" section to terms of service

**Geolocation**:
- [ ] Detect EU visitors (optional but recommended)
  - [ ] Use IP geolocation API (ipapi.co, ip-api.com)
  - [ ] Only show banner to EU visitors
  - [ ] Or show to all visitors (safer approach)
- [ ] Consider showing simplified banner to non-EU visitors

**Testing**:
- [ ] Test banner shows on first visit
- [ ] Test banner doesn't show after consent given
- [ ] Test "Accept All" sets all cookies
- [ ] Test "Reject All" only sets strictly necessary cookies
- [ ] Test cookie settings modal works
- [ ] Test preferences persist across sessions
- [ ] Test authentication works with minimal cookies (reject all)
- [ ] Test analytics don't load if rejected
- [ ] Test "Change Cookie Settings" link in footer

**Recommended Libraries**:

**Option 1: Cookie Consent by Osano** (Recommended - Simple)
```bash
npm install vanilla-cookieconsent
```
- Free and open source
- GDPR compliant out of the box
- Customizable UI
- No external dependencies
- 10KB gzipped

**Option 2: CookieYes** (Hosted Service)
- Free tier available
- Auto-blocking scripts
- Hosted dashboard
- May require account

**Option 3: Custom Implementation**
- Full control over UI/UX
- More development work
- Must ensure GDPR compliance

**Cookie Banner Content** (Example):
```
🍪 We use cookies

We use strictly necessary cookies to keep you signed in and make our
site work. We'd also like to use optional cookies to improve your
experience.

[Cookie Settings] [Reject All] [Accept All]

By clicking "Accept All", you agree to our use of cookies.
See our Cookie Policy and Privacy Policy for more details.
```

**Success Criteria**:
- ✅ Cookie consent banner appears on first visit
- ✅ User can accept, reject, or customize cookie preferences
- ✅ Preferences are saved and respected
- ✅ Authentication works with minimal cookies (strictly necessary only)
- ✅ Cookie policy page exists and is linked from banner
- ✅ Privacy policy updated with cookie information
- ✅ EU compliance verified (legal review recommended)

**Timeline**:
- Implement after Phase 4.5.14 (HTTP-only cookie migration) is complete
- Required before removing OAuth from Cloudflare tunnel
- Blocking requirement for public EU launch

**References**:
- GDPR Cookie Consent Guide: https://gdpr.eu/cookies/
- ePrivacy Directive: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32002L0058
- Cookie Consent Library: https://github.com/orestbida/cookieconsent
- GDPR Article 7: https://gdpr-info.eu/art-7-gdpr/

### Testing Requirements

- [ ] Test email change workflow with verification
- [ ] Test password change and token invalidation
- [ ] Test account deletion request flow
- [ ] Test blacklist prevents login
- [ ] Test admin can view and process deletion requests
- [ ] Test GDPR data export

### Success Criteria

- ✅ Customers can change their email and password
- ✅ Account deletion requests are tracked and require admin approval
- ✅ Blacklisted emails cannot log in
- ✅ Admins receive notification of deletion requests
- ✅ Customer data can be exported for GDPR compliance
- ✅ Clear manual process documented for data deletion
- ✅ Privacy policy updated with deletion process

### Notes

**Why manual deletion approval?**
- Allows admin to verify no open claims/disputes
- Ensures financial records are properly archived
- Prevents accidental data loss
- Complies with legal retention requirements

**Blacklist approach:**
- Immediate effect (user can't login)
- Preserves data temporarily for admin review
- Allows cancellation of deletion request
- Gives time to close open claims

---

## Phase 4.5: Pre-Production Security Fixes 🚨 **BLOCKING DEPLOYMENT**

**Priority**: CRITICAL - MUST complete before production deployment
**Status**: ⏳ **IN PROGRESS** - 93% (13/14 issues resolved)
**Remaining**: JWT Token Storage (localStorage → HTTP-only cookies) - HIGH PRIORITY
**Testing Phase**: Ready for internal testing with Cloudflare tunnel + OAuth
**Post-Testing**: Security headers and HTTPS may need review if removing Cloudflare
**Last Updated**: 2025-12-28

### Overview
Security audit revealed CRITICAL vulnerabilities that MUST be fixed before deploying to production Ubuntu server. These issues were discovered during pre-deployment review on 2025-12-06.

**DEPLOYMENT IS BLOCKED** until all critical issues are resolved.

### 🚨 CRITICAL ISSUES (MUST FIX - Blocking)

#### 4.5.1 SQL Injection Vulnerabilities - CVSS 9.0
**Risk**: Complete database compromise, data exfiltration
**Status**: ✅ **FIXED** (2025-12-06)

**Affected Files**:
- `app/repositories/customer_repository.py` (lines 27-28, 38)
- `app/repositories/admin_claim_repository.py` (lines 71, 90-94)
- `app/repositories/file_repository.py` (lines 169-171)

**Problem**: User input directly interpolated into SQL ILIKE queries using f-strings

**Solution Implemented**: ✅ **Option A** - SQLAlchemy bindparam for parameterized queries

**Tasks**:
- [x] Fix customer_repository.py search functions (search_by_name, search_by_email)
- [x] Fix admin_claim_repository.py search and filter functions (airline filter, search)
- [x] Fix file_repository.py search functions (search_files)
- [ ] Add SQL injection tests
- [ ] Verify fixes with security scan

#### 4.5.2 Exposed Secrets in Repository - CVSS 8.2
**Risk**: Credential exposure, unauthorized access
**Status**: ⚠️ **PARTIALLY FIXED** (2025-12-06)

**Problem**: `.env` file with SMTP password committed to git repository

**Tasks**:
- [x] Remove `.env` from git tracking (`git rm --cached .env`)
- [x] Create `.env.example` template without secrets
- [x] Verify `.env` is in `.gitignore` (already present)
- [x] Document secrets management (see SECURITY_ACTION_REQUIRED.md)
- [ ] **USER ACTION REQUIRED**: Revoke exposed Gmail app password
- [ ] **USER ACTION REQUIRED**: Generate new app-specific password
- [ ] **OPTIONAL**: Remove `.env` from git history with BFG/git-filter-repo

**See**: `SECURITY_ACTION_REQUIRED.md` for detailed rotation instructions

#### 4.5.3 Wildcard CORS Configuration - CVSS 8.1
**Risk**: Cross-origin data theft, CSRF attacks
**Status**: ✅ **FIXED** (2025-12-06)

**Location**: `app/main.py:50`

**Problem**: `allow_origins=["*"]` combined with `allow_credentials=True`

**Solution Implemented**: Changed to `allow_origins=config.CORS_ORIGINS`

**Tasks**:
- [x] Update CORS middleware to use `config.CORS_ORIGINS`
- [x] Remove hardcoded wildcard from main.py
- [ ] Set specific production domains in `.env` for deployment
- [ ] Test CORS with specific origins

#### 4.5.4 Blacklist Bypass in Authentication - CVSS 7.8
**Risk**: Deleted users can still log in, GDPR violation
**Status**: ✅ **FIXED** (2025-12-06)

**Location**: `app/services/auth_service.py`

**Problem**: Blacklisted users can still authenticate

**Solution Implemented**: Added `is_blacklisted` and `is_active` checks to all auth methods

**Tasks**:
- [x] Add `is_blacklisted` check in `login_user` function
- [x] Add `is_active` check in `login_user` function (already existed)
- [x] Add blacklist check in magic link authentication (`verify_magic_link_token`)
- [x] Add `is_active` check in magic link authentication
- [ ] Add blacklist tests
- [ ] Verify blacklisted users cannot log in

### ⚠️ HIGH PRIORITY ISSUES (Fix Before Launch)

#### 4.5.5 Missing Rate Limiting - CVSS 7.3
**Risk**: Brute force attacks, account enumeration
**Status**: ✅ **FIXED** (2025-12-07)

**Solution Implemented**: ✅ **Custom in-memory rate limiter with Cloudflare support**

**Implementation Details**:
- Created custom `simple_rate_limit()` function in `app/routers/auth.py`
  - Reads CF-Connecting-IP header (Cloudflare's real client IP)
  - Falls back to X-Forwarded-For, then direct IP
  - Fixed window rate limiting (in-memory, can be upgraded to Redis)
  - Returns HTTP 429 when rate limit exceeded
- Applied rate limits to all critical auth endpoints
- Tested successfully with 7 sequential requests (5 allowed, 2 blocked)

**Tasks**:
- [x] Choose rate limiting approach (custom implementation)
- [x] Implement rate limits on `/auth/login` (5/minute)
- [x] Implement rate limits on `/auth/register` (3/hour)
- [x] Implement rate limits on `/auth/password/reset-request` (3/15minutes)
- [x] Test rate limits (verified: requests 1-5 allowed, 6-7 blocked with HTTP 429)

#### 4.5.6 Missing HTTPS Configuration - CVSS 7.4
**Risk**: Man-in-the-middle attacks, credential interception
**Status**: ✅ **HANDLED BY CLOUDFLARE** (Testing Phase)

**Current Setup**:
- Cloudflare Tunnel handles HTTPS termination
- OAuth authentication required to access through Cloudflare
- Only accessible to team during testing phase

**Future (Post-Testing)**:
- [ ] May need direct HTTPS if removing Cloudflare (GDPR considerations)
- [ ] Obtain SSL certificate (Let's Encrypt recommended)
- [ ] Update nginx.conf with SSL configuration
- [ ] Add HTTP -> HTTPS redirect
- [ ] Configure SSL protocols (TLSv1.2, TLSv1.3 only)
- [ ] Add HSTS header
- [ ] Update `CORS_ORIGINS` to use https://
- [ ] Test SSL with SSL Labs

#### 4.5.7 Password Strength Inconsistency - CVSS 6.5
**Risk**: Weak passwords via account settings
**Status**: ✅ **N/A - NOT APPLICABLE**

**Reason**: Application uses **passwordless authentication** (magic links only)
- No password registration or storage
- Users authenticate via email magic links
- No password strength requirements needed
- This security issue does not apply to this application

#### 4.5.8 Security Headers Disabled - CVSS 6.5
**Risk**: XSS, clickjacking, MIME-sniffing attacks
**Status**: ⏸️ **DEFERRED - Cloudflare handles during testing**

**Current Setup (Testing Phase)**:
- Cloudflare Tunnel provides HTTPS and can add security headers
- OAuth authentication protects test environment
- Headers can be configured in Cloudflare dashboard (Transform Rules)

**Future Implementation (Post-Testing, if removing Cloudflare)**:
- [ ] **Decision Required**: Choose implementation approach
  - **Option A**: Create SecurityHeadersMiddleware in FastAPI
  - **Option B**: Configure in nginx reverse proxy
- [ ] Add security headers:
  - HSTS (Strict-Transport-Security)
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - Content-Security-Policy
  - X-XSS-Protection
- [ ] Test header presence with curl
- [ ] Verify CSP doesn't break frontend functionality

**Note**: May be required if removing Cloudflare for GDPR compliance

### 📋 MEDIUM PRIORITY (Hardening)

#### 4.5.9 Development Secrets in Config
- [ ] Remove default passwords from config.py
- [ ] Add production config validation
- [ ] Fail fast if production secrets missing

#### 4.5.10 Missing Database Connection Pool Limits
- [ ] Configure pool_size=20 in database.py
- [ ] Add max_overflow=10
- [ ] Add pool_timeout=30
- [ ] Add pool_recycle=3600

#### 4.5.11 Insufficient Security Audit Logging
- [ ] Create security logger
- [ ] Log failed login attempts
- [ ] Log successful logins with IP
- [ ] Log admin privilege changes
- [ ] Configure log rotation

#### 4.5.12 Missing Input Sanitization for XSS
- [ ] Install bleach library
- [ ] Sanitize claim notes
- [ ] Sanitize customer names in emails
- [ ] Escape HTML in email templates

#### 4.5.13 Admin Email Configuration
- [ ] Add `ADMIN_EMAIL` to .env
- [ ] Update account deletion notifications
- [ ] Update error notifications

#### 4.5.14 JWT Token Storage Security - CVSS 8.1 🔒 **NEW**
**Risk**: XSS attacks can steal JWT tokens from localStorage
**Status**: ⏳ **PENDING** - Migration to HTTP-only cookies required
**Priority**: HIGH - Should complete before public launch
**Last Updated**: 2025-12-28

**Problem**: JWT tokens (access & refresh) currently stored in localStorage
- **Current Implementation**: `frontend_Claude45/src/utils/tokenStorage.ts` uses localStorage
- **Vulnerability**: JavaScript (including malicious XSS scripts) can access localStorage
- **Impact**: If XSS vulnerability exists, attackers can steal tokens and impersonate users

**Affected Files**:
- `frontend_Claude45/src/utils/tokenStorage.ts` - Token storage utility
- `frontend_Claude45/src/services/auth.ts` - Auth service (reads from localStorage)
- `frontend_Claude45/src/services/api.ts` - API client (reads from localStorage)
- `frontend_Claude45/src/pages/*.tsx` - Multiple pages access localStorage directly
- `app/routers/auth.py` - Backend needs to set cookies instead of returning JSON tokens

**Solution**: Migrate to HTTP-only cookies
- **Backend Changes**: Set cookies in response instead of returning tokens in JSON body
- **Frontend Changes**: Remove localStorage usage, rely on automatic cookie transmission
- **Configuration**: Set `httpOnly=True`, `secure=True`, `samesite='lax'`

**Tasks**:
- [ ] **Backend**: Update `/auth/login` to set HTTP-only cookies instead of JSON response
- [ ] **Backend**: Update `/auth/refresh` to set HTTP-only cookies
- [ ] **Backend**: Update `/auth/logout` to clear cookies
- [ ] **Backend**: Add cookie configuration (secure, httpOnly, samesite, domain, path)
- [ ] **Frontend**: Remove `tokenStorage.ts` utility
- [ ] **Frontend**: Update API client to use `credentials: 'include'` in all requests
- [ ] **Frontend**: Remove all localStorage.getItem('auth_token') calls
- [ ] **Frontend**: Update auth service to not store tokens locally
- [ ] **Frontend**: Remove token from login/register response handling
- [ ] **Config**: Update CORS to allow credentials from specific origins
- [ ] **Config**: Set cookie domain for production (eac.dvvcloud.work)
- [ ] **Testing**: Verify cookies are set on login
- [ ] **Testing**: Verify cookies are sent automatically on API requests
- [ ] **Testing**: Verify cookies cannot be accessed via JavaScript (document.cookie)
- [ ] **Testing**: Verify logout clears cookies
- [ ] **Testing**: Verify refresh token flow works with cookies
- [ ] **Security**: Add CSP headers to further protect against XSS
- [ ] **Documentation**: Update JWT_SECURITY_EXPLAINED.md with implementation status

**Reference Documentation**:
- See `docs/JWT_SECURITY_EXPLAINED.md` for detailed explanation and migration guide
- Security checklist in JWT_SECURITY_EXPLAINED.md:464-472

**GDPR Consideration**:
- ⚠️ After migrating to cookies, must implement cookie consent banner for EU compliance
- See Phase 4.6 for cookie consent implementation details
- Required before public launch in EU markets

**Version**: This should trigger v0.3.1 release (security patch)

### Success Criteria

Before deployment is approved:

- [ ] ✅ All 4 CRITICAL issues resolved
- [ ] ✅ All 4 HIGH priority issues resolved
- [ ] ✅ Security scan shows no critical/high vulnerabilities
- [ ] ✅ Penetration testing completed
- [ ] ✅ SSL certificate installed and tested
- [ ] ✅ Rate limiting verified with load testing
- [ ] ✅ CORS tested with production domains
- [ ] ✅ Blacklist enforcement verified
- [ ] ✅ All secrets rotated and secured
- [ ] ✅ Production .env file created (not committed)
- [ ] ✅ Deployment checklist completed

### Testing Requirements

**Security Testing**:
```bash
# SQL injection testing
sqlmap -u "http://localhost:8000/api/customers?name=test" --batch

# Dependency vulnerabilities
safety check

# OWASP ZAP scan
docker run -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:8000

# SSL testing
ssllabs.com scan
```

**Manual Testing**:
- [ ] Attempt SQL injection in all search fields
- [ ] Test CORS with different origins
- [ ] Attempt login with blacklisted user
- [ ] Brute force login (should rate limit after 5 attempts)
- [ ] Test weak passwords (should reject <12 chars)
- [ ] Verify JWT expiration enforcement
- [ ] Test refresh token rotation

### Deployment Readiness Checklist

**Configuration**:
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `SECRET_KEY` = 64+ char unique value
- [ ] `FILE_ENCRYPTION_KEY` = Fernet key (backed up)
- [ ] `DATABASE_URL` = production PostgreSQL
- [ ] `REDIS_URL` = production Redis
- [ ] `NEXTCLOUD_URL` = production instance
- [ ] `NEXTCLOUD_PASSWORD` != default
- [ ] `CORS_ORIGINS` = specific domains only (https://)
- [ ] `SECURITY_HEADERS_ENABLED=true`
- [ ] `SMTP_*` credentials rotated
- [ ] `ADMIN_EMAIL` configured

**Infrastructure**:
- [ ] Ubuntu server prepared
- [ ] Docker and docker-compose installed
- [ ] Firewall configured (22, 80, 443)
- [ ] SSL certificate obtained
- [ ] nginx configured with HTTPS
- [ ] Database backups configured
- [ ] Log rotation configured
- [ ] Monitoring setup (optional but recommended)

**Documentation**:
- [ ] Production deployment guide created
- [ ] Secrets management documented
- [ ] Incident response plan created
- [ ] GDPR data deletion workflow documented

### Estimated Timeline

- **Day 1 (4-8 hours)**: Fix 4 critical issues
  - SQL injection fixes (2-3 hours)
  - Secret rotation (1 hour)
  - CORS configuration (30 min)
  - Blacklist enforcement (1 hour)
  - Testing (2-3 hours)

- **Day 2 (4-8 hours)**: Fix high priority issues
  - Rate limiting (2 hours)
  - HTTPS configuration (2 hours)
  - Password consistency (1 hour)
  - Security headers (1 hour)
  - Testing (2 hours)

- **Day 3 (Optional)**: Medium priority hardening
  - Audit logging (2 hours)
  - XSS sanitization (2 hours)
  - Additional testing (2 hours)

**Total**: 1-3 days depending on priority level

### Notes

**Why This Phase is Critical**:
- Application has good architecture and features
- Security fundamentals are in place (JWT, bcrypt, file encryption)
- Only specific vulnerabilities need patching
- Without fixes, production deployment would be **irresponsible and dangerous**

**Post-Fix Benefits**:
- Production-ready security posture
- GDPR compliant
- Protection against common attacks
- Professional security standards
- Multi-user concurrent access safe

---

## Phase 5: Multi-Passenger Claims (Family/Group Claims)

**Priority**: HIGH - Major UX improvement and revenue opportunity
**Status**: 📋 **PLANNED** - Not yet implemented
**Estimated Effort**: 3.5-5 weeks (18-27 days)
**Business Value**: HIGH - Increases average order value and customer satisfaction
**📄 Detailed Planning**: See [docs/MULTI_PASSENGER_CLAIMS.md](docs/MULTI_PASSENGER_CLAIMS.md)

### Overview

Allow a single account holder (e.g., a parent) to submit multiple related claims for different passengers (e.g., family members) on the same flight. This addresses a critical use case where families traveling together need to file separate claims while managing everything from one account.

### Business Case

**Problem**: A parent with 4 family members on a delayed flight must currently:
- Submit 4 separate claims individually
- Re-enter the same flight information 4 times
- Re-enter the same address 4 times
- Manage 4 disconnected claims

**Solution**: Multi-passenger claim submission allowing:
- One-time flight and eligibility check
- Add multiple passengers to the same claim group
- Shared account holder information
- Separate claim processing per passenger
- Grouped view for both customers and admins

**Expected Impact**:
- **Increased Conversions**: 15-25% higher completion rate for family travelers
- **Higher Average Order Value**: 4 claims instead of 1 (4x compensation)
- **Reduced Support Costs**: Fewer questions about linking claims
- **Competitive Advantage**: Most competitors don't offer this feature
- **Better Admin Efficiency**: Process family claims together, share flight eligibility verification

### Key Features

#### 5.1 Customer Features
- **Claim Type Selection**: Choose single or multi-passenger claim at start
- **Add Multiple Passengers**: Repeatable form to add each family member
  - First/Last Name
  - Date of Birth
  - Relationship (self, spouse, child, parent, other)
  - Checkbox to share address (default: checked)
  - Document upload per passenger
- **Group Management**: View all grouped claims together in dashboard
- **Shared Information**: Flight details, address entered once
- **Individual Tracking**: Each claim has own status and compensation

#### 5.2 Admin Features
- **Claim Groups View**: New admin page to view grouped claims
- **Bulk Actions**: Approve all, request info from all
- **Group Notes**: Add notes visible across all claims in group
- **Efficiency Dashboard**: See processing time savings from grouping
- **Individual Override**: Can process each claim separately if needed

#### 5.3 Database Changes
- New table: `claim_groups` (links claims together)
- New table: `claim_group_notes` (admin notes for groups)
- Modified `claims` table: Add `claim_group_id`, passenger details
- All changes backward compatible with single claims

### Success Metrics

**Adoption Metrics** (6 months post-launch):
- Target: 20% of claims submitted as grouped
- Target: Average 3 passengers per group
- Target: 95% completion rate for grouped claims

**Business Metrics**:
- Target: 25% increase in average compensation per customer
- Target: 30% reduction in admin processing time for family claims

### Implementation Phases

1. **Backend Foundation** (3-5 days): Database models, repositories, services
2. **Single Claim Group API** (2-3 days): Core API endpoints
3. **Frontend Multi-Passenger Form** (5-7 days): Wizard with passenger addition
4. **Customer Dashboard** (2-3 days): View grouped claims
5. **Admin Interface** (4-6 days): Manage and process grouped claims
6. **Notifications & Polish** (2-3 days): Email templates, testing

### GDPR & Compliance

- Account holder must confirm permission to file on behalf of others
- Consent checkbox required: "I confirm I have permission to file claims for these passengers"
- Passengers can claim ownership of their claim later if they register
- Data deletion of account holder should NOT delete passenger claims

### Technical Considerations

- All claims in group must share same flight_number and flight_date
- Passenger details must be unique within a group (no duplicates)
- Bulk operations must be atomic (all succeed or all fail)
- Each claim maintains independent status (can approve some, reject others)

### Open Questions

1. **Maximum Group Size**: Limit to 10 passengers? (Reasonable for family/small group)
2. **Group Naming**: Auto-generate (e.g., "Smith Family - AB1234") or let user customize?
3. **Payment Splitting**: Should we support different bank accounts per passenger?
4. **Historical Migration**: Can customers group existing claims retroactively?
5. **Pricing Impact**: Charge per claim or per group? (Currently: commission-based, no change needed)

### Next Steps

- [ ] Product team review and approval
- [ ] Design UI mockups for multi-passenger flow
- [ ] User research interviews with family travelers
- [ ] Technical spike on database performance
- [ ] Prioritize against other Phase 5+ features

---

## Future Enhancements (Post-MVP)

These are not prioritized but documented for future reference:

### Payment Integration
- Integrate Stripe or PayPal for compensation disbursement
- Support multiple payment methods (bank transfer, PayPal, check)
- Track payment status and history
- Generate payment receipts

### OCR & Data Extraction
- Extract flight details from boarding passes automatically
- Extract personal info from ID documents
- Reduce manual data entry
- Validate extracted data against user input

### Customer Portal (Frontend)
- React/Vue.js single-page application
- Customer dashboard showing claim status
- Document upload interface with drag-and-drop
- Real-time notifications
- Mobile-responsive design

### Analytics & Reporting
- Admin dashboard with metrics
- Claim success rate by airline
- Average processing time
- Revenue tracking
- Document rejection reasons
- Export reports to PDF/Excel

### Multi-language Support
- i18n for all customer-facing content
- Support EU languages (EN, DE, FR, ES, IT)
- Automatic language detection from browser
- Email templates in multiple languages

### API Integrations
- Integrate with flight data APIs (FlightAware, Aviation Edge)
- Verify flight delay/cancellation automatically
- Get real-time flight status
- Validate airport codes

### Advanced Security
- Two-factor authentication (2FA)
- OAuth2 integration (Google, Facebook login)
- API key management for third-party integrations
- Advanced fraud detection

---

## Technical Debt & Infrastructure

These should be addressed alongside feature development:

### Database Migrations
- [ ] Set up Alembic properly
- [ ] Remove `create_all()` from lifespan manager
- [ ] Create initial migration from current schema
- [ ] Document migration process

### Testing
- [ ] Increase test coverage to 80%+
- [ ] Add integration tests for all new features
- [ ] Set up continuous testing with pytest-watch
- [ ] Performance testing for file upload/download

### CI/CD
- [ ] Set up GitHub Actions or GitLab CI
- [ ] Automated testing on pull requests
- [ ] Automated deployment to staging
- [ ] Code quality checks (black, pylint, mypy)

### Monitoring & Logging
- [ ] Structured logging with JSON format
- [ ] Centralized log aggregation (ELK stack or CloudWatch)
- [ ] Application performance monitoring (New Relic, DataDog)
- [ ] Error tracking (Sentry)
- [ ] Uptime monitoring

### Documentation
- [ ] API documentation with examples
- [ ] Admin user guide
- [ ] Customer user guide
- [ ] Developer onboarding guide
- [ ] Deployment guide

---

## Notes for Future Claude Sessions

### Getting Started

1. Read `CLAUDE.md` for codebase architecture overview
2. Read this `ROADMAP.md` to understand current priorities
3. Check the status of each phase before starting work
4. Update the status as you complete tasks

### Development Workflow

1. Create feature branch: `git checkout -b feature/admin-dashboard`
2. Implement features incrementally (one endpoint at a time)
3. Write tests as you go
4. Update this roadmap with progress
5. Commit frequently with descriptive messages
6. Test thoroughly before marking as complete

### Key Principles

- **Business value first**: Focus on features that enable revenue
- **Incremental delivery**: Ship small, working increments
- **Test coverage**: Every new feature needs tests
- **Backward compatibility**: Don't break existing functionality
- **Security by default**: Every endpoint needs proper authorization
- **Documentation**: Update docs as you build

### Current Architecture Patterns to Follow

- Use repository pattern for all database access
- Use service layer for business logic
- Keep routers thin (delegate to services)
- Use async/await throughout
- Follow existing error handling patterns
- Use Pydantic for request/response validation
- Add proper logging at service level

### Questions to Ask

Before starting work on any phase, consider:

1. Does this require database schema changes? (Create migration)
2. Does this need new environment variables? (Update config.py and .env.example)
3. Does this affect existing endpoints? (Test for regressions)
4. Does this need new tests? (Always yes)
5. Does this require documentation updates? (Usually yes)
6. Does this need Celery tasks? (Phase 2 onwards)
7. Does this require specific roles? (Phase 3 onwards)

---

**End of Roadmap**

Last updated: 2025-10-29
Maintained by: Development Team
Next review: After completing Phase 1
