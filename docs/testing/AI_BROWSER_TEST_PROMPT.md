# AI Browser Agent Testing Prompt - Phase 2: Email Notifications & Async Processing

## Context & Mission

You are an AI agent controlling a web browser to test the **Phase 2 release** of the EasyAirClaim Flight Compensation System. Your mission is to comprehensively test the new email notification system and async task processing via Celery.

**What you're testing:**
- ✅ Claim submitted confirmation emails
- ✅ Status update notification emails (approved, rejected, paid)
- ✅ Document rejection notification emails
- ✅ Background task processing with Celery
- ✅ Email template rendering and content accuracy

**Test Environment:**
- API Base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- API is running with FastAPI + Celery worker + Redis

## Important Testing Notes

### Email Configuration Status
⚠️ **CRITICAL**: Check if emails are actually sending or if testing is in mock mode:
- If `NOTIFICATIONS_ENABLED=false` in .env: Emails won't send, but API should still work
- If `NOTIFICATIONS_ENABLED=true`: Emails should be sent via SMTP
- Document in your report whether emails were actually received or if testing was API-only

### What Success Looks Like
- All API endpoints return 200/201 responses
- No 500 errors or crashes
- Email tasks are queued to Celery (check Celery logs if possible)
- Response data structure matches expectations
- All required fields are present in responses

## Testing Protocol

### Phase 1: Setup & Verification

**Step 1.1: Access Swagger UI**
1. Navigate to `http://localhost:8000/docs`
2. Verify the page loads successfully
3. Document: Number of available endpoints shown

**Step 1.2: Test Health Endpoint**
1. Find `GET /health` endpoint
2. Click "Try it out" → "Execute"
3. Verify response:
   - Status code: 200
   - Response body contains: `{"status": "healthy", "timestamp": ..., "version": ...}`
4. Document any issues

---

### Phase 2: Create Test Customer

**Step 2.1: Create Customer**
1. Find `POST /customers/` endpoint
2. Click "Try it out"
3. Use this test data:
```json
{
  "email": "test.phase2@example.com",
  "firstName": "Phase",
  "lastName": "TwoTester",
  "phone": "+1234567890",
  "address": {
    "street": "123 Test Street",
    "city": "Test City",
    "postalCode": "12345",
    "country": "USA"
  }
}
```
4. Click "Execute"
5. **CRITICAL**: Copy and save the customer `id` from the response (UUID format)
6. Verify response:
   - Status code: 201
   - Response contains all submitted fields
   - `id`, `createdAt`, `updatedAt` fields are present
7. Document:
   - Customer ID: `[paste UUID here]`
   - Any missing or incorrect fields

