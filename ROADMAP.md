# Development Roadmap

**Last Updated**: 2025-10-30
**Current Version**: v0.2.0
**Status**: MVP Phase - Phase 2 Complete
**Strategy**: Business value first (#2 → #3 → #1)

This roadmap outlines the next development phases for the flight claim management platform, prioritized for MVP launch.

---

## 🎯 NEXT STEPS - START HERE

**Current State**: Phase 2 Complete (v0.2.0)
- ✅ Admin Dashboard & Claim Workflow (Phase 1)
- ✅ Async Task Processing & Email Notifications (Phase 2)

**Next Phase**: **Phase 3 - Authentication & Authorization System**

**Target Version**: v0.3.0

**What to Implement Next**:
1. JWT-based authentication system (replace X-Customer-ID and X-Admin-ID headers)
2. User registration and login endpoints
3. Password reset flow with email verification
4. Role-based access control (RBAC) for customers and admins
5. Protected routes with JWT middleware
6. Token refresh mechanism
7. Admin user management

**Why Phase 3 Next**:
- Currently using header-based authentication (X-Customer-ID, X-Admin-ID) which is insecure
- Required before public launch or adding customer-facing frontend
- Enables proper multi-user support and security
- Foundation for future features (user profiles, permissions, audit trails)

**Estimated Effort**: 2-3 weeks (or 1-2 sessions depending on complexity)

**Key Files to Create**:
- `app/routers/auth.py` - Authentication endpoints
- `app/services/auth_service.py` - JWT token management
- `app/services/password_service.py` - Password hashing and validation
- `app/middleware/jwt_middleware.py` - JWT authentication middleware
- `app/models.py` - Add User, RefreshToken, PasswordReset models

**See Phase 3 section below for complete feature list and implementation details.**

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
**Status**: ✅ **COMPLETED** (2025-10-30)
**Estimated Effort**: 1-2 weeks
**Actual Effort**: 1 session
**Business Value**: High - improves UX and enables automation

**📄 See [PHASE2_SUMMARY.md](PHASE2_SUMMARY.md) for complete implementation details.**
**📖 See [PHASE2_TESTING_GUIDE.md](PHASE2_TESTING_GUIDE.md) for testing guide.**

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

## Phase 3: Authentication & Authorization System ⬅️ **NEXT PHASE**

**Priority**: HIGH - Required before public launch
**Status**: 🔜 **NOT STARTED** - Next to implement
**Estimated Effort**: 2-3 weeks
**Target Version**: v0.3.0
**Business Value**: Critical for security and public launch

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
