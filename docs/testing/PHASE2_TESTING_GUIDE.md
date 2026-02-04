# Phase 2 - Complete Testing Guide

**Last Updated**: 2025-10-30
**Phase**: Email Notifications & Async Task Processing
**Difficulty**: Beginner-friendly

---

## Table of Contents

1. [What We're Testing](#what-were-testing)
2. [Prerequisites](#prerequisites)
3. [Setup Gmail SMTP (Step-by-Step)](#setup-gmail-smtp-step-by-step)
4. [Setup Email Configuration](#setup-email-configuration)
5. [Install Dependencies](#install-dependencies)
6. [Start the Services](#start-the-services)
7. [Test 1: Claim Submitted Email](#test-1-claim-submitted-email)
8. [Test 2: Status Update Email](#test-2-status-update-email)
9. [Test 3: Document Rejected Email](#test-3-document-rejected-email)
10. [Monitor Celery Tasks](#monitor-celery-tasks)
11. [Troubleshooting](#troubleshooting)
12. [Understanding the "From" Address](#understanding-the-from-address)

---

## What We're Testing

Phase 2 implements automated email notifications. We'll test:

✅ **Claim Submitted Email** - Customer receives confirmation when they submit a claim
✅ **Status Update Email** - Customer notified when claim status changes
✅ **Document Rejected Email** - Customer asked to re-upload rejected documents
✅ **Background Processing** - Emails sent asynchronously via Celery
✅ **Retry Logic** - Failed emails automatically retry

---

## Prerequisites

Before starting, ensure you have:

- [ ] ClaimPlane conda environment activated
- [ ] Gmail account (or any email account for testing)
- [ ] Docker installed (for Redis service)
- [ ] Terminal access
- [ ] Text editor for `.env` file

**Time Required**: ~30 minutes for first-time setup, ~5 minutes for subsequent tests

---

## Setup Gmail SMTP (Step-by-Step)

### Why Gmail?

Gmail is perfect for development/testing:
- Free
- Easy to set up
- Reliable
- 500 emails/day limit (plenty for testing)

### Step 1: Create App Password (Not Your Regular Password!)

**IMPORTANT**: Gmail requires an "App Password" for external apps. DO NOT use your regular Gmail password.

1. **Go to Google Account Settings**:
   - Visit: https://myaccount.google.com/
   - Or click your profile picture → "Manage your Google Account"

2. **Enable 2-Step Verification** (if not already enabled):
   - Left sidebar → Security
   - Scroll to "How you sign in to Google"
   - Click "2-Step Verification"
   - Follow the prompts to enable it

3. **Create App Password**:
   - After 2-Step is enabled, go back to Security
   - Scroll to "How you sign in to Google"
   - Click "App passwords" (or visit https://myaccount.google.com/apppasswords)
   - Select app: "Mail"
   - Select device: "Other" → Type "Flight Claim System"
   - Click "Generate"
   - **Copy the 16-character password** (example: `abcd efgh ijkl mnop`)
   - You'll use this as your `SMTP_PASSWORD`

**Can't find App Passwords?**
- Make sure 2-Step Verification is enabled first
- Make sure you're logged into the correct Google account
- Try the direct link: https://myaccount.google.com/apppasswords

### Step 2: Test Your Gmail Credentials

Keep your Gmail email and app password handy. We'll use them in the next section.

---

## Setup Email Configuration

### Create .env File

In your project root (`/Users/david/Documents/Proyectos/flight_claim/`), create a `.env` file:

```bash
# Navigate to project directory
cd /Users/david/Documents/Proyectos/flight_claim

# Create .env file
touch .env

# Open in text editor
nano .env
# Or use VS Code: code .env
# Or use any text editor
```

### Add Email Configuration

Copy and paste this into `.env` file, **replacing the placeholders**:

```bash
# ===== EMAIL CONFIGURATION (PHASE 2) =====

# Gmail SMTP Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail-address@gmail.com        # ← Change this!
SMTP_PASSWORD=abcd efgh ijkl mnop                 # ← Change this! (16-char app password)

# Email "From" Address (can be anything!)
SMTP_FROM_EMAIL=noreply@claimplane.com          # ← This is what customers see
SMTP_FROM_NAME=ClaimPlane Support

# Email Settings
SMTP_USE_TLS=true
NOTIFICATIONS_ENABLED=true

# ===== DATABASE CONFIGURATION =====
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/flight_claim

# ===== REDIS CONFIGURATION =====
REDIS_URL=redis://localhost:6379

# ===== SECURITY =====
SECRET_KEY=development-secret-key-change-in-production
FILE_ENCRYPTION_KEY=your-encryption-key-from-generate-secrets-script

# ===== OTHER SETTINGS =====
ENVIRONMENT=development
```

**Replace These Values**:
- `SMTP_USERNAME`: Your full Gmail address (e.g., `john.doe@gmail.com`)
- `SMTP_PASSWORD`: The 16-character app password from Step 1 (e.g., `abcd efgh ijkl mnop`)
- `SMTP_FROM_EMAIL`: The address customers will see (can be anything, like `noreply@claimplane.com`)
- `SMTP_FROM_NAME`: The name customers will see (e.g., "ClaimPlane Support")

**Save the file** (Ctrl+O in nano, then Ctrl+X to exit)

### Verify .env File

```bash
# Check if .env exists
ls -la .env

# View contents (without showing password)
cat .env | grep SMTP_HOST
# Should show: SMTP_HOST=smtp.gmail.com
```

---

## Install Dependencies

Activate your conda environment and install new packages:

```bash
# Activate environment
source /Users/david/miniconda3/bin/activate ClaimPlane

# Verify environment
which python
# Should show: /Users/david/miniconda3/envs/ClaimPlane/bin/python

# Install new dependencies
pip install -r requirements.txt

# Verify installations
pip list | grep aiosmtplib
# Should show: aiosmtplib 3.0.1

pip list | grep jinja2
# Should show: jinja2 3.1.2
```

**Expected output**: No errors, packages installed successfully.

---

## Start the Services

You have two options for running the services:

### **Option A: Local Development (Recommended for Learning)**

This runs everything locally so you can see logs in real-time.

**Terminal 1: Start Database & Redis**
```bash
# Start PostgreSQL and Redis via Docker
docker-compose up db redis -d

# Verify services are running
docker ps
# Should show: flight_claim_db and flight_claim_redis
```

**Terminal 2: Start API**
```bash
# Activate environment
source /Users/david/miniconda3/bin/activate ClaimPlane

# Start FastAPI
python app/main.py

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

**Terminal 3: Start Celery Worker** ⭐ **This is where the magic happens!**
```bash
# Activate environment
source /Users/david/miniconda3/bin/activate ClaimPlane

# Start Celery worker
celery -A app.celery_app worker --loglevel=info

# You should see:
# -------------- celery@YourMachineName v5.3.4 (emerald-rush)
# --- ***** -----
# -- ******* ---- Darwin-25.0.0-x86_64-64bit 2025-10-30 ...
# - *** --- * ---
# - ** ---------- [config]
# - ** ---------- .> app:         flight_claim_worker:0x...
# - ** ---------- .> transport:   redis://localhost:6379//
# - ** ---------- .> results:     redis://localhost:6379/
# - *** --- * --- .> concurrency: 8 (prefork)
# -- ******* ----
# --- ***** -----
#
# [tasks]
#   . send_claim_submitted_email
#   . send_document_rejected_email
#   . send_status_update_email
#
# [2025-10-30 10:30:00,123: INFO/MainProcess] Connected to redis://localhost:6379//
# [2025-10-30 10:30:00,456: INFO/MainProcess] mingle: searching for neighbors
# [2025-10-30 10:30:01,789: INFO/MainProcess] mingle: all alone
# [2025-10-30 10:30:02,012: INFO/MainProcess] celery@YourMachineName ready.
```

**Look for these lines in Celery output**:
- `[tasks]` section should list 3 tasks ✅
- `Connected to redis` ✅
- `celery@... ready` ✅

**Keep all 3 terminals open!** You'll watch the Celery worker process tasks in real-time.

---

### **Option B: Full Docker Compose (Easier, Less Visible)**

This runs everything in Docker, including the Celery worker.

```bash
# Start all services
docker-compose up -d

# Check all services are running
docker ps
# Should show: api, db, redis, celery_worker, nginx

# View Celery worker logs
docker logs flight_claim_celery_worker -f
```

**For this guide, we'll use Option A** (local development) so you can see exactly what's happening.

---

## Test 1: Claim Submitted Email

This tests the email sent when a customer submits a new claim.

### Step 1: Open Swagger UI

1. Open browser: http://localhost:8000/docs
2. You should see the FastAPI interactive API documentation

### Step 2: Create a Test Customer (If Needed)

If you don't have a customer yet:

1. Find `POST /customers/` endpoint
2. Click "Try it out"
3. Enter customer data:
```json
{
  "email": "your-actual-email@gmail.com",
  "first_name": "Test",
  "last_name": "Customer",
  "phone": "+1234567890",
  "address": {
    "street": "123 Test St",
    "city": "Test City",
    "postalCode": "12345",
    "country": "USA"
  }
}
```
4. Click "Execute"
5. **Copy the `id` from the response** (UUID like `123e4567-e89b-12d3-a456-426614174000`)

### Step 3: Submit a Test Claim

1. Find `POST /claims/` endpoint
2. Click "Try it out"
3. Enter claim data (**use the customer ID from above**):
```json
{
  "customer_id": "paste-customer-uuid-here",
  "flight_info": {
    "flight_number": "LH123",
    "airline": "Lufthansa",
    "departure_date": "2025-11-15",
    "departure_airport": "FRA",
    "arrival_airport": "JFK"
  },
  "incident_type": "delay",
  "notes": "Flight delayed by 4 hours due to technical issues"
}
```
4. Click "Execute"
5. **Response should be `201 Created`** with claim details

### Step 4: Watch Celery Worker (Terminal 3)

Immediately after submitting, switch to Terminal 3 (Celery worker). You should see:

```
[2025-10-30 10:35:00,123: INFO/MainProcess] Task send_claim_submitted_email[abc-123-def-456] received
[2025-10-30 10:35:00,234: INFO/ForkPoolWorker-1] Task started: Sending claim submitted email to your-actual-email@gmail.com
[2025-10-30 10:35:02,456: INFO/ForkPoolWorker-1] Email sent successfully to your-actual-email@gmail.com
[2025-10-30 10:35:02,567: INFO/MainProcess] Task send_claim_submitted_email[abc-123-def-456] succeeded in 2.34s
```

**What this means**:
- Line 1: Task received from Redis queue ✅
- Line 2: Worker started processing the email ✅
- Line 3: Email sent successfully via Gmail SMTP ✅
- Line 4: Task completed in ~2 seconds ✅

### Step 5: Check Your Email

1. Open your email inbox (the email you used for the customer)
2. **Look for email from "ClaimPlane Support"** or your `SMTP_FROM_NAME`
3. Subject should be: "Claim Submitted - Lufthansa LH123"
4. Open the email

**Expected Email Content**:
- ✅ Green header with "Claim Submitted Successfully"
- ✅ Greeting: "Hello Test Customer"
- ✅ Claim details box with claim ID, flight number, airline
- ✅ "What happens next?" section
- ✅ Professional formatting with colors and layout

**Email might be in Spam folder initially** - mark it as "Not Spam"

### Step 6: Verify HTML Rendering

- Check if colors render (green header)
- Check if layout is clean and professional
- Try viewing on mobile (should be responsive)

**If email doesn't arrive within 2 minutes**, see [Troubleshooting](#troubleshooting) section.

---

## Test 2: Status Update Email

This tests the email sent when an admin updates a claim's status.

### Scenario 1: Approve a Claim

1. In Swagger UI, find `PUT /admin/claims/{claim_id}/status`
2. Click "Try it out"
3. Enter the claim ID from Test 1
4. **Add X-Admin-ID header**:
   - Click "Add string item" in Parameters
   - Header name: `X-Admin-ID`
   - Value: Any UUID (e.g., `11111111-1111-1111-1111-111111111111`)
5. Request body:
```json
{
  "new_status": "approved",
  "change_reason": "All documents verified. Flight confirmed delayed by 4 hours. Customer eligible for €600 compensation."
}
```
6. Click "Execute"

**Watch Terminal 3** (Celery worker):
```
[INFO] Task send_status_update_email received
[INFO] Task started: Sending status update email (submitted -> approved)
[INFO] Email sent successfully
[INFO] Task succeeded
```

**Check Email**:
- Subject: "Claim Status Update - Approved"
- **Green header** (approved status)
- Shows status change: "Submitted → Approved"
- Should show compensation amount (if calculated)
- "What happens next?" section for approved claims

### Scenario 2: Reject a Claim

1. Same endpoint: `PUT /admin/claims/{claim_id}/status`
2. Update status to rejected:
```json
{
  "new_status": "rejected",
  "change_reason": "Flight delay was less than 3 hours. Not eligible for compensation under EU261/2004."
}
```

**Check Email**:
- Subject: "Claim Status Update - Rejected"
- **Red header** (rejected status)
- Shows rejection reason in a warning box
- Explains next steps for rejected claims

### Scenario 3: Mark as Paid

1. First approve the claim (if not already)
2. Then update to paid:
```json
{
  "new_status": "paid",
  "change_reason": "Payment processed successfully"
}
```

**Check Email**:
- Subject: "Claim Status Update - Paid"
- **Blue header** (paid status)
- "Payment Processed" confirmation box
- Shows compensation amount (if set)
- Info about when funds will arrive

---

## Test 3: Document Rejected Email

This tests the email sent when an admin rejects an uploaded document.

### Step 1: Upload a Test Document (if needed)

1. Find `POST /files/upload` endpoint
2. Upload a test file:
   - `file`: Select any PDF, JPG, or PNG
   - `claim_id`: The claim ID from Test 1
   - `document_type`: `boarding_pass`
   - Add `X-Customer-ID` header with customer UUID

### Step 2: Reject the Document

1. Find `PUT /admin/files/{file_id}/review` endpoint
2. Click "Try it out"
3. Enter the file ID from upload response
4. Add `X-Admin-ID` header (any UUID)
5. Request body:
```json
{
  "approved": false,
  "rejection_reason": "Image is too blurry. Unable to read passenger name and flight details. Please upload a clearer image.",
  "reviewer_notes": "Customer needs to re-upload boarding pass"
}
```
6. Click "Execute"

**Watch Terminal 3**:
```
[INFO] Task send_document_rejected_email received
[INFO] Task started: Sending document rejected email
[INFO] Email sent successfully
[INFO] Task succeeded
```

**Check Email**:
- Subject: "Document Re-upload Required - Boarding Pass"
- **Orange header** (warning)
- Document issue details box
- Shows rejection reason
- "Tips for successful upload" section
- Action required box

---

## Monitor Celery Tasks

### Real-Time Monitoring (Terminal 3)

Keep Terminal 3 open to see tasks as they're processed:

```bash
# Each task shows:
[timestamp: INFO/MainProcess] Task {task_name}[{task_id}] received
[timestamp: INFO/Worker] Task started: {description}
[timestamp: INFO/Worker] Email sent successfully to {email}
[timestamp: INFO/MainProcess] Task {task_name}[{task_id}] succeeded in {time}s
```

### Check Redis Queue (Optional)

```bash
# Connect to Redis CLI
redis-cli -h localhost

# Check queue length (should be 0 if all tasks processed)
LLEN celery

# Check all keys
KEYS *

# Exit Redis CLI
exit
```

### View Task Results (Optional)

```bash
# In Python shell
source /Users/david/miniconda3/bin/activate ClaimPlane
python

>>> from app.celery_app import celery_app
>>> from app.tasks.claim_tasks import send_claim_submitted_email
>>>
>>> # Trigger a task
>>> result = send_claim_submitted_email.delay(
...     customer_email="test@example.com",
...     customer_name="Test User",
...     claim_id="test-123",
...     flight_number="LH123",
...     airline="Lufthansa"
... )
>>>
>>> # Check task status
>>> result.status
'SUCCESS'
>>>
>>> # Get result
>>> result.get(timeout=10)
{'status': 'success', 'email': 'test@example.com'}
>>>
>>> exit()
```

---

## Troubleshooting

### Problem: Celery worker won't start

**Error**: `ImportError: cannot import name 'celery_app'`

**Solution**:
```bash
# Check Python path
echo $PYTHONPATH

# Ensure you're in project root
cd /Users/david/Documents/Proyectos/flight_claim

# Try importing manually
python -c "from app.celery_app import celery_app; print('OK')"
# Should print: OK
```

### Problem: "Connected to redis" but no tasks listed

**Error**: `[tasks]` section is empty

**Solution**:
```bash
# Check tasks module exists
ls app/tasks/claim_tasks.py

# Verify tasks are decorated correctly
grep -n "@celery_app.task" app/tasks/claim_tasks.py
# Should show 3 matches

# Force reload
celery -A app.celery_app worker --loglevel=debug
```

### Problem: Emails not sending

**Error**: `Task failed: SMTP authentication failed`

**Solution 1 - Check credentials**:
```bash
# Verify .env file exists
cat .env | grep SMTP

# Check if password has spaces (should have spaces!)
# Correct: abcd efgh ijkl mnop
# Incorrect: abcdefghijklmnop
```

**Solution 2 - Test SMTP connection directly**:
```bash
python << EOF
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from app.services.email_service import EmailService

async def test():
    result = await EmailService.send_email(
        to_email=os.getenv("SMTP_USERNAME"),  # Send to yourself
        subject="Test Email",
        html_content="<h1>Test</h1><p>If you receive this, SMTP works!</p>",
        text_content="Test - SMTP works!"
    )
    print(f"Email sent: {result}")

asyncio.run(test())
EOF
```

**Common SMTP errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| `535 Authentication failed` | Wrong app password | Regenerate app password in Google Account |
| `534 Application-specific password required` | Using regular password | Use app password instead |
| `Connection refused` | Wrong port | Use port 587 for TLS |
| `Timeout` | Firewall blocking | Check firewall settings |

### Problem: Tasks stay in "PENDING" state

**Error**: Task received but never starts

**Solution**:
```bash
# Check Redis connection
redis-cli -h localhost ping
# Should return: PONG

# Check Celery can connect to Redis
celery -A app.celery_app inspect active
# Should show: empty list (if no tasks running)

# Check if worker is actually running
ps aux | grep celery
```

### Problem: Email goes to Spam

**Cause**: Gmail doesn't recognize the "From" address

**Temporary Solution**:
1. Check Spam folder
2. Mark as "Not Spam"
3. Add sender to contacts

**Long-term Solution** (for production):
- Set up SPF record for your domain
- Set up DKIM signing
- Use proper email service (SendGrid, AWS SES)

### Problem: HTML not rendering (plain text only)

**Cause**: Email client doesn't support HTML

**Solution**:
- Try different email client (Gmail web, Apple Mail, etc.)
- Check email source to verify HTML is included
- Plain text fallback should still be readable

### Problem: Can't find app password option in Google

**Cause**: 2-Step Verification not enabled

**Solution**:
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification first
3. Wait 5 minutes
4. Go back to Security → App passwords should now appear

---

## Understanding the "From" Address

### How Email "From" Works

When you send an email, there are actually TWO addresses involved:

1. **SMTP Username** (`SMTP_USERNAME`):
   - The Gmail account you're logging into
   - Example: `john.doe@gmail.com`
   - Used for authentication (login)

2. **From Address** (`SMTP_FROM_EMAIL`):
   - What recipients see in their inbox
   - Example: `noreply@claimplane.com`
   - Can be anything you want!

### Using Custom "From" Address with Gmail

**What you'll do**:
```bash
SMTP_USERNAME=john.doe@gmail.com           # Your actual Gmail
SMTP_FROM_EMAIL=noreply@claimplane.com  # What customers see
SMTP_FROM_NAME=ClaimPlane Support        # Display name
```

**What customers see**:
```
From: ClaimPlane Support <noreply@claimplane.com>
Subject: Claim Submitted - Lufthansa LH123
```

**Potential issues**:
- Some email clients show "via gmail.com" next to sender
- Example: `ClaimPlane Support <noreply@claimplane.com> via gmail.com`
- Emails might go to spam more often
- SPF checks might fail (Gmail's servers sending for your domain)

### Development vs Production

**Development (what we're doing now)**:
✅ Use Gmail SMTP with custom "From" address
✅ Perfect for testing
✅ Free and easy

**Production (for real customers)**:
❌ Don't use Gmail for production
✅ Option 1: **Own SMTP server on your domain**
- Set up Postfix/Sendmail on your server
- Full control, no "via" messages
- Requires server maintenance

✅ Option 2: **SendGrid** (recommended)
- Professional email delivery service
- Free tier: 100 emails/day
- Proper SPF/DKIM setup
- Deliverability analytics
- Cost: $15/month for 40k emails

✅ Option 3: **AWS SES** (cheapest)
- Amazon's email service
- $0.10 per 1000 emails
- Requires AWS account
- Sandbox mode initially (request production access)

✅ Option 4: **Configure Gmail to send as your domain**
- In Gmail: Settings → Accounts → "Send mail as"
- Add and verify your custom domain
- Google walks you through DNS setup
- Best of both worlds: Gmail + your domain

### Verifying Your Domain (Production)

When you're ready for production, you'll need to:

1. **Add SPF record** (DNS TXT record):
```
v=spf1 include:_spf.google.com ~all
```

2. **Add DKIM record** (DNS TXT record):
- Google provides this when you set up "Send as"
- Cryptographically signs emails

3. **Add DMARC record** (DNS TXT record):
```
v=DMARC1; p=quarantine; rua=mailto:dmarc@claimplane.com
```

**For now, don't worry about this!** It's only needed for production.

---

## Testing Checklist

Use this checklist to verify everything works:

### Setup Phase
- [ ] Gmail app password created
- [ ] `.env` file created with correct credentials
- [ ] Dependencies installed (`aiosmtplib`, `jinja2`)
- [ ] Database running (`docker ps` shows flight_claim_db)
- [ ] Redis running (`docker ps` shows flight_claim_redis)
- [ ] API running (Terminal 2, port 8000)
- [ ] Celery worker running (Terminal 3, shows 3 tasks)

### Email Tests
- [ ] Claim submitted email received
- [ ] Claim submitted email HTML renders correctly
- [ ] Status update email (approved) received
- [ ] Status update email (rejected) received
- [ ] Status update email (paid) received
- [ ] Document rejected email received
- [ ] All emails show correct "From" name
- [ ] All emails have correct subject lines

### Monitoring Tests
- [ ] Celery worker logs show tasks received
- [ ] Celery worker logs show emails sent successfully
- [ ] Tasks complete in ~2-3 seconds
- [ ] No error messages in logs
- [ ] Redis queue clears (all tasks processed)

### Edge Cases
- [ ] Test with wrong SMTP password → task retries 3 times
- [ ] Test with invalid email address → task fails gracefully
- [ ] Test with notifications disabled → no emails sent but API works
- [ ] Stop Celery worker → tasks queue in Redis → start worker → tasks process

---

## Next Steps

### You've Successfully Tested Phase 2! 🎉

Your email notification system is working. Here's what you've accomplished:

✅ Set up async task processing with Celery
✅ Configured Gmail SMTP
✅ Sent 3 types of automated emails
✅ Monitored background tasks
✅ Learned how email "From" addresses work

### What's Next?

**Option 1: Move to Phase 3**
- Implement JWT authentication
- Replace `X-Customer-ID` headers with proper login
- User registration and password reset

**Option 2: Enhance Email System**
- Add more email templates
- Implement email preferences (let customers opt out)
- Add email delivery tracking
- Set up unsubscribe links

**Option 3: Deploy to Production**
- Set up proper domain email
- Configure SendGrid or AWS SES
- Add DNS records (SPF, DKIM, DMARC)
- Set up monitoring

### Questions?

If something doesn't work:
1. Check the [Troubleshooting](#troubleshooting) section
2. Check Celery worker logs (Terminal 3)
3. Check API logs (Terminal 2)
4. Verify Redis is running: `redis-cli ping`
5. Test SMTP connection directly (see Troubleshooting)

---

## Appendix: Quick Reference

### Start Everything (Local Development)
```bash
# Terminal 1: Database & Redis
docker-compose up db redis -d

# Terminal 2: API
source /Users/david/miniconda3/bin/activate ClaimPlane
python app/main.py

# Terminal 3: Celery Worker
source /Users/david/miniconda3/bin/activate ClaimPlane
celery -A app.celery_app worker --loglevel=info
```

### Stop Everything
```bash
# Stop API (Terminal 2): Ctrl+C
# Stop Celery (Terminal 3): Ctrl+C
# Stop Docker services
docker-compose down
```

### View Logs
```bash
# API logs: Terminal 2
# Celery logs: Terminal 3
# Redis logs:
docker logs flight_claim_redis -f
# Database logs:
docker logs flight_claim_db -f
```

### Test Email Directly (Python)
```bash
python << 'EOF'
import asyncio, os
from dotenv import load_dotenv
load_dotenv()
from app.services.email_service import EmailService

asyncio.run(EmailService.send_email(
    os.getenv("SMTP_USERNAME"),
    "Test Email",
    "<h1>Test</h1>",
    "Test"
))
EOF
```

### Environment Variables Required
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM_EMAIL=noreply@claimplane.com
SMTP_FROM_NAME=ClaimPlane Support
SMTP_USE_TLS=true
NOTIFICATIONS_ENABLED=true
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/flight_claim
REDIS_URL=redis://localhost:6379
```

---

**Last Updated**: 2025-10-30
**Author**: Phase 2 Development Team
**Questions**: Check PHASE2_SUMMARY.md for implementation details