**Expected Response Example:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "test.phase2@example.com",
  "firstName": "Phase",
  "lastName": "TwoTester",
  ...
}
```

---

### Phase 3: Test Email #1 - Claim Submitted Email

**Step 3.1: Submit a Claim**
1. Find `POST /claims/` endpoint
2. Click "Try it out"
3. **IMPORTANT**: Replace `CUSTOMER_ID_HERE` with the UUID from Step 2.1
```json
{
  "customer_id": "CUSTOMER_ID_HERE",
  "flight_info": {
    "flight_number": "LH456",
    "airline": "Lufthansa",
    "departure_date": "2025-11-15",
    "departure_airport": "FRA",
    "arrival_airport": "JFK",
    "scheduled_departure": "2025-11-15T10:00:00Z",
    "actual_departure": "2025-11-15T14:30:00Z"
  },
  "incident_type": "delay",
  "description": "Flight was delayed by 4.5 hours due to technical issues. Missed connecting flight.",
  "notes": "Test claim for Phase 2 email notification testing"
}
```
4. Click "Execute"
5. **CRITICAL**: Save the claim `id` from response
6. Verify response:
   - Status code: 201
   - Claim has status `"submitted"`
   - All flight info matches
   - Has `id`, `customer_id`, `status`, `submitted_at` fields

7. Document:
   - Claim ID: `[paste UUID here]`
   - Claim Status: `[should be "submitted"]`
   - Any errors or missing data

**Step 3.2: Verify Email Task Triggered**
- Note: If you have access to Celery logs, you should see:
  ```
  [INFO] Task send_claim_submitted_email[task-id] received
  [INFO] Task started: Sending claim submitted email
  [INFO] Email sent successfully
  ```
- Document: Whether you saw Celery task activity (if logs accessible)

**Step 3.3: Expected Email Content** (if emails are enabled)
- **To**: test.phase2@example.com
- **From**: EasyAirClaim Support (or configured from address)
- **Subject**: "Claim Submitted - Lufthansa LH456"
- **Content Should Include**:
  - Greeting: "Hello Phase TwoTester"
  - Claim ID
  - Flight details: LH456, FRA → JFK
  - Airline: Lufthansa
  - Incident type: Delay
  - "What happens next?" section
  - Professional HTML formatting

---

### Phase 4: Test Email #2 - Status Update (Approved)

**Step 4.1: Update Claim Status to Approved**
1. Find `PUT /admin/claims/{claim_id}/status` endpoint
2. Click "Try it out"
3. Enter your claim ID in the `claim_id` parameter field
4. **IMPORTANT**: Add required header:
   - Click "Add string item" under Parameters
   - Header name: `X-Admin-ID`
   - Value: `11111111-1111-1111-1111-111111111111` (any valid UUID)
5. Request body:
```json
{
  "new_status": "approved",
  "change_reason": "All documents verified. Flight confirmed delayed by 4.5 hours. Customer eligible for €600 compensation under EU261/2004."
}
```
6. Click "Execute"
7. Verify response:
   - Status code: 200
   - `status` is now `"approved"`
   - `compensation_amount` field present (should be 600.00)
   - `status_history` array shows the change

8. Document:
   - New status: `[should be "approved"]`
   - Compensation amount: `[should be 600.00]`
   - Status history contains previous status `"submitted"`
   - Any errors

**Step 4.2: Expected Email Content** (if emails enabled)
- **Subject**: "Claim Status Update - Approved"
- **Content Should Include**:
  - Green header or approved styling
  - Status change: "Submitted → Approved"
  - Compensation amount: €600
  - Change reason displayed
  - "What happens next?" for approved claims
  - Professional HTML formatting

---

### Phase 5: Test Email #2B - Status Update (Rejected)

**Step 5.1: Create Second Claim** (for rejection test)
1. Use `POST /claims/` again with same customer ID
2. Change flight number to `"BA789"`, airline to `"British Airways"`
3. Save the new claim ID

**Step 5.2: Update to Rejected Status**
1. Use `PUT /admin/claims/{claim_id}/status`
2. Use the NEW claim ID from Step 5.1
3. Add `X-Admin-ID` header
4. Request body:
```json
{
  "new_status": "rejected",
  "change_reason": "Flight delay was less than 3 hours. Not eligible for compensation under EU261/2004. Delay was 2 hours 45 minutes."
}
```
5. Click "Execute"
6. Verify response:
   - Status: 200
   - New status: `"rejected"`
   - Reason stored in status history

7. Document:
   - Status updated successfully: Yes/No
   - Rejection reason visible: Yes/No
   - Any errors

**Step 5.3: Expected Email Content** (if emails enabled)
- **Subject**: "Claim Status Update - Rejected"
- **Content Should Include**:
  - Red/warning header styling
  - Status: "Rejected"
  - Rejection reason clearly displayed
  - Information about next steps for rejected claims

---

### Phase 6: Test Email #2C - Status Update (Paid)

**Step 6.1: Update First Claim to Paid**
1. Use `PUT /admin/claims/{claim_id}/status`
2. Use the FIRST claim ID (the one that's approved)
3. Add `X-Admin-ID` header
4. Request body:
```json
{
  "new_status": "paid",
  "change_reason": "Payment of €600 processed successfully via SEPA transfer. Reference: PAY-2025-001"
}
```
5. Click "Execute"
6. Verify:
   - Status: 200
   - New status: `"paid"`
   - Status history shows: submitted → approved → paid

7. Document the status transition chain

**Step 6.2: Expected Email Content** (if emails enabled)
- **Subject**: "Claim Status Update - Paid"
- **Content Should Include**:
  - Blue/success header styling
  - "Payment Processed" confirmation
  - Compensation amount: €600
  - Payment reference: PAY-2025-001
  - Timeline for funds to arrive

---

### Phase 7: Test Email #3 - Document Rejected Email

**Step 7.1: Upload a Test Document**
1. Find `POST /files/upload` endpoint
2. Click "Try it out"
3. Fill in the form:
   - `file`: Upload ANY small file (PDF, JPG, PNG - doesn't matter for testing)
   - `claim_id`: Use your first claim ID
   - `document_type`: Select `boarding_pass`
4. **IMPORTANT**: Add header:
   - Header: `X-Customer-ID`
   - Value: Your customer UUID
5. Click "Execute"
6. **CRITICAL**: Save the `file_id` from response
7. Verify:
   - Status: 201
   - Response has `id`, `file_name`, `document_type`, `status` fields
   - Status should be `"pending_review"`

8. Document:
   - File ID: `[paste UUID]`
   - File uploaded successfully: Yes/No
   - Any errors

**Step 7.2: Reject the Document**
1. Find `PUT /admin/files/{file_id}/review` endpoint
2. Click "Try it out"
3. Enter your file ID
4. Add header `X-Admin-ID`: `11111111-1111-1111-1111-111111111111`
5. Request body:
```json
{
  "approved": false,
  "rejection_reason": "Image is too blurry. Unable to read passenger name, flight number, and boarding time. Please upload a clearer, higher resolution image.",
  "reviewer_notes": "Customer needs to re-upload boarding pass. Common issue with mobile photos."
}
```
6. Click "Execute"
7. Verify:
   - Status: 200
   - File status now `"rejected"`
   - Rejection reason stored

8. Document:
   - File status updated: Yes/No
   - Rejection reason: `[paste reason]`
   - Any errors

**Step 7.3: Expected Email Content** (if emails enabled)
- **Subject**: "Document Re-upload Required - Boarding Pass"
- **Content Should Include**:
  - Orange/warning header
  - Document type: Boarding Pass
  - Rejection reason clearly stated
  - "Tips for successful upload" section
  - Action required: "Please re-upload"
  - Claim ID reference

---

### Phase 8: Edge Cases & Error Scenarios

**Test 8.1: Invalid Customer ID**
1. Try `POST /claims/` with non-existent customer ID: `"99999999-9999-9999-9999-999999999999"`
2. Expected: 404 or 422 error
3. Document: Actual status code and error message

**Test 8.2: Invalid Status Transition**
1. Try updating the PAID claim to "submitted" (backwards transition)
2. Expected: 400 error with message about invalid transition
3. Document: Error handling quality

**Test 8.3: Missing Required Fields**
1. Try creating claim without `customer_id`
2. Expected: 422 validation error
3. Document: Error message clarity

**Test 8.4: Invalid Admin Header**
1. Try updating claim status without `X-Admin-ID` header
2. Expected: 401 or 403 error
3. Document: Security validation working

---

### Phase 9: API Consistency Checks

**Test 9.1: Get Customer by ID**
1. Use `GET /customers/{customer_id}` with your test customer
2. Verify all data matches what was submitted
3. Document any discrepancies

**Test 9.2: List Claims**
1. Use `GET /claims/` with `customer_id` query parameter
2. Should return your 2 test claims
3. Verify both claims are present with correct statuses

**Test 9.3: Get Claim Details**
1. Use `GET /claims/{claim_id}`
2. Check if status history is included
3. Verify compensation calculations are correct

**Test 9.4: List Files**
1. Use `GET /files/` with your claim ID
2. Should show your uploaded file with "rejected" status
3. Verify file metadata is complete

---

## Comprehensive Test Report Template

At the end of testing, generate a report with this structure:

```markdown
# Phase 2 Testing Report - Email Notifications & Async Processing

