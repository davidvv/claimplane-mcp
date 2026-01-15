# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL - READ FIRST ⚠️

### MANDATORY Testing Protocol

**BEFORE implementing ANY code changes:**

1. **TEST APIs FIRST**: Always test external APIs to verify what data they actually provide before writing code
   - Use `docker exec` to run test scripts inside the container
   - Never assume API field availability based on documentation alone
   - Example: `docker exec flight_claim_api python -c "test script here"`

2. **DOCKER-FIRST DEVELOPMENT**: This project runs on Docker in production
   - ALL changes must be tested in Docker containers
   - After code changes: `docker compose build api && docker compose restart api`
   - Never implement local-only solutions
   - The owner uses Docker exclusively, not local Python environments

3. **NO ASSUMPTIONS**: Verify actual behavior before implementing solutions
   - Test the full request/response cycle
   - Check actual data structures returned by APIs
   - Validate assumptions with real API calls

### Environment Management

**YOU MUST READ `DEVELOPMENT_WORKFLOW.md` BEFORE DOING ANYTHING ELSE.**

This project uses a dedicated Python virtual environment.

**MANDATORY RULES**:
- ✅ ALWAYS use a virtual environment (conda, venv, or virtualenv)
- ✅ Name your environment: `ClaimPlane` (recommended for consistency)
- ✅ Install dependencies from: `requirements.txt`
- ✅ Verify environment: `which python` should NOT show system Python
- ❌ NEVER install packages to base/system Python

**Setup for new developers:**
```bash
# Option 1: Using conda (recommended)
conda create -n ClaimPlane python=3.11
conda activate ClaimPlane
pip install -r requirements.txt

# Option 2: Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Architecture Decisions - Owner Approval Required

**🚨 CRITICAL**: Before making ANY changes, check `.claude/ARCHITECTURE_DECISIONS.md`

This file lists **architectural decisions that require David's explicit approval**:
- Infrastructure changes (ports, servers, Docker configuration)
- Database architecture changes
- Authentication/security modifications
- Framework or technology switches
- Development workflow changes

**IF YOUR TASK INVOLVES ANY OWNER-ONLY DECISION**:
1. ⛔ STOP immediately
2. 💬 Inform the user that this requires owner approval
3. 📝 Offer to document the proposal for review
4. ⏸️ WAIT for explicit approval before proceeding

### Claude Code Skills

**IMPORTANT**: Before committing changes, ALWAYS read `.claude/skills/commit-workflow.md`

This skill documents:
- Commit message format (Conventional Commits)
- Version tagging guidelines
- **CRITICAL**: Always update ROADMAP.md when completing a phase
- **CRITICAL**: NO Claude/Anthropic attribution in commits

### Project Context

**Current Status**: v0.2.0 (Phase 2 Complete - Email Notifications & Async Processing)

**Next Priority**: Phase 3 - Authentication & Authorization System (v0.3.0)
- See `ROADMAP.md` "NEXT STEPS" section for detailed requirements
- See `docs/SECURITY_AUDIT_v0.2.0.md` for security vulnerabilities Phase 3 will fix

---

## Project Overview

FastAPI-based flight compensation claim management platform with:
- EU261/2004 compensation calculation
- Admin dashboard for claim processing
- Secure file storage with encryption (Nextcloud integration)
- Async email notifications (Celery + Redis)
- Document validation and security scanning

### Frontend

**IMPORTANT**: We are using `frontend_Claude45` as the official frontend.
- Location: `/frontend_Claude45`
- Dev server: `npm run dev` (runs on port 3000)
- Old frontends (`FrontEnd_Claude`, `FrontEnd_Haiku`) have been removed
- DO NOT create or switch to other frontend directories

## Architecture

### High-Level Flow

**Claim Submission Flow**:
```
Customer → FastAPI Router → Service Layer → Repository → Database
                                ↓
                          Celery Task → Email Service → Customer
```

**File Upload Flow**:
```
Upload → Validation → Encryption → Nextcloud → Database → Verification
         (MIME,        (Fernet)     (WebDAV)              (SHA256)
          Security)
