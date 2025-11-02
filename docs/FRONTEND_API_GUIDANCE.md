# Frontend API Guidance

**Audience**: Frontend/UI Developer
**Date**: 2025-11-02
**Status**: ✅ IMPLEMENTED - Eligibility Check Endpoint Available

---

## 📋 Requested Endpoints - Implementation Status

### 1. ✅ Eligibility Check Endpoint - IMPLEMENTED

**Endpoint**: `POST /eligibility/check`
**Status**: ✅ **Live and ready to use**
**Authentication**: None required (public endpoint)

#### Request

```bash
POST /eligibility/check
Content-Type: application/json

{
  "departure_airport": "MAD",     # IATA code (3 letters)
  "arrival_airport": "JFK",       # IATA code (3 letters)
  "delay_hours": 5.0,             # Optional, delay in hours
  "incident_type": "delay"        # delay, cancellation, denied_boarding, baggage_delay
}
```

#### Response

```json
{
  "eligible": true,
  "amount": "600",
  "distance_km": 5762.05,
  "reason": "Delay of 5.0 hours qualifies for full compensation",
  "requires_manual_review": false
}
```

#### Example Usage

```bash
# Example 1: Long-haul flight with eligible delay
curl -X POST http://localhost:8000/eligibility/check \
  -H "Content-Type: application/json" \
  -d '{
    "departure_airport": "MAD",
    "arrival_airport": "JFK",
    "delay_hours": 5.0,
    "incident_type": "delay"
  }'

# Response: {"eligible":true,"amount":"600","distance_km":5762.05,...}

# Example 2: Short-haul with insufficient delay
curl -X POST http://localhost:8000/eligibility/check \
  -H "Content-Type: application/json" \
  -d '{
    "departure_airport": "BCN",
    "arrival_airport": "LHR",
    "delay_hours": 2.5,
    "incident_type": "delay"
  }'

# Response: {"eligible":false,"amount":"0","distance_km":1147.58,...}

# Example 3: Cancellation
curl -X POST http://localhost:8000/eligibility/check \
  -H "Content-Type: application/json" \
  -d '{
    "departure_airport": "FRA",
    "arrival_airport": "AMS",
    "incident_type": "cancellation"
  }'

# Response: {"eligible":true,"amount":"250","distance_km":365.71,...}
```

#### Compensation Rules (EU261/2004)

| Distance | Compensation | Notes |
|----------|--------------|-------|
| < 1,500 km | €250 | Short-haul |
| 1,500 - 3,500 km | €400 | Medium-haul |
| > 3,500 km | €600 | Long-haul |

**Minimum delay**: 3 hours

**Use Cases**:
- Landing page eligibility calculator
- Pre-submission eligibility check
- Marketing funnels
- Customer self-service tools

---

### 2. ❌ Get Claims by Email - NOT IMPLEMENTED

**Endpoint**: `GET /claims/by-email/{email}`
**Status**: ❌ **Not implemented - Security risk**
**Reason**: Information disclosure vulnerability

#### Why This Endpoint Is Dangerous

```
GET /claims/by-email/victim@example.com
→ Returns all claims for victim@example.com
→ No authentication required
→ Anyone can access anyone's claims
```

**Security Issues**:
- Email addresses are not secret (publicly available, easy to guess)
- Exposes PII: names, flight details, claim amounts, addresses
- Privacy/GDPR violation
- Can be scraped/enumerated

#### What to Use Instead

**Current secure alternative**: `GET /claims/customer/{customer_id}`

```bash
# Get claims by customer UUID (more secure)
GET /claims/customer/{customer_id}
Headers: X-Customer-ID: {customer_id}
```

**Recommendation**:
1. Store customer UUID locally after registration/claim submission
2. Use customer UUID for subsequent requests
3. Wait for proper authentication before implementing email-based lookups

---

## 🎯 Available API Endpoints

### Public Endpoints (No Auth Required)

```
POST /eligibility/check
  - Check flight compensation eligibility
  - Body: { departure_airport, arrival_airport, delay_hours, incident_type }
  - Returns: { eligible, amount, distance_km, reason, requires_manual_review }
```

### Customer Endpoints (Require X-Customer-ID Header)

**⚠️ Note**: Current header-based auth is for development only.

```
POST /claims/submit
  - Submit new claim with customer info
  - Creates customer if doesn't exist
  - Body: { customer_info, flight_info, incident_type, notes }
  - Returns: Claim object with ID

GET /claims/customer/{customer_id}
  - Get all claims for specific customer
  - Returns: List of claims

GET /claims/{claim_id}
  - Get single claim details
  - Returns: Claim object

POST /files/upload/{claim_id}
  - Upload document for claim
  - Multipart form data
  - Returns: File metadata

GET /files/download/{file_id}
  - Download file
  - Returns: File stream
```

### Admin Endpoints (Require X-Admin-ID Header)

**⚠️ Note**: For development/internal use only.