## Test Execution Summary
- **Date**: [timestamp]
- **Duration**: [total time]
- **API Base URL**: http://localhost:8000
- **Email Notifications Enabled**: Yes/No
- **Total Tests**: 30+
- **Passed**: X
- **Failed**: Y
- **Warnings**: Z

## Test Environment Status
- FastAPI Health: ✅/❌
- Swagger UI Accessible: ✅/❌
- Database Connection: ✅/❌ (inferred from API responses)
- Celery Worker Status: ✅/❌/Unknown

## Feature Test Results

### 1. Customer Management
- Create Customer: ✅/❌
- Customer ID Generated: `[UUID]`
- Data Integrity: ✅/❌
- Issues: [none or describe]

### 2. Claim Submission Email
- Claim Created Successfully: ✅/❌
- Claim ID: `[UUID]`
- Status: `[submitted]`
- Email Task Triggered: ✅/❌/Unknown
- Expected Email Content: [describe or N/A if emails disabled]
- Issues: [none or describe]

### 3. Status Update Emails

#### 3.1 Approved Status
- Status Update Success: ✅/❌
- Compensation Calculated: ✅/❌ (€600)
- Email Content Expected: [describe or N/A]
- Issues: [none or describe]

#### 3.2 Rejected Status
- Status Update Success: ✅/❌
- Rejection Reason Stored: ✅/❌
- Email Content Expected: [describe or N/A]
- Issues: [none or describe]

#### 3.3 Paid Status
- Status Update Success: ✅/❌
- Status Transition Valid: ✅/❌
- Email Content Expected: [describe or N/A]
- Issues: [none or describe]

### 4. Document Rejection Email
- File Upload Success: ✅/❌
- File ID: `[UUID]`
- Document Rejection Success: ✅/❌
- Rejection Reason Stored: ✅/❌
- Email Content Expected: [describe or N/A]
- Issues: [none or describe]

### 5. Error Handling
- Invalid Customer ID: ✅/❌ (Status: [code])
- Invalid Status Transition: ✅/❌ (Status: [code])
- Missing Required Fields: ✅/❌ (Status: [code])
- Missing Admin Header: ✅/❌ (Status: [code])

