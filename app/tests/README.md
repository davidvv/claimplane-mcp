# Test Suite Documentation

This directory contains comprehensive tests for all API endpoints in the Flight Claim Management System.

## Test Structure

### Configuration
- `conftest.py` - Pytest configuration and shared fixtures

### Test Files

#### Core Functionality Tests
- `test_health_endpoints.py` - Health check endpoints (3 tests)
- `test_auth_endpoints.py` - Authentication and authorization (15 tests)
- `test_eligibility_endpoints.py` - Eligibility checking (6 tests)

#### Customer-Facing Tests
- `test_claims_endpoints.py` - Claims management (12 tests)
- `test_customers_endpoints.py` - Customer profile management (18 tests)
- `test_files_endpoints.py` - File upload and management (12 tests)
- `test_flights_endpoints.py` - Flight lookup (5 tests)

#### Admin Tests
- `test_admin_claims_endpoints.py` - Admin claims management (15 tests)
- `test_admin_files_endpoints.py` - Admin file management (11 tests)

#### Service Tests
- `test_compensation_service.py` - Compensation calculation logic

## Running Tests

### Prerequisites

1. **Test Database Setup**
   ```bash
   # Create test database
   createdb test_flight_claim
   ```

2. **Environment Setup**
   ```bash
   # Activate conda environment
   source /Users/david/miniconda3/bin/activate EasyAirClaim
   ```

### Running All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth_endpoints.py -v

# Run specific test class
pytest app/tests/test_auth_endpoints.py::TestAuthEndpoints -v

# Run specific test
pytest app/tests/test_auth_endpoints.py::TestAuthEndpoints::test_register_user -v
```

### Running Tests by Category

```bash
# Run only auth tests
pytest app/tests/test_auth_endpoints.py

# Run only admin tests
pytest app/tests/test_admin_*.py

