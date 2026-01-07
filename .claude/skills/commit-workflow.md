# Commit Workflow & Versioning Skill

## Purpose
This skill ensures proper commit practices, version tagging, and roadmap maintenance for the EasyAirClaim project.

## When to Use This Skill
- After completing a feature implementation
- Before pushing changes to GitHub
- When a phase milestone is completed
- Any time you're about to commit significant changes

---

## ⚠️ CRITICAL: MANDATORY PRE-COMMIT CHECKLIST

**BEFORE YOU DO ANYTHING ELSE**, answer these questions:

1. ❓ **Does this change affect the project roadmap?**
   - Did I complete a phase or major milestone?
   - Did I start working on a new phase?
   - Did I make significant progress on current phase features?
   - Did I change project priorities or strategy?

2. ❓ **Did I complete any significant work that needs time tracking?**
   - Did I implement a new feature or bug fix?
   - Did I spend notable time (>30 min) on this change?
   - Should this work be recorded in time tracking files?

3. ❓ **If YES to any above**: **STOP and update ROADMAP.md AND time tracking files NOW**
4. ❓ **If NO**: Proceed to commit workflow (Step 2 below)

---

## Commit Workflow Steps

### Step 1: Check & Update ROADMAP.md (MANDATORY FIRST STEP)

**🚨 ALWAYS START HERE - Check if roadmap needs updating BEFORE committing**

#### Decision Tree: Do I Need to Update ROADMAP?

```
Did I complete an ENTIRE PHASE from ROADMAP.md?
├─ YES → Go to Section 1.1 (Phase Completion Update)
│
└─ NO → Did I make SIGNIFICANT progress on current phase?
    ├─ YES → Go to Section 1.2 (Progress Update)
    │
    └─ NO → Is this just a bug fix or small improvement?
        ├─ YES → Skip to Step 2 (no roadmap update needed)
        └─ NO → Review changes again - you probably need Section 1.2
```

#### 1.1 Phase Completion Update (Major Changes)

**When**: You completed ALL tasks in a phase from ROADMAP.md

**What to Update**:
1. Mark the phase as ✅ **COMPLETED** with today's date
2. Update "Current Version" in header (e.g., v0.3.0)
3. Update "Status" in header
4. Update "NEXT STEPS - START HERE" section with new current state
5. Mark the next phase clearly

**Example Changes**:
```markdown
# At top of ROADMAP.md
**Current Version**: v0.4.0 (Phase 4 Complete)  # ← Update this
**Status**: MVP Phase - Payment Integration Ready 🚀  # ← Update this

## 🎯 NEXT STEPS - START HERE

**Current State**: Phase 4 Complete ✅ (v0.4.0)  # ← Update this
- ✅ Admin Dashboard & Claim Workflow (Phase 1)
- ✅ Async Task Processing & Email Notifications (Phase 2)
- ✅ JWT Authentication & Authorization System (Phase 3)
- ✅ Customer Frontend (Phase 4)  # ← Add this

**Phase 4 Status**: ✅ **COMPLETED** (2025-12-06) 🎨  # ← Add section like this
- ✅ React customer portal with JWT integration
- ✅ Claim submission form with file upload
- ✅ Dashboard showing claim status
- ✅ Mobile-responsive design
- ✅ Real-time notifications

**Next Priority**: Payment Integration (Phase 5)  # ← Update this
```

#### 1.2 Progress Update (Feature Additions)

**When**: You added significant features but didn't complete entire phase

**What to Update**:
- Add ✅ checkmarks to completed tasks in current phase section
- Update phase status percentage if shown
- Add notes about what's working

**Example Changes**:
```markdown
## Phase 4: Customer Frontend

**Status**: ⏳ **IN PROGRESS** - ~60% Complete  # ← Update percentage
...

#### 4.1 Customer Dashboard
- ✅ Dashboard layout component  # ← Add checkmark
- ✅ Claim list view  # ← Add checkmark
- ⏳ Claim detail modal  # ← In progress
- ⏳ Real-time status updates  # ← Not started
```

#### 1.3 Bug Fixes / Small Improvements (Usually Skip)

**When**: Bug fixes, small UI tweaks, refactoring

**What to Do**: ✅ No roadmap update needed - proceed to Step 1.5

