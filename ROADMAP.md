# Development Roadmap

**Last Updated**: 2025-12-06
**Current Version**: v0.3.0 (Phase 3 Complete, Phase 4 In Progress)
**Status**: MVP Phase - Customer Account Management & GDPR Compliance 🔐
**Strategy**: Business value first (#2 → #3 → #4 → GDPR)

This roadmap outlines the next development phases for the flight claim management platform, prioritized for MVP launch.

---

## 🎯 NEXT STEPS - START HERE

**Current State**: Security Hardening In Progress 🔒 (v0.3.0+)
- ✅ Admin Dashboard & Claim Workflow (Phase 1)
- ✅ Async Task Processing & Email Notifications (Phase 2)
- ✅ JWT Authentication & Authorization System (Phase 3) 🎉
- ⏳ Customer Account Management & GDPR Compliance (Phase 4) - 80% Complete
- ⏳ **Pre-Production Security Fixes (Phase 4.5)** - 56% Complete ⬅️ **IN PROGRESS**
  - ✅ SQL Injection fixed
  - ✅ CORS Wildcard fixed
  - ✅ Blacklist Bypass fixed
  - ✅ Rate Limiting fixed (with Cloudflare support)
  - ⚠️ SMTP Credentials (user action required)
  - ⏳ HTTPS, Password Consistency, Security Headers (remaining)

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

**Next Priority**: Frontend Integration or Payment Integration (Phase 4 or Phase 5)

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
**Estimated Effort**: 1 week
**Business Value**: Critical - enables customer self-service and GDPR compliance

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
**Status**: ⏳ **IN PROGRESS** - 67% Complete (6/9 Critical+High issues resolved)
**Estimated Effort**: 1 day remaining
**Deadline**: BEFORE any production deployment
**Last Updated**: 2025-12-07 (09:37 UTC)

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
**Status**: ❌ Not Fixed

**Tasks**:
- [ ] Obtain SSL certificate (Let's Encrypt recommended)
- [ ] Update nginx.conf with SSL configuration
- [ ] Add HTTP -> HTTPS redirect
- [ ] Configure SSL protocols (TLSv1.2, TLSv1.3 only)
- [ ] Add HSTS header
- [ ] Update `CORS_ORIGINS` to use https://
- [ ] Test SSL with SSL Labs

#### 4.5.7 Password Strength Inconsistency - CVSS 6.5
**Risk**: Weak passwords via account settings
**Status**: ❌ Not Fixed

**Problem**: Registration requires 12 chars, account change only 8

**Tasks**:
- [ ] Update `app/routers/account.py:162` to require 12 chars
- [ ] Update `app/schemas/account_schemas.py` min_length to 12
- [ ] Add complexity validator to account password change
- [ ] Add tests for password strength validation

#### 4.5.8 Security Headers Disabled - CVSS 6.5
**Risk**: XSS, clickjacking, MIME-sniffing attacks
**Status**: ❌ Not Fixed

**Decision Required**: Choose security headers implementation:
- [ ] **Option A**: Create SecurityHeadersMiddleware
- [ ] **Option B**: Use existing middleware if available
- [ ] **Option C**: Configure in nginx

**Tasks**:
- [ ] Check if security middleware exists
- [ ] Create/activate security headers middleware
- [ ] Set `SECURITY_HEADERS_ENABLED=true` for production
- [ ] Add headers: HSTS, X-Frame-Options, CSP, etc.
- [ ] Test header presence with curl

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
