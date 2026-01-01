# Update Documentation

Regenerate and update all project documentation to reflect current implementation.

## Instructions

Execute all documentation updates proactively.

### Step 1: Verify Current State
1. Check ROADMAP.md current version and phase
2. Identify what has changed since last documentation update
3. List all documentation files that exist

### Step 2: API Documentation
Update `docs/api-reference.md`:

1. Scan all routers in `app/routers/`:
   - List all endpoints
   - Document request/response schemas
   - Include authentication requirements
   - Add example requests/responses

2. Group by category:
   - Authentication endpoints
   - Customer endpoints
   - Admin endpoints
   - File endpoints
   - Claim endpoints

3. Generate OpenAPI/Swagger reference if available

### Step 3: Database Documentation
Update `docs/database-schema.md`:

1. Read all models from `app/models.py`
2. Document each table:
   - Table name
   - Columns with types
   - Relationships
   - Indexes
   - Constraints
3. Generate ERD description
4. Document migration status

### Step 4: Architecture Documentation
Update or create `docs/architecture.md`:

1. Document current architecture:
   - FastAPI backend structure
   - Frontend structure
   - Database (PostgreSQL)
   - Redis/Celery for async tasks
   - Nextcloud for file storage

2. Document request flow:
   - Customer request flow
   - Admin workflow
   - File upload/download flow
   - Authentication flow

3. Document design patterns:
   - Repository pattern
   - Service layer
   - Dependency injection

### Step 5: Deployment Documentation
Update or create `docs/deployment.md`:

1. Document deployment process:
   - Docker setup
   - Environment variables
   - Database migrations
   - Cloudflare tunnel configuration

2. Document requirements:
   - System requirements
   - Dependencies
   - Third-party services

3. Include troubleshooting section

### Step 6: Security Documentation
Update security documentation:

1. Document authentication system
2. Document authorization (RBAC)
3. Document security measures:
   - File encryption
   - Password hashing
   - Rate limiting
   - CORS configuration

### Step 7: Development Guide
Update or create `docs/development-guide.md`:

1. Setup instructions
2. Running locally
3. Running tests
4. Code style guidelines
5. Contribution workflow

### Step 8: Update README.md
Ensure root README.md is current:

1. Project description
2. Features implemented
3. Quick start guide
4. Link to detailed docs
5. Current version and status

### Step 9: CHANGELOG
Generate or update CHANGELOG.md:

1. Extract from git commits since last version
2. Group by type (feat, fix, docs, etc.)
3. Format in Keep a Changelog style
4. Include version numbers and dates

## Output Format

```
📚 Documentation Update Complete

Updated Files:
✅ docs/api-reference.md (45 endpoints documented)
✅ docs/database-schema.md (12 tables documented)
✅ docs/architecture.md (created new)
✅ docs/deployment.md (updated Cloudflare section)
✅ docs/security.md (updated with Phase 4.5 fixes)
✅ docs/development-guide.md (updated setup instructions)
✅ README.md (updated to v0.3.0)
✅ CHANGELOG.md (added v0.3.0 entries)

Summary of Changes:
- Added 15 new endpoints from Phase 3
- Documented JWT authentication flow
- Updated database schema with new tables
- Added Cloudflare tunnel deployment guide
- Documented security improvements

Files Needing Attention:
⚠️ docs/testing-guide.md - Outdated, needs Phase 3 update
⚠️ docs/troubleshooting.md - Missing common issues

Next Steps:
1. Review updated docs for accuracy
2. Update troubleshooting guide
3. Consider adding diagrams for complex flows
```

## Execution Notes

- Read actual code to generate accurate docs
- Don't just update dates - verify content is current
- Include code examples where helpful
- Cross-reference related documentation
- Check for broken links
- Ensure consistent formatting across all docs
- Version documentation with code (same version numbers)