### 6. API Consistency
- Get Customer: ✅/❌
- List Claims: ✅/❌ (Found [X] claims)
- Get Claim Details: ✅/❌
- List Files: ✅/❌

## Critical Issues Found
[List any blocking issues here]

1. Issue: [description]
   - Severity: Critical/High/Medium/Low
   - Steps to Reproduce: [steps]
   - Expected: [expected behavior]
   - Actual: [actual behavior]
   - API Endpoint: [endpoint]
   - Status Code: [code]

## Warnings & Non-Critical Issues
[List any warnings or minor issues]

## Performance Observations
- Average API Response Time: [if measurable]
- Slowest Endpoint: [endpoint] ([time])
- Celery Task Queue: Working/Unknown
- Email Delivery: Immediate/Delayed/N/A

## Email Notification Quality (if enabled)
- HTML Rendering: ✅/❌/N/A
- Content Accuracy: ✅/❌/N/A
- Personalization: ✅/❌/N/A (customer name, claim details)
- Formatting: Professional/Needs Work/N/A
- Mobile Responsive: Unknown/Good/Poor/N/A

## API Documentation Quality
- Swagger UI Completeness: Good/Needs Work
- Request Examples: Clear/Confusing
- Response Schemas: Accurate/Inaccurate
- Error Messages: Helpful/Cryptic

## Test Data Generated
- Customer ID: `[UUID]`
- Claim IDs: `[UUID1]`, `[UUID2]`
- File ID: `[UUID]`
- Emails Expected: 6 total (1 submitted + 3 status + 1 rejected doc + 1 more status)

## Recommendations for Phase 3

1. [Based on findings, suggest improvements]
2. [Security considerations]
3. [UX improvements]
4. [Technical debt]

## Overall Assessment
**Phase 2 Status**: ✅ Ready for Production / ⚠️ Ready with Caveats / ❌ Not Ready

**Summary**: [2-3 sentences summarizing the state of Phase 2]

**Email System**: [Working as expected / Has issues / Could not test]

**Async Processing**: [Verified working / Could not verify / Has issues]

---

## Appendix: API Response Examples

### Sample Claim Response
```json
[paste actual response]
```

### Sample Error Response
```json
[paste actual error]
```

### Celery Logs (if accessible)
```
[paste relevant logs]
```

---

**Report Generated**: [timestamp]
**Tester**: AI Browser Agent
**Next Steps**: [Suggest immediate fixes or proceed to Phase 3]
```

## Testing Guidelines

### Do's ✅
- Be thorough - test every scenario listed
- Copy exact UUIDs and data from responses
- Document EVERYTHING, even if it works perfectly
- Take note of response times if very slow
- Check for console errors in browser dev tools
- Verify data types match expectations
- Test with realistic data

### Don'ts ❌
- Don't skip error scenarios
- Don't assume features work without testing
- Don't forget to document which endpoints you used
- Don't rush through the tests
- Don't ignore warning messages
- Don't modify test data mid-test (keep it consistent)

## Important Notes

1. **Email Testing**: If emails are not actually being sent (NOTIFICATIONS_ENABLED=false), focus on API functionality and that email tasks would be queued correctly.

2. **Celery Logs**: If you can access Celery worker logs, include any relevant output about task processing.

3. **Security Headers**: Note that this is a development environment. The X-Customer-ID and X-Admin-ID headers are temporary and will be replaced with JWT authentication in Phase 3.

4. **Compensation Calculation**: The API should automatically calculate compensation based on flight distance and delay duration. Document if calculations seem incorrect.

5. **Data Persistence**: All data should persist across API calls. If you refresh or retry a GET endpoint, data should be consistent.

## Success Criteria

Phase 2 passes testing if:
- ✅ All CRUD operations work (Create, Read, Update, Delete)
- ✅ Email tasks are triggered for all 6 scenarios
- ✅ No 500 errors occur during normal operations
- ✅ Error handling is appropriate (4xx errors for bad requests)
- ✅ Data integrity is maintained
- ✅ Status transitions follow business logic
- ✅ Compensation calculations are accurate
- ✅ API responses are consistent and complete

## Quick Reference: API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/customers/` | Create customer |
| GET | `/customers/{id}` | Get customer |
| POST | `/claims/` | Create claim |
| GET | `/claims/{id}` | Get claim |
| GET | `/claims/` | List claims |
| PUT | `/admin/claims/{id}/status` | Update claim status |
| POST | `/files/upload` | Upload document |
| PUT | `/admin/files/{id}/review` | Review document |
| GET | `/files/` | List files |

---

**Good luck with testing! Be thorough and document everything.**
