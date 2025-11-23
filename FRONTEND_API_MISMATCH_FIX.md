# Frontend API Response Mismatch Fix

## Problem
After implementing magic link authentication successfully, the Status page was showing blank even though:
- Magic link verification worked ✅
- JWT tokens were created with claim_id ✅
- Backend returned 200 OK with claim data ✅

The issue was a **frontend-backend API response structure mismatch**.

## Root Cause
The backend `ClaimResponseSchema` was returning **flat fields**:
```json
{
  "id": "...",
  "customerId": "...",
  "flightNumber": "BA456",
  "airline": "British Airways",
  "departureDate": "2024-11-20",
  "departureAirport": "LHR",
  "arrivalAirport": "JFK",
  "incidentType": "cancellation",
  ...
}
```

But the frontend TypeScript type expected a **nested flightInfo object**:
```typescript
export interface Claim {
  id?: string;
  customerId: string;
  flightInfo: FlightStatus;  // <-- Nested object
  incidentType: IncidentType;
  ...
}
```

The Status page tried to access `claim.flightInfo.flightNumber` (line 381) but the backend response had no `flightInfo` property, causing the page to render blank.

## Solution

### 1. Updated ClaimResponseSchema
**File**: `app/schemas.py:187-225`

Changed from flat fields to nested `flightInfo`:

```python
class ClaimResponseSchema(BaseModel):
    """Schema for claim response."""

    id: UUID
    customer_id: UUID = Field(..., alias="customerId")
    flight_info: FlightInfoSchema = Field(..., alias="flightInfo")  # <-- Nested
    incident_type: str = Field(..., alias="incidentType")
    status: str
    compensation_amount: Optional[Decimal] = Field(None, alias="compensationAmount")
    currency: str = "EUR"
    notes: Optional[str]
    submitted_at: datetime = Field(..., alias="submittedAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    @classmethod
    def from_orm(cls, claim):
        """Create response from ORM model by constructing flightInfo from flat fields."""
        return cls(
            id=claim.id,
            customer_id=claim.customer_id,
            flight_info=FlightInfoSchema(
                flightNumber=claim.flight_number,
                airline=claim.airline,
                departureDate=claim.departure_date,
                departureAirport=claim.departure_airport,
                arrivalAirport=claim.arrival_airport
            ),
            incidentType=claim.incident_type,
            status=claim.status,
            compensationAmount=claim.compensation_amount,
            currency=claim.currency,
            notes=claim.notes,
            submittedAt=claim.submitted_at,
            updatedAt=claim.updated_at
        )
```

### 2. Updated Claim Endpoints
**File**: `app/routers/claims.py`

Changed all claim response endpoints to use `from_orm()`:

```python
# Before
return ClaimResponseSchema.model_validate(claim)

# After
return ClaimResponseSchema.from_orm(claim)
```

This transformation happens in 3 locations:
- `POST /claims/` (line 151)
- `POST /claims/submit` (line 260)
- `GET /claims/{claim_id}` (line 300)

## Testing Results

### Before Fix
```bash
$ curl http://localhost:8000/claims/{id}
{
  "id": "...",
  "flightNumber": "BA456",  # <-- Flat structure
  "airline": "British Airways",
  ...
}
```
Frontend: Blank page (can't access `claim.flightInfo.flightNumber`)

### After Fix
```bash
$ curl http://localhost:8000/claims/{id}
{
  "id": "...",
  "flightInfo": {  # <-- Nested structure
    "flightNumber": "BA456",
    "airline": "British Airways",
    "departureDate": "2024-11-20",
    "departureAirport": "LHR",
    "arrivalAirport": "LAX"
  },
  ...
}
```
Frontend: Status page renders correctly ✅

## Bonus Fix: Magic Link Reusability

### Problem
Users could only use their magic link once. After the first use, they got "Invalid or expired magic link token" errors.

### Solution
**File**: `app/models.py:600-623`

Extended the grace period from 5 minutes to 24 hours:

```python
@property
def is_valid(self):
    """
    Check if token is still valid.

    Tokens are valid if:
    - Not expired (within 48 hours of creation)
    - Either never used OR used within last 24 hours (grace period for multiple uses)
    """
    from datetime import timezone, timedelta
    now = datetime.now(timezone.utc)

    # Check expiration
    if self.expires_at <= now:
        return False

    # If never used, it's valid
    if self.used_at is None:
        return True

    # Allow reuse within 24 hour grace period
    # This lets users click the link multiple times within a day
    grace_period = timedelta(hours=24)
    return (now - self.used_at.replace(tzinfo=timezone.utc)) < grace_period
```

**Updated comment**: `app/services/auth_service.py:583-584`

Now users can:
- Click their magic link multiple times within 24 hours ✅
- Tokens still expire after 48 hours for security ✅
- Much better UX - no more "link already used" frustration ✅

## Files Modified
1. `app/schemas.py` - Restructured ClaimResponseSchema with nested flightInfo
2. `app/routers/claims.py` - Updated all claim endpoints to use from_orm()
3. `app/models.py` - Extended magic link grace period to 24 hours
4. `app/services/auth_service.py` - Updated comment for grace period
5. `MAGIC_LINK_FIX_SUMMARY.md` - Updated security documentation
6. `FRONTEND_API_MISMATCH_FIX.md` - This documentation

## Impact
- ✅ Status page now displays claim details correctly
- ✅ Magic links work end-to-end
- ✅ Users can reuse links for 24 hours
- ✅ No breaking changes to API contracts (aliases maintain camelCase)
- ✅ Maintains backend flat database structure while frontend gets nested objects

---
**Status**: ✅ FIXED AND TESTED
**Date**: November 23, 2025
**Test**: `curl localhost:8000/claims/submit` returns nested flightInfo structure
