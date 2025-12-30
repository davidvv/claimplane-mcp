# Phase 2: Async Task Processing & Notification System

[← Back to Roadmap](README.md)

---

**Priority**: HIGH
**Status**: ✅ **COMPLETED** (2025-11-02)
**Estimated Effort**: 1-2 weeks
**Actual Effort**: 2 sessions (implementation + bug fixes)
**Business Value**: High - improves UX and enables automation

**📄 Documentation:**
- [PHASE2_SUMMARY.md](../PHASE2_SUMMARY.md) - Complete implementation details
- [PHASE2_COMPLETION.md](../PHASE2_COMPLETION.md) - Final completion report with test results
- [Testing Guide](../docs/testing/PHASE2_TESTING_GUIDE.md) - Detailed testing procedures

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

**Note**: This phase is complete. The checkboxes below represent the original planning requirements and are kept for historical reference.

---

## Overview

Implemented asynchronous task processing using Celery and built a comprehensive email notification system to keep customers informed about their claim status throughout the lifecycle.

---

## Features to Implement

### 2.1 Celery Setup

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

### 2.2 Email Service

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

### 2.3 Notification System

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

### 2.4 Background Tasks

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

### 2.5 Webhook System (Optional)

**File**: `app/services/webhook_service.py` (new)

- [ ] Allow customers to register webhook URLs
- [ ] Send claim status updates to webhooks
- [ ] Retry failed webhook deliveries
- [ ] Webhook authentication (HMAC signatures)

### 2.6 Integration Points

Update existing code to trigger notifications:

- [ ] `app/routers/claims.py` - Send notification on claim submission
- [ ] `app/routers/admin_claims.py` - Send notification on status change
- [ ] `app/routers/admin_files.py` - Send notification on document rejection
- [ ] `app/services/file_service.py` - Queue virus scan task after upload

---

## Configuration Updates

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

---

## Testing Requirements

- [ ] Test email sending with different templates
- [ ] Test Celery task execution and retries
- [ ] Test notification preferences
- [ ] Test scheduled tasks
- [ ] Test failure scenarios (email bounce, task failure)

---

## Success Criteria

- ✅ Customers receive email when claim is submitted
- ✅ Customers receive email when status changes
- ✅ Heavy operations (virus scan, OCR) run in background
- ✅ Failed tasks are retried automatically
- ✅ Scheduled tasks run on time
- ✅ Email templates are professional and branded

---

[← Back to Roadmap](README.md)
