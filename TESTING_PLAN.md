# COMPREHENSIVE TESTING PLAN - Multi-Passenger Claims (Phase 5)

**Based on User Requirements:**
- Priority: Customer flow first
- Test Data: UA988 on 2025-08-18 (3+ hour delay, eligible)
- Approach: Sequential testing (one WP at a time)
- Bug Handling: Continue testing, document all bugs, fix after complete testing

---

## TEST EXECUTION STRATEGY

**Test Flight Data:**
- Flight: UA988
- Date: 2025-08-18
- Route: FRA → IAD
- Status: 3+ hours delayed (eligible for €600 compensation per passenger)
- This is our "golden test case" - known eligible flight

**Sequential Approach:**
Each phase must be completed and verified before moving to the next. This ensures thorough testing without overwhelming complexity.

**Bug Documentation:**
- All bugs will be documented in real-time
- Testing continues even if bugs found
- Fixes happen AFTER complete testing phase
- No interruptions to ask user (as requested)

---

## PHASE 0: PRE-TESTING SETUP

### 0.1 Verify API Connectivity
```bash
# Test AeroDataBox API
python scripts/test_api_connection.py

# Expected: Status 200, flight data returned
# Test with: UA988 on 2025-08-18
curl "https://eac.dvvcloud.work/api/v1/flights/status/UA988?date=2025-08-18"
```

### 0.2 Verify Test Accounts
- Customer account: vences.david@icloud.com (existing)
- Admin account: Need to verify access
- Ensure JWT tokens work

### 0.3 Clear Test Environment
- Clean browser cache
- Reset any test claim groups
- Ensure fresh start

---

## PHASE 1: WP #366 - Customer Consent Checkbox

### Objective
Test GDPR-compliant consent checkbox in Step 3 of claim form when multiple passengers are added.

### Test Steps

#### 1.1 Single Passenger (Consent Should NOT Appear)
1. Navigate to: https://eac.dvvcloud.work/claim
2. Enter flight: UA988 on 2025-08-18
3. Complete Step 1 (Flight) and Step 2 (Eligibility)
4. In Step 3, add only 1 passenger (yourself)
5. **VERIFY**: Consent checkbox should NOT be visible
6. Fill other required fields
7. Click "Continue to Review"
8. **VERIFY**: Proceeds to Step 4 without issues

**Pass Criteria:**
- [ ] No consent checkbox shown for single passenger
- [ ] Form validates and proceeds normally
- [ ] No errors in browser console

#### 1.2 Multiple Passengers (Consent MUST Appear)
1. Navigate to: https://eac.dvvcloud.work/claim
2. Enter flight: UA988 on 2025-08-18
3. Complete Step 1 and Step 2
4. In Step 3, add first passenger (account holder)
5. Click "Add Passenger" button
6. Add second passenger (e.g., spouse)
7. **VERIFY**: Amber-colored consent card appears below passengers
8. **VERIFY**: Checkbox text: "I confirm I have permission to file claims for these passengers"
9. Fill all required fields (email, address, etc.)
10. Try to submit WITHOUT checking consent box
11. **VERIFY**: Form validation error appears
12. Check the consent checkbox
13. Click "Continue to Review"
14. **VERIFY**: Proceeds to Step 4 successfully

**Pass Criteria:**
- [ ] Consent checkbox appears when 2+ passengers added
- [ ] Form prevents submission without consent
- [ ] Clear error message shown
- [ ] Amber styling draws attention
- [ ] Proceeds normally after consent given

#### 1.3 Three+ Passengers
1. Add 3+ passengers in Step 3
2. **VERIFY**: Consent checkbox still appears
3. Complete submission
4. **VERIFY**: All passengers saved correctly

---

## PHASE 2: WP #363 - Customer Dashboard Claim Groups

### Objective
Test the new "Claim Groups" tab in customer dashboard showing grouped claims.

### Test Steps

#### 2.1 View Claim Groups Tab
1. Login as customer: vences.david@icloud.com
2. Navigate to: https://eac.dvvcloud.work/claims
3. **VERIFY**: Two tabs visible: "Individual Claims" and "Claim Groups"
4. Click "Claim Groups" tab
5. **VERIFY**: Shows count badge (e.g., "2") if groups exist
6. **VERIFY**: Group cards displayed (or empty state if none)

**Pass Criteria:**
- [ ] Tab navigation works
- [ ] Count badges show correct numbers
- [ ] Smooth transition between tabs