```

### Layered Architecture

The codebase follows strict separation of concerns:

1. **Router Layer** (`app/routers/`): Thin HTTP handlers
   - Extract request data
   - Call service methods
   - Return responses
   - **Never contain business logic**

2. **Service Layer** (`app/services/`): Business logic and orchestration
   - `compensation_service.py`: EU261/2004 calculation engine
   - `claim_workflow_service.py`: Status transition validation
   - `file_service.py`: Orchestrates upload/download flow
   - `encryption_service.py`: Fernet encryption (streaming for large files)
   - `nextcloud_service.py`: WebDAV integration with retry logic
   - `email_service.py`: SMTP email sending with templates

3. **Repository Layer** (`app/repositories/`): Database access
   - `BaseRepository`: Generic CRUD with pagination
   - Domain-specific repositories inherit from base
   - All use async SQLAlchemy sessions
   - **Never accessed directly from routers**

4. **Model Layer** (`app/models.py`): SQLAlchemy ORM models
   - `Customer`, `Claim`, `ClaimFile`, `FileAccessLog`
   - Phase 1: `ClaimNote`, `ClaimStatusHistory` (audit trail)
   - Phase 2: Email notification tracking
   - Phase 3 (planned): `User`, `RefreshToken`, `PasswordResetToken`

### Key Patterns

**Async/Await Everywhere**: Full async stack
```python
async def get_session() -> AsyncSession:
    # FastAPI dependency for DB sessions
```

**Repository Pattern**: Never query models directly
```python
# Good
await customer_repository.get_by_id(customer_id)

# Bad - Don't do this
await session.execute(select(Customer).where(...))
```

**Service Orchestration**: Complex operations in services
```python
# FileService orchestrates:
# validation → encryption → Nextcloud upload → DB record → verification
```

**Error Classification**: Nextcloud errors are categorized
- Retryable: Network issues, 500/502/503, timeouts
- Permanent: 401/403 (auth), 404 (not found), 507 (quota)

### Authentication Architecture (Current MVP)

**TEMPORARY DESIGN - Phase 3 will replace**:
- Current: `X-Customer-ID` and `X-Admin-ID` headers (insecure)
- Phase 3: JWT-based authentication with RBAC
- See `docs/SECURITY_AUDIT_v0.2.0.md` for security implications

User ID extraction pattern:
```python
user_id = request.headers.get("X-Customer-ID")  # Current
# Phase 3: user_id = current_user.id (from JWT)
```

### Async Task Processing (Phase 2)

**Celery + Redis Architecture**:
```
FastAPI → Celery Task Queue (Redis) → Celery Worker → Email Service
         (non-blocking)              (background)
```

Key files:
- `app/celery_app.py`: Celery configuration
- `app/tasks/claim_tasks.py`: Email notification tasks
- All tasks use automatic retry with exponential backoff

### Database Relationships

```
Customer 1→N Claim
Claim 1→N ClaimFile
Claim 1→N ClaimNote (Phase 1 - admin notes)
Claim 1→N ClaimStatusHistory (Phase 1 - audit trail)
ClaimFile 1→N FileAccessLog
```

---

## Development Commands

### Running the Application

```bash
# Activate environment first (conda activate ClaimPlane OR source venv/bin/activate)

# Local development
python app/main.py

# Or with uvicorn
uvicorn app.main:app --reload

# Docker full stack (requires Nextcloud)
docker-compose -f docker-compose.nextcloud.yml up -d  # Nextcloud first
docker-compose up -d  # Main application

# Phase 2: Run Celery worker (separate terminal)
celery -A app.celery_app worker --loglevel=info
```

### Frontend Development

```bash
# Navigate to frontend directory
cd frontend_Claude45

# Install dependencies (first time only)
npm install

# Start dev server (runs on port 3000)
npm run dev

# Build for production
npm run build
```

### Testing

```bash
# Activate environment first (conda activate ClaimPlane OR source venv/bin/activate)

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest app/tests/test_compensation_service.py -v

# Run async tests
pytest app/tests/test_api.py -v
```

### Database Operations

```bash
# Tables auto-create on startup (lifespan manager in app/main.py)
# For production, use Alembic:

alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

---

## Important Configuration

### Critical Environment Variables

See `app/config.py` for full list:

- `DATABASE_URL`: Must use `postgresql+asyncpg://` for async
- `FILE_ENCRYPTION_KEY`: Fernet key (generate with `scripts/generate_secrets.py`)
- `NEXTCLOUD_URL`, `NEXTCLOUD_USERNAME`, `NEXTCLOUD_PASSWORD`: WebDAV credentials
- `REDIS_URL`: Redis connection for Celery (Phase 2)
- `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`: Email configuration (Phase 2)