---

### Step 1.5: Update Time Tracking (MANDATORY FOR SIGNIFICANT WORK)

**🚨 ALWAYS DO THIS AFTER Step 1 if you completed notable work**

#### When to Update Time Tracking

Update time tracking when:
- You implemented a new feature or significant enhancement
- You fixed a bug that took notable time (>15-30 min)
- You completed work that should be recorded for project metrics
- You want accurate time estimates for future planning

#### What to Update

1. **time_tracking_david.md** - Add entry with:
   - Date and work description
   - Key tasks and commits
   - Estimated time spent

2. **time_tracking_summary.md** - Update totals:
   - Total commits
   - Estimated total hours
   - Date range

#### Example Time Tracking Update

```markdown
## Latest Work (2026-01-07) - Feature Name

### Feature Implementation
**Estimated Time**: X-Y hours

#### Key Tasks:
1. **Task Description** (commit-hash)
   - Details of what was done
   - Estimated: A-B hours

2. **Another Task** (commit-hash)
   - More details
   - Estimated: C-D hours

### Updated Summary Statistics
- **Total Commits**: N (added M new commits)
- **Date Range**: Updated to YYYY-MM-DD
- **Estimated Total Time**: ~X-Z hours (added A-B hours)
```

#### Time Estimation Guidelines

| Work Type | Estimated Time |
|-----------|----------------|
| Complex feature | 2-5 hours |
| Medium task | 1-2 hours |
| Bug fix | 0.5-1.5 hours |
| Documentation | 0.5-1 hour |

---

### Step 2: Review Changes

Review what has changed before committing:

```bash
git status
git diff
```

**Check for**:
- Files that shouldn't be committed (`__pycache__`, `.env`, etc.)
- Unintended changes
- Debug code or console.logs left in
- Large files or generated artifacts

---

### Step 3: Stage Files Selectively

**IMPORTANT**: Never commit `__pycache__` files or other generated artifacts.

```bash
# Stage specific files (RECOMMENDED)
git add <file1> <file2> ...

# If you updated ROADMAP.md, include it
git add ROADMAP.md

# If you updated time tracking, include those files
git add time_tracking_david.md time_tracking_summary.md

# OR stage all except pycache
git add .
git restore --staged **/__pycache__/*.pyc
```

**Critical Files to Check**:
- ✅ Include ROADMAP.md if you updated it in Step 1
- ✅ Include time_tracking files if you updated them in Step 1.5
- ❌ Never commit `.env` files with secrets
- ❌ Never commit `__pycache__` or `.pyc` files
- ❌ Never commit `node_modules/`
- ❌ Never commit database files (`.db`, `.sqlite`)

---

### Step 4: Write Commit Message

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

Updated ROADMAP.md to mark Phase 3 as complete.
```

```
fix(admin): resolve blank page on status updates and dashboard analytics

Fixed multiple critical admin dashboard issues:
- Fixed blank page crash when updating claim status to rejected
- Added proper error message extraction from nested API responses
- Updated analytics counters to show correct values
```

```
docs: update API reference with Phase 3 endpoints

Added documentation for all authentication endpoints including
request/response schemas and security considerations.
```

**IMPORTANT**: NO Claude/Anthropic attribution in commits!
- ❌ Do NOT add "Co-Authored-By: Claude"
- ❌ Do NOT add Anthropic email addresses
- ❌ Do NOT mention "Generated with Claude Code"
- ❌ Do NOT mention AI assistance in commit messages

**If you updated ROADMAP.md or time tracking**: Mention it in commit message
```
feat(frontend): complete customer portal implementation

Implemented React customer portal with all core features.

Updated ROADMAP.md to mark Phase 4 as complete and update next steps.
Updated time_tracking_david.md with estimated time for implementation.
```

---

### Step 5: Commit Changes

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <short description>

<detailed explanation>

<list of changes>

Updated ROADMAP.md to reflect completion of [Phase X / feature Y].
Updated time_tracking_david.md with X-Y hours for this work.
EOF
)"
```

---

### Step 6: Check Versioning Requirements

Refer to `VERSIONING.md` for version bump guidelines:

