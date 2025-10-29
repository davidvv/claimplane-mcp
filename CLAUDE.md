# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL - READ FIRST ⚠️

**ENVIRONMENT MANAGEMENT**: This project uses a dedicated conda environment called **EasyAirClaim**.

**YOU MUST READ `DEVELOPMENT_WORKFLOW.md` BEFORE DOING ANYTHING ELSE.**

Key rules:
- ✅ ALWAYS activate the EasyAirClaim conda environment first
- ❌ NEVER install packages to base environment
- ✅ Activate: `source /Users/david/miniconda3/bin/activate EasyAirClaim`
- ✅ Verify: `which python` should show `/Users/david/miniconda3/envs/EasyAirClaim/bin/python`

See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for complete instructions.

---

## Project Overview

This is a FastAPI-based flight claim management system with secure file storage and Nextcloud integration. The application handles customer claims for flight compensation (delays, cancellations, denied boarding, baggage delays) and manages associated documents with encryption, validation, and security scanning.

## Architecture

### Layered Architecture Pattern

The codebase follows a clean layered architecture:

1. **Models Layer** (`app/models.py`): SQLAlchemy ORM models with validators
   - `Customer`: Customer information with address as a nested property
   - `Claim`: Flight claims with incident types and status workflow
   - `ClaimFile`: File metadata with encryption, access control, and versioning
   - `FileAccessLog`: Audit trail for file operations
   - `FileValidationRule`: Document-specific validation rules

2. **Repository Layer** (`app/repositories/`): Data access abstraction
   - `BaseRepository`: Generic CRUD operations with pagination
   - `CustomerRepository`, `ClaimRepository`, `FileRepository`: Domain-specific queries
   - All repositories use async SQLAlchemy sessions

3. **Service Layer** (`app/services/`): Business logic and external integrations
   - `EncryptionService`: Fernet-based file encryption/decryption with streaming support
   - `FileValidationService`: Document type validation, MIME type checking, security scanning
   - `NextcloudService`: WebDAV integration with retry logic and error classification
   - `FileService`: Orchestrates file upload/download with all security checks

4. **Router Layer** (`app/routers/`): FastAPI endpoint handlers
   - `customers.py`: Customer CRUD operations
   - `claims.py`: Claim submission and tracking
   - `files.py`: File upload/download with streaming support
   - `health.py`: System health checks (basic, database, detailed)

### Key Architectural Patterns

- **Repository Pattern**: Abstracts database operations from business logic
- **Service Layer Pattern**: Encapsulates complex business logic and external service integration
- **Async/Await**: Full async support throughout the stack for better performance
- **Dependency Injection**: FastAPI's dependency system for database sessions
- **Error Classification**: Structured exception hierarchy for Nextcloud operations (retryable vs permanent errors)

### File Management Flow

1. **Upload**: Client → Router → FileService → Validation → Encryption → NextcloudService → Database
2. **Download**: Client → Router → FileService → Database → NextcloudService → Decryption → Client
3. **Verification**: Post-upload integrity check with SHA256 hash comparison

### Database Relationships

- `Customer` has many `Claim` (one-to-many)
- `Claim` has many `ClaimFile` (one-to-many)
- `Customer` has many `ClaimFile` (one-to-many, for ownership tracking)
- `ClaimFile` has many `FileAccessLog` (one-to-many, audit trail)

## Development Commands

### Running the Application

```bash
# Local development (requires Python 3.11+)
python app/main.py

# With uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Docker Compose (full stack with Nextcloud)
docker-compose -f docker-compose.nextcloud.yml up -d  # Start Nextcloud first
docker-compose up -d  # Start main application

# Check health
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test files
pytest app/tests/test_file_operations.py
pytest app/tests/test_edge_cases.py
pytest scripts/test_nextcloud_integration.py

# Run async tests
pytest app/tests/test_api.py -v
```

### Database Operations

