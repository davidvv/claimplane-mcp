# API Integration Test Report

**Date:** January 13, 2026  
**Test Environment:** localhost:8000 (API), localhost:80 (Frontend)  
**Branch:** workflow

---

## Executive Summary

Tested all API endpoints used by the claim workflow UI. **Most endpoints work correctly.** Found 2 minor issues that should be addressed for consistency.

---

## Test Results Summary

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/health` | GET | ✅ PASS | Returns healthy status |
| `/eligibility/check` | POST | ✅ PASS | Requires flat schema |
| `/claims/draft` | POST | ✅ PASS | Creates draft claim |
| `/claims/submit` | POST | ✅ PASS | Works with correct schema |
| `/claims/{id}` | GET | ✅ PASS | Returns claim details |
| `/claims/` | GET | ✅ PASS | Returns claim list |
| `/claims/{id}/documents` | GET | ✅ PASS | Returns document list |
| `/claims/{id}/documents` | POST | ✅ PASS | Uploads documents |
| `/customers/me` | GET | ✅ PASS | Returns customer profile |
| `/customers/me` | PUT | ⚠️ PARTIAL | Requires email (should be optional) |
| `/auth/magic-link/request` | POST | ✅ PASS | Sends magic link |

---

## Detailed Test Results

### 1. Health Check ✅
```
GET /health
Response: 200 OK
Body: {"status":"healthy","timestamp":"2026-01-13T09:24:16.940884","version":"1.0.0"}
```

### 2. Eligibility Check ✅
```
POST /eligibility/check
Body: {"departure_airport":"FRA","arrival_airport":"JFK","delay_hours":5.0,"incident_type":"delay"}
Response: 200 OK
Body: {"eligible":true,"amount":"600","distance_km":6187.97,"reason":"Delay of 5.0 hours qualifies for full compensation","requires_manual_review":false}
```
**Note:** This endpoint uses a flat schema (no nested flight_info/customer_info).

### 3. Create Draft Claim ✅
```
POST /claims/draft
Body: {"email":"test@example.com","flight_info":{...},"incident_type":"delay"}
Response: 201 Created
Claim ID: 26b0b963-367e-4c1a-9b46-c58cba8592b9
Access Token: eyJhbGci... (JWT token)
```

### 4. Get Claim ✅
```
GET /claims/26b0b963-367e-4c1a-9b46-c58cba8592b9
Headers: Authorization: Bearer <token>
Response: 200 OK
Body: Full claim details with flightInfo, status, timestamps
```

### 5. List Claims ✅
```
GET /claims/
Headers: Authorization: Bearer <token>
Response: 200 OK
Body: Array of claims (found 2 claims in test)
```

### 6. List Documents ✅
```
GET /claims/{id}/documents
Headers: Authorization: Bearer <token>
Response: 200 OK
Body: Array of documents (empty for new claims)
```

### 7. Upload Document ✅
```
POST /claims/{id}/documents
Headers: Authorization: Bearer <token>
Body: multipart/form-data with file and document_type
Response: 201 Created
Body: {"id":"199387be-...","filename":"3cbdd73e-...pdf","originalFilename":"test_boarding_pass.pdf",...}
```
**Note:** File must be a real file with valid MIME type (PDF, JPG, PNG).

### 8. Get Customer Profile ✅
```
GET /customers/me
Headers: Authorization: Bearer <token>
Response: 200 OK
Body: {"id":"bede705c-...","email":"test@example.com","firstName":"","lastName":"",...}
```

### 9. Update Customer ⚠️ (Requires Email)
```
PUT /customers/me
Headers: Authorization: Bearer <token>
Body: {"email":"test@example.com","first_name":"Updated","last_name":"User","phone":"+1987654321"}
Response: 200 OK
```
**Issue:** The endpoint requires `email` field even though the user is already authenticated via JWT token. The email should be optional for authenticated users since it's already known from the token.

### 10. Submit Claim ✅
```
POST /claims/submit
Body: {
  "customer_info": {
    "email": "test_submit2@example.com",
    "first_name": "Submit",
    "last_name": "Test",
    ...
  },
  "flight_info": {...},
  "incident_type": "delay",
  "terms_accepted": true
}
Response: 201 Created
Body: {"claim":{...},"accessToken":"...","tokenType":"bearer"}
```
**Note:** The backend expects `email` inside `customer_info`, not at the top level.

### 11. Auth Magic Link ✅
```
POST /auth/magic-link/request
Body: {"email":"test@example.com"}
Response: 200 OK
Body: {"message":"If an account exists with this email, a magic link has been sent"}
```

---

## Issues Found

### Issue 1: Update Customer Requires Email (Minor)
**Endpoint:** `PUT /customers/me`  
**Severity:** Low  
**Description:** The endpoint requires `email` in the request body, but the user is already authenticated via JWT token which contains their email. Making email optional would improve UX.

**Current behavior:**
```json
// 422 Error when email missing
{"detail":[{"type":"missing","loc":["body","email"],"msg":"Field required"}]}
```

**Expected behavior:** Email should be optional for authenticated users.

---

### Issue 2: Schema Inconsistency Between Draft and Submit (Frontend Issue)
**Endpoints:** `POST /claims/draft` vs `POST /claims/submit`  
**Severity:** Low  
**Description:** The two endpoints have different payload structures for email:

- `/claims/draft`: Expects `email` at top level
- `/claims/submit`: Expects `email` inside `customer_info`

**Impact:** The frontend needs to handle both structures correctly.

**Recommendation:** Either:
1. Make both endpoints consistent (email inside customer_info for both)
2. Or document the difference clearly

---

## Frontend Compatibility Notes

Based on API testing, the frontend should:

1. **Eligibility Check (Step 1 → 2):**
   - Send flat payload: `{"departure_airport":"FRA","arrival_airport":"JFK",...}`

2. **Draft Creation (Step 2 → 3):**
   - Send email at top level: `{"email":"...","flight_info":{...},"incident_type":"..."}`

3. **Submit Claim (Step 4):**
   - Send email inside customer_info:
   ```json
   {
     "customer_info": {
       "email": "...",
       "first_name": "...",
       ...
     },
     "flight_info": {...},
     "incident_type": "...",
     "terms_accepted": true
   }
   ```

4. **Document Upload:**
   - Use real files (not /dev/null)
   - Include Authorization header with Bearer token
   - Use multipart/form-data content type

---

## Recommendations

1. **Fix Update Customer:** Make email field optional in `CustomerUpdateSchema` since the user is already authenticated.

2. **Standardize Email Handling:** Consider making both draft and submit endpoints expect email inside `customer_info` for consistency.

3. **Add API Documentation:** Document the expected request schemas clearly for each endpoint.

4. **Add Integration Tests:** Create a test suite that runs these API tests automatically on each deployment.

---

## Test Files Created

- `/home/david/easyAirClaim/claimplane/tests/test_api_workflow.py` - Comprehensive async API test script

Run with:
```bash
python3 tests/test_api_workflow.py
```

---

## Conclusion

The API is functioning correctly. All core endpoints work as expected. The two minor issues found are:
1. Update customer requiring email (low severity)
2. Schema inconsistency between draft and submit (low severity, frontend can handle)

The claim workflow is ready for use with these minor considerations.