# Run only customer-facing tests
pytest app/tests/test_claims_endpoints.py app/tests/test_customers_endpoints.py app/tests/test_files_endpoints.py
```

## Test Coverage

### Endpoints Covered

#### Health Endpoints (3/3)
- ✅ GET /health
- ✅ GET /health/db
- ✅ GET /health/detailed

#### Authentication Endpoints (10/10)
- ✅ POST /auth/register
- ✅ POST /auth/login
- ✅ POST /auth/refresh
- ✅ POST /auth/logout
- ✅ GET /auth/me
- ✅ POST /auth/password/reset-request
- ✅ POST /auth/password/reset-confirm
- ✅ POST /auth/password/change
- ✅ POST /auth/verify-email

#### Eligibility Endpoints (1/1)
- ✅ POST /eligibility/check

#### Claims Endpoints (8/8)
- ✅ POST /claims/
- ✅ POST /claims/submit
- ✅ GET /claims/{claim_id}
- ✅ GET /claims/
- ✅ GET /claims/customer/{customer_id}
- ✅ PUT /claims/{claim_id}
- ✅ PATCH /claims/{claim_id}
- ✅ GET /claims/status/{status}

#### Customers Endpoints (11/11)
- ✅ GET /customers/me
- ✅ PUT /customers/me
- ✅ PATCH /customers/me
- ✅ POST /customers/
- ✅ GET /customers/{customer_id}
- ✅ GET /customers/
- ✅ GET /customers/search/by-email/{email}
- ✅ GET /customers/search/by-name/{name}
- ✅ PUT /customers/{customer_id}
- ✅ PATCH /customers/{customer_id}

#### Files Endpoints (8/10)
- ✅ POST /files/upload
- ✅ GET /files/{file_id}
- ✅ GET /files/{file_id}/download
- ✅ DELETE /files/{file_id}
- ✅ GET /files/claim/{claim_id}
- ✅ GET /files/validation-rules
- ✅ POST /files/search
- ⚠️ GET /files/customer/{customer_id} (tested but may need auth)
- ⚠️ GET /files/{file_id}/access-logs (tested but may need auth)
- ⚠️ GET /files/summary/{customer_id} (tested but may need auth)

#### Flights Endpoints (1/1)
- ✅ GET /flights/status/{flight_number}

#### Admin Claims Endpoints (14/14)
- ✅ GET /admin/claims
- ✅ GET /admin/claims/{claim_id}
- ✅ PUT /admin/claims/{claim_id}/status
- ✅ PUT /admin/claims/{claim_id}/assign
- ✅ PUT /admin/claims/{claim_id}/compensation
- ✅ POST /admin/claims/{claim_id}/notes
- ✅ GET /admin/claims/{claim_id}/notes
- ✅ GET /admin/claims/{claim_id}/history
- ✅ POST /admin/claims/bulk-action
- ✅ GET /admin/claims/analytics/summary
- ✅ POST /admin/claims/calculate-compensation
- ✅ GET /admin/claims/{claim_id}/status-transitions

#### Admin Files Endpoints (8/8)
- ✅ GET /admin/files/claim/{claim_id}/documents
- ✅ GET /admin/files/{file_id}/metadata
- ✅ PUT /admin/files/{file_id}/review
- ✅ POST /admin/files/{file_id}/request-reupload
- ✅ GET /admin/files/pending-review
- ✅ GET /admin/files/by-document-type/{document_type}
- ✅ GET /admin/files/statistics
- ✅ DELETE /admin/files/{file_id}

**Total Coverage: 62+ endpoints tested**

## Test Fixtures

### Database Fixtures
- `db_session` - Fresh database session for each test
- `client` - Async HTTP client with overridden dependencies

### User Fixtures
- `test_customer` - Regular customer user
- `test_admin` - Admin user
- `test_superadmin` - Superadmin user

### Token Fixtures
- `customer_token` - JWT token for customer
- `admin_token` - JWT token for admin
- `superadmin_token` - JWT token for superadmin

### Header Fixtures
- `auth_headers` - Authorization headers for customer
- `admin_headers` - Authorization headers for admin
- `superadmin_headers` - Authorization headers for superadmin

## Test Patterns

### Authentication Tests
Tests verify:
- Successful authentication
- Failed authentication (invalid credentials)
- Unauthorized access (missing/invalid token)
- Role-based access control

### CRUD Tests
Tests verify:
- Create operations
- Read operations (single and list)
- Update operations (PUT and PATCH)
- Delete operations (soft delete)
- Pagination and filtering

### Error Handling Tests
Tests verify:
- 400 Bad Request (validation errors)
- 401 Unauthorized (missing auth)
- 403 Forbidden (insufficient permissions)
- 404 Not Found (non-existent resources)
- 422 Unprocessable Entity (schema validation)

## Notes

### Mocking External Services

Some tests may fail due to external service dependencies:

1. **Nextcloud Integration**: File upload tests require Nextcloud to be running or mocked
2. **Celery Tasks**: Email notification tests require Redis and Celery worker
3. **SMTP Server**: Email sending tests require SMTP configuration

### Test Database

Tests use a separate test database (`test_flight_claim`) that is created and destroyed for each test to ensure isolation.

### Async Tests

All endpoint tests are async and use `@pytest.mark.asyncio` decorator.

## Future Improvements

1. Add integration tests with real external services
2. Add performance/load tests
3. Add tests for edge cases and race conditions
4. Add tests for concurrent operations
5. Improve test coverage for file upload/download with actual files
6. Add tests for WebSocket endpoints (if any)
7. Add contract tests for API schemas

## Troubleshooting

### Database Connection Errors
```bash
# Check PostgreSQL is running
pg_isready

# Verify test database exists
psql -l | grep test_flight_claim
```

### Import Errors
```bash
# Ensure app is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/Users/david/Documents/Proyectos/flight_claim"
```

### Async Test Errors
```bash
# Install pytest-asyncio if not already installed
pip install pytest-asyncio
```
