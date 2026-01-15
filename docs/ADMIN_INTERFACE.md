# Admin Interface Guide

Complete guide to using the ClaimPlane Admin Dashboard for managing flight compensation claims.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Admin Dashboard](#admin-dashboard)
- [Claim Details](#claim-details)
- [Status Management](#status-management)
- [Features](#features)

---

## Overview

The Admin Interface provides a comprehensive dashboard for managing flight compensation claims. Admins can:

- ✅ View all claims in a sortable, filterable table
- ✅ Search claims by customer, email, or flight number
- ✅ View detailed claim information including customer details, flight info, and documents
- ✅ Update claim statuses with audit trail
- ✅ Add internal notes or customer-facing notes
- ✅ Review and approve/reject uploaded documents
- ✅ Track status history for each claim
- ✅ View analytics summary (total claims, pending review, compensation amounts)

---

## Getting Started

### 1. Create an Admin User

First, you need an admin account. See [ADMIN_USER_MANAGEMENT.md](./ADMIN_USER_MANAGEMENT.md) for detailed instructions.

**Quick setup:**
```bash
# Activate conda environment
source /Users/david/miniconda3/bin/activate ClaimPlane

# Run admin creation script
python scripts/create_admin_user.py
```

### 2. Login to Admin Dashboard

1. Navigate to: `http://localhost:3000/auth`
2. Enter your admin email and password
3. Click "Login"
4. You'll be redirected based on your role:
   - **Admin/Superadmin** → `/admin/dashboard`
   - **Customer** → `/my-claims`

### 3. Access Admin Dashboard Directly

Once logged in, you can access the admin dashboard at:
```
http://localhost:3000/admin/dashboard
```

---

## Admin Dashboard

The main dashboard shows all claims in the system with powerful filtering and search capabilities.

### Dashboard Sections

#### 1. Analytics Cards (Top)

Four summary cards showing:
- **Total Claims**: All claims in the system
- **Pending Review**: Claims awaiting admin action
- **Approved**: Claims that have been approved
- **Total Compensation**: Sum of all compensation amounts (in EUR)

#### 2. Filters

**Search Bar:**
- Search by customer name, email, or flight number
- Real-time filtering as you type

**Status Filter:**
- All Statuses
- Submitted
- Pending Review
- Under Review
- Approved
- Rejected
- Completed

**Airline Filter:**
- Filter by airline name (e.g., "Ryanair", "EasyJet")

**Action Buttons:**
- **Filter**: Apply current filters
- **Reset**: Clear all filters

#### 3. Claims Table

Displays claims with the following columns:

| Column | Description |
|--------|-------------|
| **Customer** | Name and email |
| **Flight** | Flight number and airline |
| **Route** | Departure → Arrival airports |
| **Incident** | Type (delay, cancellation, etc.) |
| **Status** | Current claim status (color-coded badge) |
| **Compensation** | Calculated EUR amount |
| **Submitted** | Date claim was submitted |
| **Files** | Number of uploaded documents |
| **Actions** | "View" button to see details |

**Interactions:**
- Click any row to view claim details
- Click "View" button to open claim detail page

---

## Claim Details

The claim detail page shows comprehensive information about a single claim.

### URL Pattern
```
/admin/claims/{claim-id}
```

### Page Layout

The claim detail page is divided into two columns:

#### Left Column (Main Details)

**1. Flight Information Card**
- Flight number and airline
- Route (departure → arrival)
- Incident type
- Scheduled departure/arrival times
- Actual departure/arrival times (if available)
- Delay duration (in hours)
- Calculated compensation amount
- Incident description

**2. Customer Information Card**
- Full name
- Email address
- Phone number (if provided)
- Full address (street, city, postal code, country)

**3. Documents Card**
- Lists all uploaded documents
- For each document:
  - Original filename
  - Document type (boarding pass, ID, etc.)
  - File size
  - Upload date
  - Status badge (uploaded, approved, rejected)
  - "View" button to download/preview

**4. Notes Card**
- **Add Note Form:**
  - Text area for note content
  - Checkbox: "Internal note (not visible to customer)"
  - "Add Note" button

- **Notes List:**
  - Shows all notes in chronological order
  - Each note displays:
    - Author name
    - Timestamp
    - "Internal" badge (if internal note)
    - Note text

#### Right Column (Actions & History)

**1. Update Status Card**
- **Status Dropdown:**
  - Shows current status
  - Lists all valid next statuses (based on workflow rules)
  - Only valid transitions are allowed

- **Reason Field:**
  - Optional text field
  - Explain why status is being changed
  - Shown in status history

- **Update Button:**
  - Disabled if no status change
  - Shows "Updating..." when in progress

**2. Status History Card**
- Chronological list of all status changes
- For each change:
  - New status (with badge)
  - Admin who made the change
  - Timestamp
  - Reason (if provided)

**3. Quick Info Card**
- Full Claim ID (UUID)
- Submitted timestamp
- Last updated timestamp
- Extraordinary circumstances flag (if applicable)

---

## Status Management

### Status Workflow

Claims follow a predefined workflow with valid transitions:

```
submitted
  ├─> pending_review
  └─> rejected

pending_review
  ├─> under_review
  └─> rejected

under_review
  ├─> approved
  ├─> additional_info_required
  └─> rejected

additional_info_required
  ├─> under_review
  └─> rejected

approved
  └─> payment_processing

payment_processing
  └─> payment_sent

payment_sent
  └─> completed

Any status → cancelled
```

### Status Descriptions

| Status | Description | Next Steps |
|--------|-------------|------------|
| **submitted** | Claim just submitted by customer | Review claim details |
| **pending_review** | Awaiting admin review | Assign to reviewer |
| **under_review** | Admin is reviewing | Approve or request info |
| **additional_info_required** | Need more info from customer | Wait for customer response |
| **approved** | Claim approved for compensation | Process payment |
| **rejected** | Claim rejected | Provide rejection reason |
| **payment_processing** | Payment being processed | Wait for payment completion |
| **payment_sent** | Payment sent to customer | Confirm receipt |
| **completed** | Claim fully resolved | Archive |
| **cancelled** | Claim cancelled | No further action |

### Updating Claim Status

**Steps:**
1. Navigate to claim detail page
2. Scroll to "Update Status" card (right column)
3. Select new status from dropdown (only valid transitions shown)
4. Optionally provide a reason in the text field
5. Click "Update Status"
6. Status will update immediately
7. Customer receives email notification (if configured)
8. Status history is automatically updated

**Best Practices:**
- ✅ Always provide a reason for rejections
- ✅ Provide reason when changing to "additional_info_required"
- ✅ Review all documents before approving
- ✅ Add internal notes to document decision-making process

---

## Features

### Search & Filtering

**Search supports:**
- Customer first name
- Customer last name
- Customer email
- Flight number
- Airline name

**Filters:**
- Status filter (dropdown)
- Airline filter (text input)
- Combination of filters

**Tips:**
- Use airline filter for bulk review (e.g., "Ryanair" claims)
- Combine status filter with search for specific customer issues
- Use "Pending Review" status to prioritize work queue

### Notes System

**Two types of notes:**

1. **Internal Notes** (checkbox checked)
   - Only visible to admin users
   - Use for internal communication and documentation
   - Examples: "Spoke with airline", "Awaiting legal review"

2. **Customer-Facing Notes** (checkbox unchecked)
   - Visible to customer
   - Use for customer communication
   - Examples: "We've contacted the airline on your behalf"

**Note Features:**
- Chronological display (newest first)
- Shows author name and timestamp
- Cannot be edited once posted
- All notes are permanently logged

### Document Review

**Document Types:**
- Boarding pass
- ID document
- Flight ticket
- Delay certificate
- Cancellation notice
- Bank statement
- Receipt
- Other

**Review Process:**
1. Click "View" on document in Documents card
2. Review document content
3. Approve or reject via file review endpoint (future UI feature)
4. Customer receives notification if rejected

### Analytics Dashboard

**Metrics shown:**
- **Total Claims**: All-time claim count
- **Pending Review**: Claims needing attention
- **Approved**: Successfully approved claims
- **Total Compensation**: Sum of all compensation amounts

**Use Cases:**
- Monitor workload (pending review count)
- Track approval rates
- Estimate total liability
- Identify trends by airline/route

---

## Keyboard Shortcuts

*(Future enhancement)*

Planned keyboard shortcuts:
- `Ctrl/Cmd + K`: Quick search
- `N`: Add note
- `S`: Update status
- `Esc`: Close modal/cancel

---

## Mobile Support

The admin interface is responsive and works on tablets. However, for best experience:
- ✅ **Recommended**: Desktop (1280px+ width)
- ⚠️ **Supported**: Tablet (768px+ width)
- ❌ **Not Optimized**: Mobile phone (<768px)

---

## Troubleshooting

### Can't Access Admin Dashboard

**Problem**: Redirected to login or home page when accessing `/admin/dashboard`

**Solutions:**
1. Check you're logged in (look for auth token in localStorage)
2. Verify your user has `admin` or `superadmin` role:
   ```sql
   SELECT email, role FROM customers WHERE email = 'your@email.com';
   ```
3. Clear browser cache and cookies
4. Try logging out and back in

### Claims Not Loading

**Problem**: "Failed to load claims" error

**Solutions:**
1. Check backend is running (`http://localhost:8000/health`)
2. Check browser console for errors (F12)
3. Verify JWT token is valid (check localStorage `auth_token`)
4. Refresh access token via `/auth/refresh`

### Status Update Fails

**Problem**: "Failed to update claim status" error

**Possible Causes:**
1. **Invalid transition**: You selected a status that's not allowed from current status
2. **Missing reason**: Some status changes require a reason (e.g., rejection)
3. **Expired token**: Your session may have expired

**Solutions:**
1. Check valid transitions for current status
2. Provide a reason if required
3. Log out and back in to refresh session

### Documents Not Visible

**Problem**: Document list is empty but customer uploaded files

**Possible Causes:**
1. Files failed to upload to Nextcloud
2. Database sync issue
3. Permission issues

**Solutions:**
1. Check Nextcloud is running (`docker ps | grep nextcloud`)
2. Check backend logs for Nextcloud errors
3. Verify file records in database:
   ```sql
   SELECT * FROM claim_files WHERE claim_id = 'claim-id-here';
   ```

---

## API Endpoints Used

The admin interface uses these backend endpoints:

**Claims:**
- `GET /admin/claims` - List claims with filters
- `GET /admin/claims/{id}` - Get claim details
- `PUT /admin/claims/{id}/status` - Update status
- `POST /admin/claims/{id}/notes` - Add note
- `GET /admin/claims/{id}/notes` - Get notes
- `GET /admin/claims/{id}/history` - Get status history
- `GET /admin/claims/{id}/status-transitions` - Get valid statuses
- `GET /admin/claims/analytics/summary` - Get analytics

**Files:**
- `GET /admin/files/claim/{id}/documents` - List claim files
- `GET /admin/files/{id}/download` - Download file
- `PUT /admin/files/{id}/review` - Approve/reject file
- `GET /admin/files/pending-review` - Get files awaiting review

All endpoints require:
- `Authorization: Bearer {jwt-token}` header
- User with `admin` or `superadmin` role

---

## Future Enhancements

### short term improvements that I wanna take care of:
now the table view with all the claims needs improvements: filters dont work; they do nothing. We need a filed showing which admin is taking care of that claim. Finally, we have a markdown file @docs/ADMIN_INTERFACE.md that has some to DOs. Please take care of the filtering, as we have it in there, claim asignment, in browser document viewer. I also want to have a field to see the 
progress of a claim in days. Days since created, days since last update (and if you think there are some more data fields that are interesting for future analytics please suggest them). Finally: how hard would be the real-time updates (websocket)? 

Planned features for future versions:

- [x] Filters working correctly
- [x] Assigned admin field in claims table
- [x] Days since created field
- [x] Days since last update field
- [ ] Bulk status updates (select multiple claims)
- [ ] Advanced filtering (date range, compensation amount)
- [ ] Export claims to CSV/Excel
- [ ] In-browser document viewer (PDF, images)
- [ ] Email templates customization
- [ ] User management UI (promote users to admin)
- [ ] Claim assignment UI (assign claims to specific admins)
- [ ] Analytics dashboard with charts
- [ ] Keyboard shortcuts
- [ ] Dark mode toggle
- [ ] Real-time updates (WebSocket)
- [ ] Note editing functionality

### Additional Analytics Fields (Suggestions for Future Implementation)

These metrics would provide deeper insights into claim processing efficiency and help identify bottlenecks:

1. **Days in Current Status**
   - Track how long a claim has been in its current status
   - Helps identify stuck claims that need attention
   - Useful for SLA monitoring (e.g., "Claims pending review > 7 days")

2. **Average Response Time**
   - Time between status changes
   - Measure admin performance and efficiency
   - Identify slow-moving claims

3. **Time to First Action**
   - Time from submission to first status change
   - Critical SLA metric for customer satisfaction
   - Identify claims that haven't been touched

4. **Compensation per Day**
   - Calculated as: compensation_amount / claim_age_days
   - Priority metric for high-value claims
   - Help optimize which claims to process first

5. **Admin Workload Distribution**
   - Number of active claims assigned per admin
   - Load balancing metric
   - Identify overloaded or underutilized admins

6. **Status Transition History Metrics**
   - Average time spent in each status
   - Common status paths (workflow analysis)
   - Identify inefficient workflow patterns

**Implementation Notes:**
- Most of these require tracking status change timestamps more granularly
- Could be calculated on-the-fly or pre-computed and cached
- Consider adding database indexes on relevant timestamp fields

---

## Related Documentation

- [Admin User Management](./ADMIN_USER_MANAGEMENT.md) - Creating admin accounts
- [API Reference](./api-reference.md) - Complete API documentation
- [Database Schema](./database-schema.md) - Database structure
- [Security Audit](./SECURITY_AUDIT_v0.2.0.md) - Security considerations

---

**Last Updated:** 2025-11-29
**Version:** v0.2.0
