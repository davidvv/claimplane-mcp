# Phase 1: Admin Dashboard & Claim Workflow Management

[← Back to Roadmap](README.md)

---

**Priority**: HIGHEST
**Status**: ✅ **COMPLETED** (2025-10-29)
**Estimated Effort**: 2-3 weeks
**Actual Effort**: 1 session
**Business Value**: Critical - enables core revenue-generating workflow

**📄 See [PHASE1_SUMMARY.md](../PHASE1_SUMMARY.md) for complete implementation details.**

**Note**: This phase is complete. The checkboxes below represent the original planning requirements and are kept for historical reference.

---

## Overview

Build the administrative interface and backend logic to review, process, and manage flight compensation claims. This is the core business function that allows the platform to generate revenue.

---

## Features to Implement

### 1.1 Admin Claim Management Endpoints

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

### 1.2 Compensation Calculation Engine

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

### 1.3 Document Review Interface (Backend)

**File**: `app/routers/admin_files.py` (new)

- [x] `GET /admin/claims/{claim_id}/documents` - List all documents for a claim
  - Group by document type
  - Show validation status
  - Show security scan results

- [x] **Document Viewer Modal (Frontend)** - View PDF/images directly in admin panel (Task #295)
  - Native browser rendering for PDFs and images
  - Auto-download for other file types
  - Integrated into Claim Detail page

- [x] `PUT /admin/files/{file_id}/review` - Approve/reject document
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

### 1.4 Database Schema Updates

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

### 1.5 Repositories

**File**: `app/repositories/admin_claim_repository.py` (new)

- [ ] Query methods for admin views
- [ ] Bulk operation support
- [ ] Complex filtering and sorting
- [ ] Analytics queries (claims by status, by airline, etc.)

### 1.6 Status Transition Validation

**File**: `app/services/claim_workflow_service.py` (new)

- [ ] Define valid status transition rules
- [ ] Validate transitions before applying
- [ ] Handle side effects (notifications, logging, etc.)
- [ ] Status change authorization (who can change what)

---

## Testing Requirements

- [ ] Unit tests for compensation calculation
- [ ] Integration tests for status transitions
- [ ] Test bulk operations
- [ ] Test invalid status transitions
- [ ] Test compensation edge cases

---

## Success Criteria

- ✅ Admin can view all claims in a filterable list
- ✅ Admin can review documents and approve/reject them
- ✅ Admin can calculate compensation automatically based on EU261/2004
- ✅ Admin can update claim status with proper audit trail
- ✅ All status changes are logged in status history
- ✅ Invalid status transitions are prevented

---

[← Back to Roadmap](README.md)
