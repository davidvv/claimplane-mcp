# Phase 4: Customer Account Management & GDPR Compliance

[← Back to Roadmap](README.md)

---

**Priority**: MEDIUM-HIGH - Required for GDPR compliance
**Status**: ✅ **COMPLETED** (95% Complete - Code Implementation Done)
**Estimated Effort**: 2-3 weeks
**Business Value**: Enables public launch with legal compliance
**Target Version**: v0.4.0
**Last Updated**: 2026-02-13 (Status corrected after code audit)

---

## Current Progress

### ✅ Completed (Phase 4.1 - 4.5)


**Priority**: HIGH - Required for production launch
**Status**: ✅ **COMPLETED** - ~95% Complete (Code Implementation Done)
**Estimated Effort**: 1-2 weeks (including cookie consent implementation)
**Business Value**: Critical - enables customer self-service and GDPR compliance
**Blocking**: Phase 4.6 (Cookie Consent) requires Phase 4.5.14 (HTTP-only cookies) - ✅ COMPLETED

**What's Completed**:
- ✅ Frontend account settings UI (AccountSettings.tsx) - 100% FULLY FUNCTIONAL
- ✅ Account management endpoints - 100% (GET /account/info, PUT /account/email, PUT /account/password, POST /account/delete-request)
- ✅ Admin deletion management endpoints - 100% (GET /admin/deletion-requests, approve/reject/process workflows)
- ✅ Admin frontend for deletion requests (DeletionRequests.tsx) - 100% FULLY FUNCTIONAL
- ✅ GDPR data export endpoint (GET /account/export-data) - 100% IMPLEMENTED
- ✅ Database models (AccountDeletionRequest, Customer deletion fields) - 100%
- ✅ Email notification tasks (email change, password change, deletion requests, admin notifications) - 100%
- ✅ GDPR service with data anonymization workflow - 100%
- ✅ Legal pages (Terms, Privacy Policy, Contact) - 100% EXIST AND FUNCTIONAL
- ✅ Granular GDPR consent (WP #358) - Separate T&C and Privacy Policy checkboxes
- ✅ Real IP tracking (WP #360) - Centralized Cloudflare/proxy IP extraction across API and middleware

**What's Remaining**:
- ⏸️ Cookie consent implementation - DEFERRED until analytics tracking added (not required for JWT auth cookies)
- 📋 Manual data deletion workflow documentation - PENDING (small documentation task)
- 📋 Privacy policy content review - PENDING (verify all sections current)

### Overview
Implement customer account settings page and GDPR-compliant account deletion workflow. Customers should be able to manage their email, password, and request account deletion.

### Features to Implement

#### 4.1 Account Settings Page (Frontend)

**File**: `frontend_Claude45/src/pages/AccountSettings.tsx` ✅ **COMPLETED**

- [x] Account settings UI with sections:
  - [x] Email address change (with verification)
  - [x] Password change (require current password)
  - [x] Account deletion request
  - [x] Display account creation date and last login

#### 4.2 Account Management Endpoints (Backend)

**File**: `app/routers/account.py` ✅ **COMPLETED**

- [x] `GET /account/info` - Get account information
  - Returns user profile data
  - Includes total claims count
  - Displays creation date and last login

- [x] `PUT /account/email` - Change email address
  - Require current password for verification
  - Send verification email to new address
  - Update email only after verification
  - Invalidate all existing tokens on email change

- [x] `PUT /account/password` - Change password
  - Require current password
  - Validate new password strength
  - Invalidate all refresh tokens (force re-login on all devices)
  - Send email notification about password change

- [x] `POST /account/delete-request` - Request account deletion
  - **DO NOT delete immediately** - create deletion request
  - Blacklist email to prevent login
  - Notify admins via email about deletion request
  - Include user info and open claims count
  - Set deletion_requested_at timestamp

#### 4.2.1 Admin Deletion Management ✅ **IMPLEMENTED**

**File**: `app/routers/admin_deletion_requests.py` ✅ **COMPLETED**

- [x] `GET /admin/deletion-requests` - List account deletion requests with filtering and pagination
  - Show pending deletion requests with user details
  - Display open claims count
  - Filter by status, date range, search by email
  
- [x] `GET /admin/deletion-requests/{id}` - Get detailed deletion request information
  - Full customer data snapshot
  - Review history and notes
  
- [x] `POST /admin/deletion-requests/{id}/review` - Approve or reject deletion request
  - Approve: Marks request for processing, notifies customer
  - Reject: Provides reason, allows customer to resubmit
  - Sends appropriate email notifications
  
- [x] `POST /admin/deletion-requests/{id}/process` - Execute data deletion/anonymization
  - Calls GDPRService to anonymize customer data
  - Deletes personal info while preserving claim records (anonymized)
  - Removes files from Nextcloud
  - Marks request as completed

#### 4.3 Database Schema Updates

**File**: `app/models.py` ✅ **COMPLETED**

- [x] Added fields to `Customer` model:
```python
# Account deletion fields
deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
deletion_reason = Column(Text, nullable=True)
is_blacklisted = Column(Boolean, default=False)
blacklisted_at = Column(DateTime(timezone=True), nullable=True)
```

- [x] Added new `AccountDeletionRequest` model:
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

**File**: `app/tasks/account_tasks.py` ✅ **COMPLETED**

- [x] Email to customer: Account deletion requested (confirmation)
- [x] Email to admins: New account deletion request (with user details and claims count)
- [x] Email to customer: Email changed (security notification)
- [x] Email to customer: Password changed (security notification)

#### 4.5 Admin Interface for Deletion Requests ✅ **IMPLEMENTED**

**File**: `frontend_Claude45/src/pages/Admin/DeletionRequests.tsx` ✅ **COMPLETED**

- [x] List pending deletion requests with filtering and pagination
- [x] Show customer details and claims summary
- [x] Approve/reject deletion with notes modal
- [x] Process deletion with confirmation
- [x] Real-time status updates
- [ ] Manual data deletion workflow documentation (PENDING - see section 4.9)

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
   - ✅ Define retention periods for different data types (claims: 7 years, implemented via `gdpr_retention_task.py`)
   - ✅ Keep financial records for 7 years (legal requirement, automated via Celery task)
   - ✅ Anonymize vs. delete decision tree (implemented: claims anonymized after 7 years)

4. **Right to Data Portability** ✅ **IMPLEMENTED**
   - [x] `GET /account/export-data` - Export all customer data as JSON ✅ IMPLEMENTED
   - [x] Includes claims, files metadata, account history, status history
   - [x] GDPR Article 20 compliance
   - [ ] PDF export format (optional enhancement)

5. **Privacy Policy & Terms** ✅ **PAGES EXIST**
   - [x] Privacy Policy page exists (`/privacy`) ✅ IMPLEMENTED
   - [x] Terms of Service page exists (`/terms`) ✅ IMPLEMENTED
   - [x] Contact page exists (`/contact`) ✅ IMPLEMENTED
   - [ ] Review privacy policy content for data deletion process details
   - [ ] Document 30-day deletion window in policy
   - [ ] Verify data retention explanations are current

#### 4.6 Cookie Consent & GDPR Compliance 🍪 **CONDITIONAL**

**Priority**: MEDIUM - Only required if we implement client-side tracking
**Status**: ⏸️ **DEFERRED** - Not needed until analytics with cookies are implemented
**Regulation**: GDPR Article 7 (Consent), ePrivacy Directive
**Last Updated**: 2025-12-29

**Current Assessment**:
We currently use ONLY strictly necessary cookies (JWT authentication: `access_token`, `refresh_token`). These do NOT require user consent under GDPR Article 6(1)(b) and ePrivacy Directive Recital 25.

**When Cookie Consent IS Required**:
- If we add Google Analytics (client-side tracking cookies)
- If we add marketing/retargeting cookies
- If we add any non-essential tracking

**When Cookie Consent is NOT Required** ✅:
- Strictly necessary authentication cookies (current setup)
- Server-side analytics (no cookies)
- Cookieless analytics (Plausible, Fathom, Simple Analytics)

**Overview**:
A cookie consent banner is only legally required when we store non-essential cookies. Our JWT authentication cookies are strictly necessary for the service to function and are exempt from consent requirements. We must still DISCLOSE these cookies in our Privacy Policy (Phase 4.7), but we don't need an interactive consent banner unless we add optional tracking.

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
- ✅ Phase 4.5.14 (HTTP-only cookie migration) is complete - READY TO START
- Required before removing OAuth from Cloudflare tunnel
- Blocking requirement for public EU launch
- Estimated implementation: 2-3 days

**References**:
- GDPR Cookie Consent Guide: https://gdpr.eu/cookies/
- ePrivacy Directive: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32002L0058
- Cookie Consent Library: https://github.com/orestbida/cookieconsent
- GDPR Article 7: https://gdpr-info.eu/art-7-gdpr/

#### 4.7 Missing Homepage Pages 📄 **REQUIRED FOR LAUNCH**

**Priority**: HIGH - Required for legal compliance and professional presence
**Status**: ⏳ **NOT STARTED**
**Last Updated**: 2025-12-29

**Overview**:
Add essential legal and informational pages to the homepage that are required for GDPR compliance, professional credibility, and customer trust.

**Missing Pages**:

1. **Terms of Use / Terms of Service** ❌
   - [ ] Create Terms of Service page (`/terms`)
   - [ ] Include sections:
     - [ ] Service description
     - [ ] User responsibilities
     - [ ] Intellectual property rights
     - [ ] Limitation of liability
     - [ ] Dispute resolution
     - [ ] Governing law (EU/Germany)
     - [ ] Contact information
   - [ ] Link from footer (all pages)
   - [ ] Require acceptance during claim submission
   - [ ] Version control and effective date

2. **Privacy Policy** ❌ **CRITICAL - GDPR REQUIRED**
   - [ ] Create Privacy Policy page (`/privacy`)
   - [ ] Include sections:
     - [ ] Data controller information (company details)
     - [ ] What data we collect (personal info, flight details, documents)
     - [ ] Why we collect it (legal basis: contract performance, legal obligation)
     - [ ] How we use it (claim processing, customer support, legal compliance)
     - [ ] Who we share it with (third parties: email service, file storage)
     - [ ] Data retention periods (claims: 7 years for legal compliance)
     - [ ] User rights (access, rectification, erasure, portability, object)
     - [ ] Cookie policy (integrated from 4.6)
     - [ ] International data transfers (if any)
     - [ ] Security measures (encryption, access controls)
     - [ ] How to exercise rights (contact email)
     - [ ] DPO contact information (if required)
     - [ ] Last updated date
   - [ ] Link from footer (all pages)
   - [ ] Link from cookie consent banner
   - [ ] Version control and effective date

3. **Contact Page** ❌
   - [ ] Create Contact page (`/contact`)
   - [ ] Include:
     - [ ] Contact form (name, email, subject, message)
     - [ ] Email address: support@claimplane.com
     - [ ] Response time expectations (24-48 hours)
     - [ ] FAQ section link
     - [ ] Company address (if applicable)
   - [ ] Integrate with backend email service (Celery task)
   - [ ] Rate limiting (prevent spam: 3 messages per hour per IP)
   - [ ] Auto-reply confirmation email
   - [ ] Link from footer and header navigation

**Implementation Details**:

**Frontend**:
- Create pages in `frontend_Claude45/src/pages/Legal/`
  - `TermsOfService.tsx`
  - `PrivacyPolicy.tsx`
  - `ContactPage.tsx`
- Add routes to `App.tsx`
- Update footer component with links
- Add "By continuing, you agree to our Terms of Service and Privacy Policy" to claim form

**Backend**:
- [ ] Add endpoint: `POST /contact` (contact form submission)
- [ ] Add Celery task: `send_contact_form_email`
- [ ] Rate limiting on contact endpoint

**Legal Review**:
- [ ] **CRITICAL**: Have Terms and Privacy Policy reviewed by legal professional
- [ ] Ensure GDPR compliance (especially Privacy Policy)
- [ ] Verify German/EU law compliance
- [ ] Update as needed based on legal feedback

**Timeline**:
- Privacy Policy: 1-2 days (research + writing + legal review)
- Terms of Service: 1-2 days (research + writing + legal review)
- Contact Page: 1 day (frontend + backend + email integration)
- **Total**: 3-5 days

**Success Criteria**:
- ✅ All three pages exist and are accessible
- ✅ Pages linked from footer on all pages
- ✅ Privacy Policy meets GDPR requirements
- ✅ Terms of Service covers liability and user responsibilities
- ✅ Contact form works and sends emails
- ✅ Legal review completed (recommended)

**Why This Matters**:
- **Legal Compliance**: Privacy Policy is MANDATORY under GDPR (Article 13 & 14)
- **Customer Trust**: Professional companies have these pages
- **Risk Mitigation**: Terms of Service protects company from liability
- **Transparency**: Users have right to know how their data is used
- **Support**: Contact page provides customer support channel

#### 4.8 Analytics & Tracking Strategy 📊 **DECISION NEEDED**

**Priority**: MEDIUM - Valuable for growth but not blocking launch
**Status**: 📋 **PLANNING** - Need to decide what to track and how
**Estimated Effort**: 1-3 days (depending on approach chosen)
**Last Updated**: 2025-12-29

**Overview**:
Determine what user behavior and business metrics we want to track, and choose a privacy-respecting implementation approach. The key question: What analytics provide business value without compromising user privacy or requiring cookie consent?

---

### What Could We Track? (Business Value Assessment)

#### 1. Conversion Funnel 🎯 **HIGH VALUE**

**Goal**: Identify where users abandon the claim submission process

**Track**:
- Homepage → Eligibility check: How many start?
- Eligibility check → Claim form: How many qualify and continue?
- Claim form → Document upload: Where do they drop off?
- Document upload → Submit: Do file uploads cause abandonment?

**Business Impact**:
- If 50% drop off at document upload → simplify that step
- If 80% abandon at eligibility check → improve messaging
- **ROI**: Increasing conversion by 10% = 10% more revenue
- **Implementation**: Easy - add event tracking in backend

**Example**:
```python
await analytics.track_event("claim_flow_step", {
    "step": "eligibility_check_started",
    "user_type": "anonymous",
    "flight_distance_km": 1500
})
```

#### 2. Traffic Sources 📈 **HIGH VALUE**

**Goal**: Know which marketing channels actually work

**Track**:
- Organic search vs paid ads vs referrals
- Which keywords bring paying customers?
- Social media effectiveness
- Referral program performance (future)

**Business Impact**:
- Stop wasting money on ads that don't convert
- Double down on channels that work
- Measure marketing ROI accurately
- **ROI**: Could cut marketing costs by 30-50%

**Implementation**: Server-side referrer tracking or Plausible

#### 3. User Behavior Patterns 🔍 **MEDIUM VALUE**

**Goal**: Understand how people actually use the site

**Track**:
- Which pages get viewed most?
- How long do users spend on the claim form?
- Do they read the FAQ before submitting?
- Mobile vs desktop usage
- Browser compatibility

**Business Impact**:
- Optimize page layout based on actual behavior
- Identify confusing UI elements
- Prioritize mobile vs desktop development
- **ROI**: Moderate - improves UX incrementally

**Implementation**: Page view tracking (server-side or Plausible)

#### 4. Technical Issues 🐛 **HIGH VALUE**

**Goal**: Catch errors affecting conversions before users complain

**Track**:
- JavaScript errors in browser console
- Failed API calls (4xx, 5xx errors)
- Slow page load times
- Browser/device compatibility issues
- File upload failures

**Business Impact**:
- Fix bugs proactively
- Identify performance bottlenecks
- Reduce support tickets
- **ROI**: High - every bug fix increases conversions

**Implementation**: Error logging (Sentry) + performance monitoring

#### 5. Business Metrics 💰 **CRITICAL VALUE**

**Goal**: Understand revenue and claim success rates

**Track**:
- Claims submitted per day/week/month
- Claim approval rate by airline
- Average compensation amount
- Time to process claims
- Customer lifetime value

**Business Impact**:
- Investor reporting
- Identify best/worst airlines to target
- Forecast revenue
- **ROI**: Critical for business operations

**Implementation**: Backend database queries + dashboard (no external tracking needed)

---

### What We DON'T Need to Track (Low/No Value)

❌ **Individual user browsing history** - Creepy, no business value, privacy violation
❌ **Demographics beyond what they tell us** - Not useful for B2C flight claims
❌ **Cross-site tracking** - Irrelevant for single-purpose platform
❌ **Social media integration tracking** - Overkill for your use case
❌ **Session recordings** - Invasive, limited value for transactional site
❌ **Heatmaps** - Nice-to-have, not critical for claims platform

---

### Implementation Options (Privacy-Respecting)

#### Option 1: Server-Side Event Tracking ✅ **RECOMMENDED - START HERE**

**What it is**: Track events in your backend code as users perform actions

**Advantages**:
- ✅ NO cookie consent needed (no client-side cookies)
- ✅ GDPR compliant by default (no PII unless you log it)
- ✅ Ad-blocker proof (server-side)
- ✅ Complete control over what's tracked
- ✅ Free (just database storage)
- ✅ Can implement TODAY

**What you track**:
```python
# app/services/analytics_service.py
async def track_event(event_name: str, properties: dict):
    """Track business events server-side"""
    event = AnalyticsEvent(
        event_name=event_name,
        properties=properties,
        timestamp=datetime.now(timezone.utc),
        # NO user identification unless authenticated
        user_id=current_user.id if authenticated else None,
        session_id=request.cookies.get("session_id"),  # Anonymous session
        ip_country=get_country_from_ip(request.client.host),
        user_agent=request.headers.get("user-agent")
    )
    await db.save(event)

# Usage throughout application
await track_event("claim_submitted", {
    "airline": "Lufthansa",
    "flight_distance_km": 1500,
    "compensation_tier": "400_euro",
    "incident_type": "delay"
})

await track_event("file_uploaded", {
    "document_type": "boarding_pass",
    "file_size_kb": 250,
    "mime_type": "application/pdf"
})

await track_event("claim_form_abandoned", {
    "last_step": "passenger_details",
    "time_spent_seconds": 120
})
```

**Cost**: Free (just database storage)
**Effort**: 1-2 days to implement
**Privacy**: Excellent - you control everything
**GDPR**: No consent needed (just disclose in Privacy Policy)

**Database Schema**:
```python
class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    event_name = Column(String(100), nullable=False, index=True)
    properties = Column(JSON, nullable=True)

    # Context (anonymous unless authenticated)
    user_id = Column(UUID, ForeignKey("customers.id"), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    ip_country = Column(String(2), nullable=True)  # Just country code, not full IP
    user_agent = Column(Text, nullable=True)

    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Then build simple analytics dashboard**:
```python
# app/routers/admin_analytics.py
@router.get("/admin/analytics/conversion-funnel")
async def get_conversion_funnel(session: AsyncSession = Depends(get_db)):
    """Show claim submission funnel"""

    # Count events by step
    steps = [
        "eligibility_check_started",
        "claim_form_started",
        "documents_uploaded",
        "claim_submitted"
    ]

    funnel = {}
    for step in steps:
        count = await session.execute(
            select(func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.event_name == step)
            .where(AnalyticsEvent.timestamp >= datetime.now() - timedelta(days=30))
        )
        funnel[step] = count.scalar()

    return funnel
    # Returns: {
    #   "eligibility_check_started": 1000,
    #   "claim_form_started": 600,  # 40% drop-off
    #   "documents_uploaded": 450,   # 25% drop-off
    #   "claim_submitted": 400       # 11% drop-off
    # }
```

---

#### Option 2: Plausible Analytics ✅ **RECOMMENDED - ADD AFTER OPTION 1**

**What it is**: Privacy-focused, cookieless analytics service (like Google Analytics but GDPR-friendly)

**Advantages**:
- ✅ NO cookie consent needed (cookieless tracking)
- ✅ GDPR compliant by default (EU-based, no PII)
- ✅ Ad-blocker resistant (respects DNT but not blocked like Google)
- ✅ Beautiful dashboard (easy to share with investors/team)
- ✅ 2-minute setup (one script tag)
- ✅ Lightweight (< 1KB script)
- ✅ Open source (can self-host)

**What you get**:
- Page views and unique visitors
- Traffic sources (referrers, UTM campaigns)
- Top pages and entry/exit pages
- Countries and devices
- Custom events (button clicks, form submissions)
- Real-time dashboard

**Cost**:
- Hosted: $9/month (up to 10k monthly pageviews)
- Self-hosted: Free (requires server setup)

**Setup**:
```html
<!-- In frontend_Claude45/public/index.html -->
<script defer
        data-domain="eac.dvvcloud.work"
        src="https://plausible.io/js/script.js">
</script>
```

**Custom events** (track conversions):
```typescript
// In frontend
plausible('Claim Submitted', {
  props: {
    airline: 'Lufthansa',
    compensation: '400'
  }
});
```

**Effort**: 2 minutes (hosted) or 2 hours (self-hosted)
**Privacy**: Excellent - no cookies, no PII, GDPR-compliant
**GDPR**: No consent needed

**Comparison to Google Analytics**:
| Feature | Plausible | Google Analytics |
|---------|-----------|------------------|
| Cookie consent | ❌ Not needed | ✅ Required |
| Ad-blocker proof | ⚠️ Partial | ❌ Blocked |
| Privacy-friendly | ✅ Yes | ❌ No |
| Setup complexity | ✅ 2 minutes | ⚠️ 30 minutes |
| Cost | $9/month | Free |
| Data ownership | ✅ Yours | ❌ Google's |

**Website**: https://plausible.io

---

#### Option 3: Self-Hosted Umami ✅ **FREE ALTERNATIVE**

**What it is**: Open-source, self-hosted analytics (like Plausible but free)

**Advantages**:
- ✅ NO cookie consent needed (cookieless)
- ✅ GDPR compliant (you host it)
- ✅ Free (open source)
- ✅ Full data ownership
- ✅ Similar features to Plausible

**Disadvantages**:
- ⚠️ Requires setup and maintenance
- ⚠️ Uses server resources

**Cost**: Free (requires Docker container on your server)
**Effort**: 2-3 hours to set up
**Privacy**: Excellent - you control everything
**GDPR**: No consent needed

**Website**: https://umami.is

---

#### Option 4: Google Analytics 4 (Privacy Mode) ⚠️ **NOT RECOMMENDED**

**What it is**: Google's analytics platform with privacy settings enabled

**Advantages**:
- ✅ Free
- ✅ Powerful features
- ✅ Familiar to everyone
- ⚠️ Can be configured for cookieless tracking

**Disadvantages**:
- ❌ STILL requires consent in EU (sends data to Google)
- ❌ Ad-blockers block it (40-60% of traffic lost)
- ❌ Privacy concerns (Google owns your data)
- ❌ Overkill for your use case
- ❌ Slower (large script)

**Verdict**: **Not recommended** for ClaimPlane - privacy concerns and ad-blocking make it less effective than alternatives

---

#### Option 5: Error Tracking (Sentry) 🐛 **HIGHLY RECOMMENDED**

**What it is**: Real-time error tracking and performance monitoring

**What you get**:
- JavaScript errors in user browsers
- Backend exceptions and crashes
- API response times
- Stack traces with context
- User impact analysis
- Alerting when errors spike

**Advantages**:
- ✅ NO cookie consent needed (just error monitoring)
- ✅ Catches bugs before users report them
- ✅ Shows exactly what went wrong
- ✅ Free tier: 5k errors/month

**Cost**:
- Free tier: 5,000 errors/month
- Paid: $26/month (50k errors/month)

**Setup**:
```python
# Backend
import sentry_sdk
sentry_sdk.init(dsn="your-dsn", traces_sample_rate=0.1)
```

```typescript
// Frontend
import * as Sentry from "@sentry/react";
Sentry.init({ dsn: "your-dsn" });
```

**Effort**: 1 hour
**Privacy**: Good - only captures errors, not behavior
**GDPR**: No consent needed (error monitoring is legitimate interest)

**Website**: https://sentry.io

---

### Recommended Implementation Strategy

**Phase 1: Immediate (Week 1)** - Free, No Consent Needed
1. ✅ **Server-side event tracking** (Option 1)
   - Track conversion funnel steps
   - Track business metrics (claims submitted, approved, etc.)
   - Track technical errors
   - Build simple admin dashboard
   - **Effort**: 1-2 days
   - **Cost**: Free

2. ✅ **Sentry error tracking** (Option 5)
   - Catch frontend and backend errors
   - Performance monitoring
   - **Effort**: 1 hour
   - **Cost**: Free tier

**Phase 2: After 100+ Users (Month 2)** - Still No Consent Needed
3. ✅ **Add Plausible Analytics** (Option 2)
   - Beautiful traffic dashboard
   - Traffic source analysis
   - Professional reporting for investors
   - **Effort**: 5 minutes
   - **Cost**: $9/month

**Phase 3: Future (Month 6+)** - If Needed
4. ⚠️ **Consider cookie consent** (Phase 4.6) ONLY if you want:
   - User-specific tracking across sessions
   - Remarketing/advertising cookies
   - Third-party marketing integrations

---

### What We Need to Decide

**Decision Matrix**:

| Question | Options | Recommendation |
|----------|---------|----------------|
| **Track conversion funnel?** | Yes / No | ✅ YES - High ROI, implement server-side |
| **Track traffic sources?** | Plausible / Umami / Google / None | ✅ Plausible ($9/mo) or Umami (free) |
| **Track errors?** | Sentry / Custom / None | ✅ Sentry (free tier) |
| **Track business metrics?** | Yes / No | ✅ YES - Already in database, add dashboard |
| **Need cookie consent?** | Yes / No | ❌ NO - If using recommended options |

**Next Steps**:
1. [ ] **Decide**: Which metrics are most valuable for the business?
2. [ ] **Choose**: Plausible ($9/mo) or Umami (free, self-hosted)?
3. [ ] **Implement**: Start with server-side tracking (1-2 days)
4. [ ] **Add**: Error tracking with Sentry (1 hour)
5. [ ] **Update**: Privacy Policy to disclose analytics (Phase 4.7)

**Budget Impact**:
- **Option A** (Free): Server-side + Umami + Sentry free tier = $0/month
- **Option B** (Paid): Server-side + Plausible + Sentry free tier = $9/month
- **Option C** (Full): Server-side + Plausible + Sentry paid = $35/month

**Privacy Impact**:
- All recommended options: NO cookie consent banner needed ✅
- Just disclose in Privacy Policy: "We use cookieless analytics to improve our service"

---

### Success Criteria

After implementing analytics, we should be able to answer:
- ✅ How many people start vs complete claims? (conversion rate)
- ✅ Where do users drop off in the funnel? (optimization targets)
- ✅ Which marketing channels drive the most claims? (ROI)
- ✅ What errors are users encountering? (bug priorities)
- ✅ How many claims are approved vs rejected by airline? (business intelligence)
- ✅ What's the average claim value? (revenue forecasting)

#### 4.9 Manual Data Deletion Workflow Documentation 📋 **PENDING**

**Priority**: MEDIUM - Required for admin operations
**Status**: ⏳ **NOT STARTED**
**Estimated Effort**: 2-4 hours
**Assignee**: TBD

**Overview**:
Create comprehensive documentation for administrators on how to manually review and process account deletion requests in compliance with GDPR Article 17 (Right to Erasure).

**Documentation Requirements**:

1. **Admin Guide Document** (`docs/admin/deletion-workflow.md`)
   - [ ] Step-by-step workflow for reviewing deletion requests
   - [ ] Decision tree: Approve vs Reject criteria
   - [ ] Pre-deletion checklist (open claims, pending payments, disputes)
   - [ ] Data anonymization process explanation
   - [ ] Post-deletion verification steps

2. **Data Inventory Reference**
   - [ ] List all data stores (PostgreSQL, Nextcloud, Redis, backups)
   - [ ] Map data dependencies and relationships
   - [ ] Document what gets anonymized vs deleted
   - [ ] Retention period reference table

3. **Emergency Procedures**
   - [ ] How to cancel an approved deletion request
   - [ ] How to restore accidentally deleted data (if within backup window)
   - [ ] Contact information for technical support

4. **Legal Compliance Notes**
   - [ ] GDPR Article 17 requirements summary
   - [ ] Legal retention exceptions (financial records, active disputes)
   - [ ] Documentation requirements for regulatory audits

**Acceptance Criteria**:
- [ ] New admin can follow documentation to process a deletion request correctly
- [ ] Documentation includes screenshots of admin interface
- [ ] Decision criteria are clear and unambiguous
- [ ] Legal compliance requirements are explained

**Dependencies**:
- Admin deletion interface (✅ COMPLETED)
- GDPR service implementation (✅ COMPLETED)

---

### Testing Requirements

- [x] Test email change workflow with verification
- [x] Test password change and token invalidation
- [x] Test account deletion request flow
- [x] Test blacklist prevents login
- [x] Test admin can view and process deletion requests
- [x] Test GDPR data export

### Success Criteria

- ✅ Customers can change their email and password
- ✅ Account deletion requests are tracked and require admin approval
- ✅ Blacklisted emails cannot log in
- ✅ Admins receive notification of deletion requests
- ✅ Customer data can be exported for GDPR compliance
- ⏳ Clear manual process documented for data deletion (Section 4.9)
- ✅ Privacy policy pages exist and are accessible

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

[← Back to Roadmap](README.md)