```bash
# The application auto-creates tables on startup via lifespan manager in app/main.py
# For production, use Alembic migrations:

alembic init alembic  # Initialize (if not done)
alembic revision --autogenerate -m "migration description"
alembic upgrade head
alembic downgrade -1  # Rollback
```

## Important Configuration

### Environment Variables

Critical environment variables (see `app/config.py`):

- `DATABASE_URL`: PostgreSQL connection string (must use `postgresql+asyncpg://` for async)
- `FILE_ENCRYPTION_KEY`: Fernet key for file encryption (generate with `scripts/generate_secrets.py`)
- `NEXTCLOUD_URL`, `NEXTCLOUD_USERNAME`, `NEXTCLOUD_PASSWORD`: Nextcloud WebDAV credentials
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 52428800 = 50MB)
- `STREAMING_THRESHOLD`: Files above this size use streaming (default: 50MB)
- `CHUNK_SIZE`: Chunk size for streaming operations (default: 8MB)
- `UPLOAD_VERIFICATION_ENABLED`: Enable post-upload integrity verification (default: true)

### Configuration Classes

- `Config`: Base configuration with secure defaults
- `DevelopmentConfig`: Relaxed security for local dev (permissive CORS, higher rate limits)
- `ProductionConfig`: Strict security settings with validation checks

## Code Patterns and Conventions

### User ID Handling

**IMPORTANT**: The user ID is dynamically extracted from the `X-Customer-ID` header, NOT from authentication tokens. This is a design choice for the MVP phase. See `app/routers/files.py` for implementation.

```python
# Always get user_id from headers
user_id = request.headers.get("X-Customer-ID")
```

### Async Database Sessions

Always use async context managers for database operations:

```python
from app.database import get_session

async def my_function(session: AsyncSession = Depends(get_session)):
    # Operations are automatically committed/rolled back
    result = await repository.create(**data)
    return result
```

### Error Handling with Nextcloud

The Nextcloud service has sophisticated error classification:

- **Retryable Errors**: Network issues, server errors (500, 502, 503), timeouts
- **Permanent Errors**: Auth failures (401, 403), file not found (404), quota exceeded (507)
- **Retry Strategy**: Exponential backoff with jitter, configurable max retries

```python
# Automatic retry for transient errors
result = await nextcloud_service.upload_file_stream(...)
# Raises NextcloudPermanentError for unrecoverable issues
```

### File Encryption

All files are encrypted at rest using Fernet encryption:

```python
from app.services.encryption_service import EncryptionService

# Streaming encryption for large files
encrypted_chunks = EncryptionService.encrypt_file_stream(file_stream)

# Decryption
decrypted_data = EncryptionService.decrypt_file(encrypted_content)
```

### Model Validators

SQLAlchemy models use `@validates` decorators for data validation:

```python
@validates('email')
def validate_email(self, key, address):
    if '@' not in address:
        raise ValueError("Invalid email format")
    return address
```

### Repository Pattern Usage

Always use repositories for database operations, never direct model access:

```python
# Good
customer = await customer_repository.get_by_id(customer_id)
await customer_repository.update(customer, email="new@email.com")

# Avoid direct model manipulation
# customer.email = "new@email.com"  # Don't do this
```

## File Management Specifics

### Document Types and Validation

Document types are defined in `ClaimFile.DOCUMENT_TYPES`:
- `boarding_pass`, `id_document`, `receipt`, `bank_statement`, `flight_ticket`, `delay_certificate`, `cancellation_notice`, `other`

Each document type has validation rules in `FileValidationService.default_rules`:
- Max file size
- Allowed MIME types
- Required file extensions
- Security scan requirements
- Encryption requirements

### File Upload Flow

1. Multipart form data received at `/files/upload`
2. MIME type detection using python-magic (libmagic)
3. Document-specific validation
4. Security content scanning (PDF JavaScript, embedded files, suspicious patterns)
5. Fernet encryption (streaming for large files)
6. Upload to Nextcloud via WebDAV with retry logic
7. Post-upload verification (SHA256 hash comparison)
8. Database record creation with metadata
9. Access log entry