**During MVP (v0.x.x)**:
- **Minor version (0.X.0)**: Complete a major phase from ROADMAP.md
  - Example: v0.3.0 → v0.4.0 when Phase 4 is complete
- **Patch version (0.X.Y)**: Bug fixes, small improvements
  - Example: v0.3.0 → v0.3.1 for bug fixes

**Decision Tree**:
```
Did you complete a full phase from ROADMAP.md?
├─ YES → Bump minor version (create tag after commit)
│        Example: v0.3.0 → v0.4.0
│
└─ NO → Is this a bug fix or small improvement?
    ├─ YES → Optionally bump patch version
    │        Example: v0.3.0 → v0.3.1
    │
    └─ NO → No version tag needed (regular commit)
```

---

### Step 7: Create Version Tag (If Phase Complete)

**Only create tags when completing a FULL PHASE from ROADMAP.md**

```bash
# Create annotated tag
git tag -a v0.X.0 -m "Release v0.X.0 - Phase N: Title

Key features:
- Feature 1
- Feature 2
- Feature 3

Brief description of what this release enables."

# Example for Phase 4 completion:
git tag -a v0.4.0 -m "Release v0.4.0 - Phase 4: Customer Frontend

Key features:
- React customer portal with JWT integration
- Claim submission form with drag-and-drop file upload
- Dashboard with real-time status updates
- Mobile-responsive design
- Customer authentication flow

Enables customers to submit and track claims independently."
```

---

### Step 8: Push to GitHub

```bash
# Push commits
git push origin MVP

# Push tags (if created)
git push origin v0.X.0
```

---

## Complete Workflow Checklist

Use this checklist for **EVERY** commit:

### ✅ Step 1: Roadmap Check (MANDATORY FIRST)
- [ ] Reviewed what I changed and determined if roadmap needs updating
- [ ] **IF PHASE COMPLETE**: Updated ROADMAP.md with phase completion (Section 1.1)
- [ ] **IF SIGNIFICANT PROGRESS**: Updated ROADMAP.md with progress (Section 1.2)
- [ ] **IF BUG FIX**: Confirmed no roadmap update needed
- [ ] Updated "NEXT STEPS" section if applicable
- [ ] Updated version number in ROADMAP header if phase complete

### ✅ Step 1.5: Time Tracking Update (MANDATORY FOR NOTABLE WORK)
- [ ] Reviewed if work requires time tracking entry
- [ ] **IF SIGNIFICANT WORK**: Updated time_tracking_david.md with:
  - [ ] Date and work description
  - [ ] Key tasks and commits
  - [ ] Estimated time spent
- [ ] **IF SIGNIFICANT WORK**: Updated time_tracking_summary.md with:
  - [ ] Updated total commits
  - [ ] Updated estimated total hours
  - [ ] Updated date range

### ✅ Step 2-3: Review & Stage
- [ ] Reviewed all changes with `git status` and `git diff`
- [ ] Excluded `__pycache__`, `.env`, and generated files
- [ ] Staged ROADMAP.md if it was updated
- [ ] Staged time_tracking files if they were updated
- [ ] Tested changes locally (if applicable)

### ✅ Step 4-5: Commit
- [ ] Used conventional commit format (`feat`, `fix`, etc.)
- [ ] NO Claude/Anthropic attribution
- [ ] Included detailed description
- [ ] Mentioned ROADMAP.md update in commit message (if updated)
- [ ] Mentioned time_tracking update in commit message (if updated)

### ✅ Step 6-7: Versioning (if phase complete)
- [ ] Determined correct version number from VERSIONING.md
- [ ] Created annotated tag with descriptive message
- [ ] Listed all key features in tag message

### ✅ Step 8: Push
- [ ] Pushed commits: `git push origin MVP`
- [ ] Pushed tags (if created): `git push origin v0.X.0`

---

## Quick Reference: Complete Workflows

### Workflow A: Phase Completion (with roadmap update)