### Configuration Pattern

```python
class Config:
    # Uses SecureConfig helper for validation
    DATABASE_URL = SecureConfig.get_required_env_var("DATABASE_URL", default)
```

Two config classes:
- `Config`: Base with secure defaults
- `DevelopmentConfig` / `ProductionConfig`: Environment-specific overrides

---

## Code Patterns and Conventions

### Async Session Management

**CRITICAL**: Never call `session.commit()` manually in routers.

The `get_session` dependency handles lifecycle:
```python
from app.database import get_session

async def my_endpoint(session: AsyncSession = Depends(get_session)):
    # Session auto-commits on success, auto-rollbacks on exception
    await repository.create(**data)
```

### File Encryption Pattern

All files encrypted at rest with Fernet:
```python
# Streaming for large files (> STREAMING_THRESHOLD)
async for chunk in file.stream():
    encrypted_chunk = EncryptionService.encrypt_chunk(chunk, cipher)
```

### Nextcloud Error Handling

Automatic retry for transient errors:
```python
try:
    await nextcloud_service.upload_file_stream(...)
except NextcloudRetryableError:
    # Auto-retries with exponential backoff
except NextcloudPermanentError:
    # No retry - auth failure, quota exceeded, etc.
```

### Model Validators

SQLAlchemy models use `@validates` decorators:
```python
@validates('email')
def validate_email(self, key, address):
    if '@' not in address:
        raise ValueError("Invalid email format")
    return address
```

### Celery Task Pattern (Phase 2)

```python
@celery_app.task(bind=True, max_retries=3)
def send_claim_submitted_email(self, claim_id: str, customer_email: str):
    try:
        # Send email
    except Exception as exc:
        # Auto-retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

---

## Common Gotchas

### 1. Customer Address Property

`address` is a computed property, not a DB column:
```python
# Returns None if all address fields are None
# Otherwise returns dict with camelCase keys
customer.address  # {"street": "...", "postalCode": "..."}
```

### 2. Nextcloud Docker Networking

When using Docker Compose:
- `NEXTCLOUD_URL` must be `http://nextcloud:80` (service name)
- NOT `http://localhost:8081`

### 3. File Path Construction

Nextcloud paths must include username:
```python
webdav_path = f"/files/{username}/flight_claims/{customer_id}/{file_id}"
```

### 4. Streaming Threshold

Files above `STREAMING_THRESHOLD` (50MB default) use streaming:
- Different code path for upload/download
- Chunk-based encryption/decryption
- No full file in memory

### 5. Phase 2 Requirements

Email notifications require both services running:
- Terminal 1: FastAPI server (`uvicorn app.main:app --reload`)
- Terminal 2: Celery worker (`celery -A app.celery_app worker --loglevel=info`)

---

## File Management Specifics

### Document Types

Defined in `ClaimFile.DOCUMENT_TYPES`:
- `boarding_pass`, `id_document`, `receipt`, `bank_statement`
- `flight_ticket`, `delay_certificate`, `cancellation_notice`, `other`

### Validation Rules

Each document type has rules in `FileValidationService.default_rules`:
- Max file size
- Allowed MIME types
- Required extensions
- Security scan requirements
- Encryption requirements

### Upload Pipeline

9-step process (see `FileService.upload_file`):
1. MIME type detection (python-magic)
2. Document-specific validation
3. Security scanning (PDF JavaScript, embedded files, malware patterns)
4. Fernet encryption (streaming if large)
5. Nextcloud upload via WebDAV with retry
6. Post-upload verification (SHA256)
7. Database record creation
8. Access log entry
9. Return metadata

---

## Testing Guidelines

### Test Structure

- `app/tests/`: Core application tests
- `scripts/test_*.py`: Integration tests for external services
- Use `pytest-asyncio` for async functions
- Use `httpx.AsyncClient` for API testing

### Coverage Requirements

- Write tests for all new features
- Aim for 80%+ coverage
- Test edge cases (large files, special characters, errors)

---

## Security Considerations

### Current Security Model (v0.2.0)

**CRITICAL**: See `docs/SECURITY_AUDIT_v0.2.0.md` for complete security audit.

**Known Issues** (to be fixed in Phase 3):
- Header-based auth (X-Customer-ID) is insecure
- IDOR vulnerabilities in file downloads
- CORS wildcard configuration
- SQL injection in ILIKE queries (needs parameterization)