```
GET /admin/claims
  - List all claims with filters
  - Query params: skip, limit, status

PUT /admin/claims/{claim_id}/status
  - Update claim status
  - Body: { new_status, change_reason }
  - Triggers email notification

POST /admin/claims/{claim_id}/notes
  - Add admin note to claim

GET /admin/files
  - List all files with filters
```

---

## 🔧 Integration Guide

### Eligibility Check Flow

```javascript
// Frontend example - Eligibility calculator
async function checkEligibility(flightDetails) {
  const response = await fetch('http://localhost:8000/eligibility/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      departure_airport: flightDetails.from,
      arrival_airport: flightDetails.to,
      delay_hours: flightDetails.delayHours,
      incident_type: flightDetails.type
    })
  });

  const result = await response.json();

  if (result.eligible) {
    console.log(`Eligible for €${result.amount} compensation`);
  } else {
    console.log(`Not eligible: ${result.reason}`);
  }

  return result;
}

// Usage
checkEligibility({
  from: 'MAD',
  to: 'JFK',
  delayHours: 5.0,
  type: 'delay'
});
```

### Claim Submission Flow

```javascript
// Frontend example - Submit claim with customer info
async function submitClaim(customerInfo, flightInfo) {
  const response = await fetch('http://localhost:8000/claims/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      customer_info: {
        email: customerInfo.email,
        first_name: customerInfo.firstName,
        last_name: customerInfo.lastName,
        phone: customerInfo.phone,
        address: customerInfo.address
      },
      flight_info: {
        flight_number: flightInfo.flightNumber,
        airline: flightInfo.airline,
        departure_date: flightInfo.date,
        departure_airport: flightInfo.from,
        arrival_airport: flightInfo.to
      },
      incident_type: flightInfo.incidentType,
      notes: flightInfo.notes
    })
  });

  const claim = await response.json();

  // Store customer ID and claim ID for future requests
  localStorage.setItem('customerId', claim.customer_id);
  localStorage.setItem('lastClaimId', claim.id);

  return claim;
}
```

### Get Customer Claims

```javascript
// Frontend example - Get customer's claims
async function getCustomerClaims(customerId) {
  const response = await fetch(`http://localhost:8000/claims/customer/${customerId}`, {
    headers: {
      'X-Customer-ID': customerId  // Development only - will change to JWT
    }
  });

  const claims = await response.json();
  return claims;
}
```

---

## 📚 Response Schemas

### EligibilityResponse

```typescript
interface EligibilityResponse {
  eligible: boolean;           // Whether claim qualifies for compensation
  amount: string;              // Compensation amount in EUR (Decimal as string)
  distance_km: number;         // Flight distance in kilometers
  reason: string;              // Explanation of eligibility decision
  requires_manual_review: boolean;  // Whether admin review is needed
}
```

### ClaimResponse

```typescript
interface ClaimResponse {
  id: string;                  // UUID
  customer_id: string;         // UUID
  flight_number: string;
  airline: string;
  departure_date: string;      // ISO date
  departure_airport: string;   // IATA code
  arrival_airport: string;     // IATA code
  incident_type: string;       // delay, cancellation, denied_boarding, baggage_delay
  status: string;              // submitted, under_review, approved, rejected, paid
  notes: string | null;
  created_at: string;          // ISO datetime
  updated_at: string;          // ISO datetime
}
```

---

## 🐛 Error Handling

### API Error Format

```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input (validation error)
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error (with field details)
- `500 Internal Server Error` - Server error

### Validation Errors (422)

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "departure_airport"],
      "msg": "String should have at least 3 characters",
      "input": "MA"
    }
  ]
}
```

---

## 📖 API Documentation

**Interactive Swagger UI**: http://localhost:8000/docs
**ReDoc**: http://localhost:8000/redoc

You can test all endpoints directly in the browser using Swagger UI.

---

## 📝 Summary & Best Practices

### ✅ Ready to Use:

1. **Eligibility Check Endpoint** - Fully implemented and tested
   - No authentication required
   - Safe for public use
   - Improves user experience

### ❌ Not Available:

2. **Get Claims by Email** - Security risk, not implemented
   - Use `GET /claims/customer/{customer_id}` instead
   - Store customer UUID after claim submission

### 💡 Best Practices:

1. **Store Customer UUID**: Save after first claim submission for future requests
2. **Use Eligibility Check**: Pre-validate before claim submission
3. **Handle Validation Errors**: Display field-specific errors to users
4. **Show Loading States**: API calls may take 1-2 seconds
5. **Test in Swagger**: Use /docs for quick endpoint testing

---

## 🆘 Questions or Support?

If you need:
- Different endpoint behavior
- Additional features
- API clarification
- Integration help

**Contact the backend team** before implementing workarounds.

**Documentation References**:
- `app/routers/eligibility.py` - Eligibility endpoint source code
- `app/services/compensation_service.py` - Compensation calculation logic
- `docs/api-reference.md` - Complete API documentation
- `ROADMAP.md` - Project roadmap

---

**Last Updated**: 2025-11-02
**Version**: v0.2.0 with Eligibility Endpoint