#### 2.2 Claim Group Card Display
1. If claim groups exist:
   - **VERIFY**: Each card shows:
     - Group name (or "Group - [flight_number]")
     - Flight number
     - Flight date
     - Number of passengers
     - Status badge
     - Total compensation (if calculated)
     - Status summary (e.g., "Pending: 2, Approved: 1")
   - **VERIFY**: Cards have amber left border
   - **VERIFY**: Cards are clickable

2. If no claim groups exist:
   - **VERIFY**: Empty state message shown
   - **VERIFY**: "File a Claim" button present

**Pass Criteria:**
- [ ] All information displayed correctly
- [ ] Formatting and styling consistent
- [ ] Responsive on mobile

#### 2.3 Filter and Search (if implemented)
1. Use filters (status, date range)
2. **VERIFY**: Results update correctly
3. Use search box
4. **VERIFY**: Search filters groups

---

## PHASE 3: WP #362 - Claim Groups API Endpoints

### Objective
Test all backend API endpoints for claim groups.

### Test Steps

#### 3.1 Create Claim Group API
```bash
# Login first to get JWT token
curl -X POST https://eac.dvvcloud.work/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "vences.david@icloud.com", "password": "xxx"}'

# Create claim group
curl -X POST https://eac.dvvcloud.work/api/v1/claim-groups \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "flight_number": "UA988",
    "flight_date": "2025-08-18",
    "group_name": "Test Family Group"
  }'

# Expected: 201 Created
# Response: { success: true, data: { id, group_name, flight_number, flight_date } }
```

**Pass Criteria:**
- [ ] Returns 201 status
- [ ] Group created in database
- [ ] Response includes all required fields

#### 3.2 List My Claim Groups API
```bash
curl https://eac.dvvcloud.work/api/v1/claim-groups/me \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Response: { success: true, data: [ { group1 }, { group2 } ] }
```

**Pass Criteria:**
- [ ] Returns 200 status
- [ ] Lists only user's groups
- [ ] Includes summary data (total_claims, total_compensation, status_summary)

#### 3.3 Get Claim Group Detail API
```bash
curl https://eac.dvvcloud.work/api/v1/claim-groups/$GROUP_ID \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK with full details
```

**Pass Criteria:**
- [ ] Returns 200 status
- [ ] Returns 404 if group not found
- [ ] Returns 403 if not authorized
- [ ] Includes all claims in group

#### 3.4 Confirm Consent API
```bash
curl -X POST https://eac.dvvcloud.work/api/v1/claim-groups/$GROUP_ID/consent \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
```

**Pass Criteria:**
- [ ] Updates consent_confirmed to true
- [ ] Records consent_confirmed_at timestamp
- [ ] Records IP address

---

## PHASE 4: WP #365 - Admin Dashboard UI

### Objective
Test the admin interface for managing claim groups.

### Test Steps

#### 4.1 Admin Claim Groups List
1. Login as admin
2. Navigate to: https://eac.dvvcloud.work/panel/claim-groups
3. **VERIFY**: Claim groups list page loads
4. **VERIFY**: Filters available (status, date range, flight number)
5. **VERIFY**: Search box functional
6. **VERIFY**: Group cards displayed with:
   - Group name
   - Flight info
   - Passenger count
   - Status badge
   - Total compensation

**Pass Criteria:**
- [ ] Page loads without errors
- [ ] Filters work correctly
- [ ] Responsive layout

#### 4.2 Admin Group Detail View
1. Click on a claim group card
2. **VERIFY**: Detail view loads
3. **VERIFY**: Shows:
   - Group header with flight info
   - Consent status indicator
   - List of all claims in group
   - Individual claim details
   - Bulk action buttons (Approve All, Reject All, Request Info)
   - Notes section
   - Total compensation card

**Pass Criteria:**
- [ ] All information displayed
- [ ] Layout is clear and organized
- [ ] Navigation works (back button)

#### 4.3 Admin Add Note
1. In group detail view, scroll to notes section
2. Enter note text: "Test note from admin"
3. Click "Add Note"
4. **VERIFY**: Note appears in list
5. **VERIFY**: Timestamp and admin info shown

**Pass Criteria:**
- [ ] Note saved successfully
- [ ] Appears immediately in UI
- [ ] Proper attribution

---

## PHASE 5: WP #364 - Admin API Endpoints

### Objective
Test admin-only API endpoints.

### Test Steps

#### 5.1 List All Claim Groups (Admin)
```bash
curl https://eac.dvvcloud.work/api/v1/admin/claim-groups \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: 200 OK with all groups
```