### File Security Pipeline

Every uploaded file:
1. MIME validation
2. Size limits
3. Extension validation
4. Content security scanning
5. Encryption before storage
6. Access control on download

### Content Scanning

`FileValidationService` scans for:
- Suspicious patterns (scripts, executables)
- PDF threats (JavaScript, embedded files)
- Malware signatures (if ClamAV enabled)

---

## Deployment Notes

### Docker Services

- `db`: PostgreSQL 15 with health checks
- `redis`: Redis for Celery broker (Phase 2)
- `api`: FastAPI with uvicorn
- `celery_worker`: Background task processing (Phase 2)
- `nextcloud`: External network for file storage

### Production Checklist

Before production deployment:
1. **Complete Phase 3** (JWT authentication) - MANDATORY
2. Fix SQL injection vulnerabilities (parameterize queries)
3. Set `ENVIRONMENT=production`
4. Configure `CORS_ORIGINS` to specific domains
5. Generate secure keys (`FILE_ENCRYPTION_KEY`, `SECRET_KEY`)
6. Change default Nextcloud password
7. Enable `SECURITY_HEADERS_ENABLED=true`
8. Set up managed PostgreSQL
9. Configure SSL/TLS termination
10. Review security audit (`docs/SECURITY_AUDIT_v0.2.0.md`)

---

## Key Files to Know

### Configuration & Setup
- `DEVELOPMENT_WORKFLOW.md`: Environment setup (READ FIRST)
- `ROADMAP.md`: Development priorities and next steps
- `VERSIONING.md`: Version bump guidelines
- `.claude/skills/commit-workflow.md`: Commit workflow (use before every commit)

### Documentation
- `docs/SECURITY_AUDIT_v0.2.0.md`: Security vulnerabilities and Phase 3 requirements
- `docs/api-reference.md`: Complete API documentation
- `docs/database-schema.md`: Database schema and relationships
- `docs/project-structure.md`: Detailed component documentation

### Core Application
- `app/main.py`: FastAPI app initialization
- `app/config.py`: Configuration management
- `app/models.py`: All database models
- `app/database.py`: Async database connection
- `app/celery_app.py`: Celery configuration (Phase 2)

### Business Logic
- `app/services/compensation_service.py`: EU261/2004 calculation
- `app/services/claim_workflow_service.py`: Status transitions
- `app/services/file_service.py`: File orchestration
- `app/services/email_service.py`: Email sending (Phase 2)
- `app/services/airport_taxi_time_service.py`: Airport-specific taxi time lookups

### Data Files
- `docs/comprehensive_airport_taxiing_times.csv`: Airport taxi times (184 airports)
  - Format: Region, IATA, City, Airport Name, Taxi-Out (min), Taxi-In (min)
  - Used for accurate EU261 delay calculations (runway → gate arrival)
  - Loaded on application startup into in-memory cache
  - See `docs/FLIGHT_API_LIMITATIONS.md` for details

---

## Development Principles

When working on this codebase:

1. **Business Value First**: Focus on features that enable revenue
2. **Security by Default**: Every endpoint needs proper authorization
3. **Async Throughout**: Use async/await patterns consistently
4. **Repository Pattern**: Never query models directly from routers
5. **Service Orchestration**: Complex logic belongs in services
6. **Test Coverage**: Every feature needs tests
7. **Incremental Delivery**: Ship small, working increments
8. **Documentation**: Update docs as you build

---

## Next Steps for New Sessions

1. ✅ Read `DEVELOPMENT_WORKFLOW.md` (environment setup)
2. ✅ Activate ClaimPlane conda environment
3. ✅ Check `.claude/ARCHITECTURE_DECISIONS.md` (owner-approval requirements)
4. ✅ Read `ROADMAP.md` "NEXT STEPS" section (current priorities)
5. ✅ Check `docs/SECURITY_AUDIT_v0.2.0.md` (security context)
6. ✅ Before committing: Read `.claude/skills/commit-workflow.md`

**Current Priority**: Phase 3 - Authentication & Authorization (v0.3.0)
- See ROADMAP.md for complete Phase 3 requirements
- Will fix 10/26 security vulnerabilities automatically
- Enables public launch

---

**Project Status**: MVP Phase - v0.2.0 Complete (Email Notifications & Async Processing)
**Next Milestone**: v0.3.0 (Phase 3: Authentication & Authorization)
**Last Updated**: 2025-12-29