```bash
# 1. Update ROADMAP.md first
nano ROADMAP.md
# - Mark phase as ✅ COMPLETED
# - Update Current Version
# - Update NEXT STEPS section

# 2. Review changes
git status
git diff

# 3. Stage everything including ROADMAP.md
git add app/ frontend/ ROADMAP.md

# 4. Commit with proper message
git commit -m "feat(phase4): complete customer frontend portal

Implemented complete React customer portal with:
- JWT-authenticated dashboard
- Claim submission with file upload
- Real-time status tracking
- Mobile-responsive design

Updated ROADMAP.md to mark Phase 4 complete and update next steps."

# 5. Create version tag
git tag -a v0.4.0 -m "Release v0.4.0 - Phase 4: Customer Frontend

Key features:
- React customer portal
- Claim submission form
- Real-time dashboard
- Mobile responsive

Enables customer self-service claims."

# 6. Push
git push origin MVP
git push origin v0.4.0
```

### Workflow B: Bug Fix (no roadmap update)

```bash
# 1. Confirm no roadmap update needed (just a bug fix)

# 2. Review changes
git status
git diff

# 3. Stage files
git add app/services/api.ts frontend/src/components/

# 4. Commit
git commit -m "fix(admin): resolve blank page on status updates

Fixed crash when updating claim status without rejection reason."

# 5. Push (no tag for bug fixes unless you want patch version)
git push origin MVP
```

### Workflow C: Feature Addition (partial progress)

```bash
# 1. Update ROADMAP.md with progress
nano ROADMAP.md
# - Add ✅ to completed tasks
# - Update percentage if shown

# 2. Review and stage
git status
git add app/ frontend/ ROADMAP.md

# 3. Commit
git commit -m "feat(frontend): add claim submission form

Implemented claim submission with file upload and validation.

Updated ROADMAP.md to reflect progress on Phase 4."

# 4. Push (no tag, phase not complete yet)
git push origin MVP
```

---

## Common Mistakes to Avoid

1. ❌ **Forgetting to check roadmap FIRST** - Always start with Step 1
2. ❌ **Forgetting to update time tracking** - Always check Step 1.5 for notable work
3. ❌ Committing `__pycache__` files
4. ❌ Adding Claude/Anthropic attribution
5. ❌ Forgetting to update ROADMAP.md after phase completion
6. ❌ Updating ROADMAP.md but forgetting to include it in commit
7. ❌ Updating time tracking but forgetting to include it in commit
8. ❌ Creating version tags for minor changes
9. ❌ Using wrong version bump (patch vs minor)
10. ❌ Forgetting to push tags separately
11. ❌ Not using conventional commit format
12. ❌ Not mentioning ROADMAP update in commit message

---

## When ROADMAP.md MUST Be Updated

| Scenario | Update ROADMAP? | What to Update |
|----------|----------------|----------------|
| ✅ Completed entire phase | **YES** | Phase status, version, next steps |
| ✅ Completed major feature in phase | **YES** | Add checkmarks to tasks |
| ✅ Started new phase work | **YES** | Mark phase as IN PROGRESS |
| ⚠️ Significant refactoring | **MAYBE** | If it affects roadmap priorities |
| ❌ Bug fix | **NO** | No changes needed |
| ❌ Small UI tweak | **NO** | No changes needed |
| ❌ Documentation only | **NO** | No changes needed |
| ❌ Test additions | **NO** | No changes needed |

---

## Version History of This Skill

- v2.0 (2025-12-06): Major restructure
  - Made roadmap check mandatory first step
  - Added decision trees and flowcharts
  - Added "When to Update" table
  - Reorganized workflow for clarity
  - Added complete workflow examples

- v1.0 (2025-10-30): Initial skill creation
  - Commit workflow documentation
  - Versioning guidelines integration
  - ROADMAP update reminder system

---

## Related Files

- `VERSIONING.md` - Complete versioning strategy
- `ROADMAP.md` - Development roadmap with phases
- `CLAUDE.md` - Project instructions for Claude
- `.gitignore` - Files to exclude from commits

---

## Notes

This skill should be followed for **ALL** commits to ensure:
- ✅ Roadmap stays up-to-date (checked FIRST)
- ✅ Time tracking stays current (Step 1.5 for notable work)
- ✅ Consistent commit history
- ✅ Proper version tracking
- ✅ Clean repository (no generated files)
- ✅ No attribution issues

**When in doubt, refer to this skill before committing!**

**Remember**: ROADMAP check is Step 1, time tracking is Step 1.5 - not afterthoughts!

**Version**: v3.0 (2026-01-07) - Added time tracking update requirement
