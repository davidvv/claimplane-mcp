# Commit Workflow & Versioning Skill

## Purpose
This skill ensures proper commit practices, version tagging, and roadmap maintenance for the EasyAirClaim project.

## When to Use This Skill
- After completing a feature implementation
- Before pushing changes to GitHub
- When a phase milestone is completed
- Any time you're about to commit significant changes

## Commit Workflow Steps

### 1. Review Changes
Before committing, always review what has changed:

```bash
git status
git diff
```

### 2. Stage Files Selectively
**IMPORTANT**: Never commit `__pycache__` files or other generated artifacts.

```bash
# Stage specific files
git add <file1> <file2> ...

# OR stage all except pycache
git add .
git restore --staged **/__pycache__/*.pyc
```

### 3. Write Commit Message
Follow the Conventional Commits specification:

**Format**:
```
<type>(<scope>): <short description>

<detailed explanation>

<optional body with bullet points>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples**:
```
feat(auth): implement JWT authentication system

Added complete JWT-based authentication with:
- User registration and login endpoints
- Password hashing with bcrypt
- Token refresh mechanism
- Role-based access control (RBAC)
```

```
docs: update API reference with Phase 3 endpoints

Added documentation for all authentication endpoints including
request/response schemas and security considerations.
```

**IMPORTANT**: NO Claude/Anthropic attribution in commits!
- ❌ Do NOT add "Co-Authored-By: Claude"
- ❌ Do NOT add Anthropic email addresses
- ❌ Do NOT mention AI assistance in commit messages

### 4. Check Versioning Requirements

Refer to `VERSIONING.md` for version bump guidelines:

**During MVP (v0.x.x)**:
- **Minor version (0.X.0)**: Complete a major phase from ROADMAP.md
  - Example: v0.2.0 → v0.3.0 when Phase 3 is complete
- **Patch version (0.X.Y)**: Bug fixes, small improvements
  - Example: v0.2.0 → v0.2.1 for bug fixes

**Decision Tree**:
```
Did you complete a full phase from ROADMAP.md?
├─ YES → Bump minor version (create tag after commit)
└─ NO → Is this a bug fix or small improvement?
    ├─ YES → Bump patch version (create tag after commit)
    └─ NO → No version tag needed (regular commit)
```

### 5. Update ROADMAP.md BEFORE Committing

**CRITICAL**: Always update ROADMAP.md when:
- Completing a phase
- Starting a new phase
- Making significant changes that affect the roadmap

**Steps to Update ROADMAP**:

1. **If completing a phase**:
   - Mark the current phase as ✅ COMPLETED with date
   - Update "Current Version" in header
   - Update "Status" in header
   - Update the "NEXT STEPS - START HERE" section
   - Mark next phase with ⬅️ **NEXT PHASE** indicator

2. **Example when completing Phase 3**:
```markdown
## 🎯 NEXT STEPS - START HERE

**Current State**: Phase 3 Complete (v0.3.0)
- ✅ Admin Dashboard & Claim Workflow (Phase 1)
- ✅ Async Task Processing & Email Notifications (Phase 2)
- ✅ Authentication & Authorization System (Phase 3)

**Next Phase**: **Phase 4 - Customer Frontend**
```

3. **Commit ROADMAP changes separately**:
```bash
# Edit ROADMAP.md first
nano ROADMAP.md

# Commit with feature changes
git add <feature-files> ROADMAP.md
git commit -m "feat: implement phase 3 features

<details>

Completed Phase 3 - Authentication & Authorization:
- JWT-based authentication
- User registration and login
- Role-based access control

Updated ROADMAP.md to mark Phase 3 complete and indicate Phase 4 as next."
```

### 6. Create Version Tag (If Phase Complete)

Only create tags when completing a phase:

```bash
# Create annotated tag
git tag -a v0.X.0 -m "Release v0.X.0 - Phase N: Title

Key features:
- Feature 1
- Feature 2
- Feature 3

Brief description of what this release enables."

# Example:
git tag -a v0.3.0 -m "Release v0.3.0 - Phase 3: Authentication & Authorization

Key features:
- JWT-based authentication system
- User registration and login
- Password reset flow with email verification
- Role-based access control (RBAC)
- Protected routes with JWT middleware

Enables secure multi-user access and prepares platform for public launch."
```

### 7. Push to GitHub

```bash
# Push commits
git push origin MVP

# Push tags (if created)
git push origin v0.X.0
```

## Complete Workflow Checklist

Use this checklist for every commit:

### Pre-Commit
- [ ] Reviewed all changes with `git status` and `git diff`
- [ ] Excluded `__pycache__` and generated files
- [ ] Tested changes locally (if applicable)

### Roadmap Update (if applicable)
- [ ] Updated ROADMAP.md with phase completion status
- [ ] Updated "NEXT STEPS" section
- [ ] Marked next phase clearly

### Commit
- [ ] Used conventional commit format
- [ ] NO Claude/Anthropic attribution
- [ ] Included detailed description
- [ ] Staged ROADMAP.md with feature changes (if updated)

### Version Tag (if phase complete)
- [ ] Determined correct version number from VERSIONING.md
- [ ] Created annotated tag with descriptive message
- [ ] Listed all key features in tag message

### Push
- [ ] Pushed commits: `git push origin MVP`
- [ ] Pushed tags (if created): `git push origin v0.X.0`

## Quick Reference Commands

```bash
# Full workflow for phase completion
git status
git add <files> ROADMAP.md
git commit -m "feat(phase3): implement authentication system

Complete Phase 3 implementation with JWT authentication, RBAC, and
secure user management. Updated ROADMAP.md to mark Phase 3 complete."

git tag -a v0.3.0 -m "Release v0.3.0 - Phase 3: Authentication

Key features:
- JWT authentication
- User registration/login
- RBAC system"

git push origin MVP
git push origin v0.3.0
```

## Common Mistakes to Avoid

1. ❌ Committing `__pycache__` files
2. ❌ Adding Claude/Anthropic attribution
3. ❌ Forgetting to update ROADMAP.md after phase completion
4. ❌ Creating version tags for minor changes
5. ❌ Using wrong version bump (patch vs minor)
6. ❌ Forgetting to push tags separately
7. ❌ Not using conventional commit format

## Version History of This Skill

- v1.0 (2025-10-30): Initial skill creation
  - Commit workflow documentation
  - Versioning guidelines integration
  - ROADMAP update reminder system

## Related Files

- `VERSIONING.md` - Complete versioning strategy
- `ROADMAP.md` - Development roadmap with phases
- `CLAUDE.md` - Project instructions for Claude
- `.gitignore` - Files to exclude from commits

## Notes

This skill should be followed for ALL commits to ensure:
- Consistent commit history
- Proper version tracking
- Up-to-date roadmap
- Clean repository (no generated files)
- No attribution issues

When in doubt, refer to this skill before committing!
