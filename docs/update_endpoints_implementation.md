# PUT and PATCH Endpoints Implementation

## Overview
This document describes the implementation of PUT and PATCH endpoints for both customers and claims in the flight claim API system, following RESTful conventions and proper validation.

## Implementation Summary

### New Schemas Created

#### Customer Update Schemas
- **CustomerUpdateSchema**: Used for PUT requests - all fields are required for complete updates
- **CustomerPatchSchema**: Used for PATCH requests - only specified fields are updated (partial updates)

#### Claim Update Schemas
- **ClaimUpdateSchema**: Used for PUT requests - all fields are required for complete updates
- **ClaimPatchSchema**: Used for PATCH requests - only specified fields are updated (partial updates)

### New Endpoints Added

#### Customer Endpoints
- `PUT /customers/{customer_id}` - Complete customer update (all fields required)
- `PATCH /customers/{customer_id}` - Partial customer update (only specified fields updated)

#### Claim Endpoints
- `PUT /claims/{claim_id}` - Complete claim update (all fields required)
- `PATCH /claims/{claim_id}` - Partial claim update (only specified fields updated)

### Key Features

#### Validation
- Email uniqueness validation for customer updates
- Customer existence validation for claim updates
- Incident type validation (delay, cancellation, denied_boarding, baggage_delay)
- Airport code validation (3 characters, uppercase)
- Flight number validation (minimum 3 characters, contains digits)

#### RESTful Conventions
- PUT requests require all mandatory fields
- PATCH requests only update provided fields
- Proper HTTP status codes (200 for success, 404 for not found, 400 for bad requests)
- Consistent response format using response schemas

#### Repository Enhancements
- Enhanced `update_customer` method in `CustomerRepository`
- New `update_claim` method in `ClaimRepository`
- Proper handling of None values to avoid overwriting with null
- Email conflict detection for customer updates

### Error Handling
- 404 Not Found: When customer/claim doesn't exist
- 400 Bad Request: When email already exists or validation fails
- 200 OK: Successful updates
- Proper error messages with details

### Testing
Comprehensive test suite created in `test_update_endpoints.py` covering:
- Successful PUT and PATCH operations
- Partial updates with PATCH
- Empty PATCH requests (no changes)
- Error cases (non-existent resources)
- Email conflict scenarios
- Flight information updates

## API Examples

### Customer PUT Request
```json
PUT /customers/{customer_id}
{
  "email": "updated@example.com",
  "firstName": "Jane",
  "lastName": "Smith",
  "phone": "+1234567890",
  "address": {
    "street": "123 New St",
    "city": "New City",
    "postalCode": "12345",
    "country": "New Country"
  }
}
```

### Customer PATCH Request
```json
PATCH /customers/{customer_id}
{
  "firstName": "Janet",
  "phone": "+0987654321"
}
```

### Claim PUT Request
```json
PUT /claims/{claim_id}
{
  "customerId": "customer-uuid",
  "flightInfo": {
    "flightNumber": "LH456",
    "airline": "Lufthansa",
    "departureDate": "2024-01-15",
    "departureAirport": "FRA",
    "arrivalAirport": "JFK"
  },
  "incidentType": "cancellation",
  "notes": "Flight was cancelled due to weather"
}
```

### Claim PATCH Request
```json
PATCH /claims/{claim_id}
{
  "incidentType": "delay",
  "notes": "Flight delayed by 4 hours"
}
```

## Files Modified

### Schemas (`app/schemas.py`)
- Added `CustomerUpdateSchema` and `CustomerPatchSchema`
- Added `ClaimUpdateSchema` and `ClaimPatchSchema`

### Routers
- `app/routers/customers.py`: Added PUT and PATCH endpoints
- `app/routers/claims.py`: Added PUT and PATCH endpoints

### Repositories
- `app/repositories/customer_repository.py`: Enhanced update methods
- `app/repositories/claim_repository.py`: Added update_claim method

### Tests
- `test_update_endpoints.py`: Comprehensive test suite

## Validation Results
All tests pass successfully:
- ✅ Customer PUT endpoint
- ✅ Customer PATCH endpoint
- ✅ Claim PUT endpoint
- ✅ Claim PATCH endpoint
- ✅ Error handling
- ✅ Edge cases

The implementation follows RESTful best practices and provides robust validation and error handling.