### Streaming for Large Files

Files above `STREAMING_THRESHOLD` use streaming to avoid memory exhaustion:

```python
# Streaming upload
async for chunk in file.stream():
    encrypted_chunk = EncryptionService.encrypt_chunk(chunk, cipher)
    await nextcloud_service.upload_chunk(encrypted_chunk)
```

## Common Gotchas

### 1. Customer Address Handling

The `address` field in Customer is a computed property, not a database column. It returns `None` if all address fields are `None`, otherwise returns a dict with snake_case database fields mapped to camelCase:

```python
# Database fields: street, city, postal_code, country
# API returns: {"street": "...", "city": "...", "postalCode": "...", "country": "..."}
```

### 2. Nextcloud Network Configuration

When running with Docker Compose, the Nextcloud service is on a shared network (`flight_claim_nextcloud_network`). The `NEXTCLOUD_URL` must use the Docker service name: `http://nextcloud:80`, not `localhost`.

### 3. File Encryption Keys

The `FILE_ENCRYPTION_KEY` must be a valid Fernet key. Generate with:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key().decode()
```

Never commit encryption keys to the repository.

### 4. Async Session Management

Do NOT manually call `session.commit()` in routers. The `get_session` dependency handles transaction lifecycle:

```python
# Repository methods handle commit internally
# get_session dependency ensures rollback on exception
```

### 5. File Path Construction

Nextcloud file paths must include the username:
```python
# Correct: /files/{username}/{path}
webdav_path = f"/files/{self.username}/flight_claims/{customer_id}/{file_id}"
```

## Testing Guidelines

### Test Structure

- `app/tests/`: Core application tests
- `scripts/test_*.py`: Integration tests for external services
- Use `pytest-asyncio` for async test functions
- Use `httpx.AsyncClient` for API testing

### Running Specific Tests

```bash
# File operations
pytest app/tests/test_file_operations.py -v

# Nextcloud integration
pytest scripts/test_nextcloud_integration.py -v

# Edge cases (large files, special characters, etc.)
pytest app/tests/test_edge_cases.py -v
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI spec: `API/openapi.yaml`

## Security Considerations

### File Security Pipeline

Every uploaded file goes through:
1. MIME type validation
2. File size limits
3. Extension validation
4. Content security scanning (malicious patterns, PDF JavaScript)
5. Encryption before storage
6. Access control checks on download

### Content Scanning

The `FileValidationService` scans for:
- Suspicious file patterns (scripts, executables)
- PDF-specific threats (JavaScript, embedded files, excessive pages)
- Malware signatures (if ClamAV is enabled)

### Access Control

Files are associated with both a claim and a customer. Access is controlled via:
- `X-Customer-ID` header validation
- File ownership checks in `FileRepository.get_files_for_customer()`
- Access logs for audit trails

## Deployment Notes

### Docker Build

Multi-stage Dockerfile with:
1. Base Python 3.11 image
2. System dependency installation (libmagic)
3. Python package installation
4. Application code copy

### Services

- `db`: PostgreSQL 15 with health checks
- `api`: FastAPI application with uvicorn
- `nginx`: Reverse proxy (optional)
- `nextcloud`: External network for Nextcloud integration

### Production Checklist

1. Set `ENVIRONMENT=production`
2. Generate secure `SECRET_KEY` and `FILE_ENCRYPTION_KEY`
3. Change default `NEXTCLOUD_PASSWORD`
4. Configure `CORS_ORIGINS` to specific domains
5. Enable `SECURITY_HEADERS_ENABLED=true`
6. Set appropriate rate limits
7. Use managed PostgreSQL service
8. Configure SSL/TLS termination
9. Enable virus scanning with ClamAV
10. Set up backup strategy for database and Nextcloud storage