**Pass Criteria:**
- [ ] Returns 200
- [ ] Lists all groups (not just admin's)
- [ ] Supports filters via query params

#### 5.2 Admin Bulk Approve
```bash
curl -X PUT https://eac.dvvcloud.work/api/v1/admin/claim-groups/$GROUP_ID/bulk-action \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "approve_all"}'

# Expected: 200 OK
# Response: { success: true, updated_count: X, total_claims: Y }
```

**Pass Criteria:**
- [ ] All claims in group updated to "approved"
- [ ] Correct count returned
- [ ] Updates visible in customer dashboard

#### 5.3 Admin Bulk Reject
```bash
curl -X PUT .../bulk-action \
  -d '{"action": "reject_all", "rejection_reason": "Test bulk rejection"}'

# Expected: 200 OK
```

**Pass Criteria:**
- [ ] All claims updated to "rejected"
- [ ] Rejection reason saved
- [ ] Customer sees rejection with reason

#### 5.4 Admin Add Note API
```bash
curl -X POST .../notes \
  -H "Content-Type: application/json" \
  -d '{"note_text": "Admin note from API test"}'

# Expected: 201 Created
```

**Pass Criteria:**
- [ ] Note created
- [ ] Associated with correct group
- [ ] Admin ID recorded

---

## PHASE 6: Integration Testing - Full Flow

### Objective
Test complete end-to-end multi-passenger claim flow.

### Test Steps

#### 6.1 Complete Multi-Passenger Claim Submission
1. **Customer**: Submit claim for UA988 on 2025-08-18 with 3 passengers
   - Passenger 1: Account holder (John Smith)
   - Passenger 2: Spouse (Jane Smith)
   - Passenger 3: Child (Emily Smith)
2. **VERIFY**: Consent checkbox shown and required
3. **VERIFY**: All 3 passengers saved
4. **VERIFY**: Claim group created automatically
5. **VERIFY**: Group appears in customer dashboard

#### 6.2 Admin Reviews and Approves
1. **Admin**: Navigate to claim groups
2. **Admin**: View the new group
3. **Admin**: Add note: "All documents verified"
4. **Admin**: Click "Approve All"
5. **VERIFY**: All 3 claims marked approved
6. **VERIFY**: Customer sees updated status

#### 6.3 Customer Views Approved Claims
1. **Customer**: Check dashboard
2. **VERIFY**: Group shows "Approved" status
3. **VERIFY**: Total compensation displayed
4. **VERIFY**: Individual claims show approved

---

## PHASE 7: Bug Fixes

### Process
1. Review all documented bugs from Phases 1-6
2. Categorize by severity (Critical, High, Medium, Low)
3. Fix in order of severity
4. Re-test fixed bugs
5. Document any remaining issues

### Expected Bug Types
- UI/UX issues (alignment, colors, wording)
- API validation errors
- Data synchronization issues
- Mobile responsiveness problems

---

## PHASE 8: Final Verification

### 8.1 Regression Testing
- Re-test single passenger flow (ensure no regression)
- Re-test existing claims functionality
- Verify no broken features

### 8.2 Documentation
- Update API documentation if needed
- Document any known limitations
- Create user guide for claim groups (if needed)

### 8.3 Performance Check
- Test with 10+ passengers in group
- Verify response times acceptable
- Check for any memory leaks

---

## TESTING TIMELINE ESTIMATE

| Phase | Estimated Time | Parallelizable |
|-------|---------------|----------------|
| Phase 0 | 15 min | No |
| Phase 1 | 30 min | No |
| Phase 2 | 20 min | No |
| Phase 3 | 30 min | No |
| Phase 4 | 25 min | No |
| Phase 5 | 25 min | No |
| Phase 6 | 40 min | No |
| Phase 7 | Varies | No |
| Phase 8 | 30 min | No |

**Total**: ~3.5 hours (excluding bug fixes)

---

## SUCCESS CRITERIA

### Must Pass (Critical)
- [ ] Customer can submit multi-passenger claim
- [ ] Consent validation works
- [ ] Claim groups appear in dashboard
- [ ] Admin can bulk approve/reject
- [ ] All APIs return correct data
- [ ] No 500 errors

### Should Pass (High Priority)
- [ ] Mobile responsive
- [ ] Good performance
- [ ] Clear error messages
- [ ] Smooth UX

### Nice to Have (Medium Priority)
- [ ] Advanced filters work
- [ ] Edge cases handled gracefully

---

## ROLLBACK PLAN

If critical issues found:
1. Document all issues
2. Create fix branch from feature branch
3. Fix issues
4. Re-test
5. Merge to MVP only when all critical tests pass

---

**Plan Created**: 2026-02-13
**Test Flight**: UA988 on 2025-08-18 (FRA→IAD, 3+ hour delay)
**Approach**: Sequential testing, document bugs, fix after complete
**Expected Duration**: 3.5-5 hours
