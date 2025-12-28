# Versioning Strategy

## Current Version: v0.3.0

This project follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

## MVP Development Phases

During MVP development (v0.x.x), versions track major feature milestones:

| Version | Status | Description |
|---------|--------|-------------|
| **v0.1.0** | ✅ Released (2025-10-29) | Phase 1: Admin Dashboard & Claim Workflow |
| **v0.2.0** | ✅ Released (2025-10-30) | Phase 2: Notifications & Async Processing |
| **v0.3.0** | ✅ Released (2025-11-03) | Phase 3: JWT Authentication & Authorization |
| **v0.3.1** | 🚧 In Progress | Security Patch: HTTP-only Cookie Migration |
| **v0.4.0** | 📋 Planned | Phase 4: Customer Account Management |
| **v1.0.0** | 🎯 Target | Production-Ready MVP |

## Version Bump Guidelines

### During MVP (v0.x.x)

- **Minor version (0.X.0)**: Complete a major phase from ROADMAP.md
  - Example: v0.1.0 → v0.2.0 when Phase 2 is complete

- **Patch version (0.1.X)**: Bug fixes, small improvements, hotfixes
  - Example: v0.1.0 → v0.1.1 for bug fixes to Phase 1 features

### After MVP (v1.0.0+)

- **Major version (X.0.0)**: Breaking API changes, major architectural changes
  - Example: v1.0.0 → v2.0.0 for API v2 with breaking changes

- **Minor version (1.X.0)**: New features, backward-compatible changes
  - Example: v1.0.0 → v1.1.0 for payment integration feature

- **Patch version (1.0.X)**: Bug fixes, security patches
  - Example: v1.0.0 → v1.0.1 for security fix

## Release Process

### 1. Complete Feature Implementation
- Implement all features for the milestone
- Write comprehensive tests
- Update documentation

### 2. Update Documentation
- Update ROADMAP.md with completion status
- Create/update PHASE{N}_SUMMARY.md
- Update README.md with new features

### 3. Commit Changes
```bash
# Stage all changes
git add .

# Commit with detailed message
git commit -m "feat(feature): description

Detailed explanation of changes...
"
```

### 4. Create Version Tag
```bash
# Create annotated tag
git tag -a vX.Y.Z -m "Release vX.Y.Z - Title

Key features:
- Feature 1
- Feature 2

Brief description of what this release enables."
```

### 5. Push to GitHub
```bash
# Push commit and tag
git push origin MVP
git push origin vX.Y.Z
```

## Tag Naming Convention

- Use `vX.Y.Z` format (lowercase 'v', three numbers)
- Always use annotated tags (`-a` flag)
- Include descriptive release notes in tag message

## Examples

### Phase Completion (Minor Version)
```bash
git tag -a v0.2.0 -m "Release v0.2.0 - Phase 2: Notifications

Features:
- Email notification system
- Celery task queue
- Scheduled reminders

Enables automated customer communication."
```

### Bug Fix (Patch Version)
```bash
git tag -a v0.1.1 -m "Release v0.1.1 - Bug fixes

Fixes:
- Corrected compensation calculation for edge case
- Fixed pagination issue in claim list
- Resolved file download error"
```

## Viewing Version History

```bash
# List all tags
git tag

# Show tag details
git show v0.1.0

# Check current version
git describe --tags

# List tags with messages
git tag -n
```

## Branch Strategy

- **MVP**: Main development branch during MVP phase
- **main**: Production-ready code (will merge from MVP when v1.0.0 is released)
- **feature/**: Feature branches (merge into MVP)
- **hotfix/**: Urgent fixes (merge into MVP, cherry-pick to main if needed)

## Version in Code

The current version is also tracked in:
- `app/main.py` - FastAPI app version
- README.md - Documentation reference

Update these when creating a new version.

## Notes

- Never reuse or delete version tags
- Version tags are immutable once pushed
- If you make a mistake, create a new patch version
- Document breaking changes clearly in release notes

---

**Current Status**: MVP Phase - v0.3.0 Complete (Phase 3: JWT Authentication)
**Next Milestone**: v0.3.1 (Security Patch: HTTP-only Cookie Migration)
**Last Updated**: 2025-12-28
