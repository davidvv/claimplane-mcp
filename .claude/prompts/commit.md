# Commit Workflow

Execute the complete commit workflow following `.claude/skills/commit-workflow.md`.

## Instructions

**Proactively execute all steps without asking permission unless truly necessary.**

### Step 1: Roadmap Check (MANDATORY FIRST)
1. Review what changed using `git status` and `git diff`
2. Determine if ROADMAP.md needs updating:
   - **Phase complete?** → Update ROADMAP.md (Section 1.1 of commit-workflow.md)
   - **Significant progress?** → Update ROADMAP.md (Section 1.2)
   - **Bug fix/small change?** → Skip roadmap update
3. If updating ROADMAP.md:
   - Update "Last Updated" date
   - Mark completed tasks with ✅
   - Update percentage if shown
   - Update "NEXT STEPS" section if phase complete
   - Update version in header if phase complete

### Step 2: Review Changes
1. Run `git status` to see all changes
2. Run `git diff` to review modifications
3. Check for files that shouldn't be committed:
   - ❌ `__pycache__/` files
   - ❌ `.env` files with secrets
   - ❌ `node_modules/`
   - ❌ Debug code or console.logs

### Step 3: Stage Files
1. Stage only relevant files (be selective)
2. **Include ROADMAP.md if it was updated**
3. Exclude generated/temporary files

### Step 4: Write Commit Message
Use Conventional Commits format:
```
<type>(<scope>): <short description>

<detailed explanation>

<list of changes>

Updated ROADMAP.md to reflect [completion/progress] (if applicable)
```

**Types**: feat, fix, docs, refactor, test, chore, perf

**CRITICAL**:
- ❌ NO Claude/Anthropic attribution
- ❌ NO "Co-Authored-By: Claude"
- ❌ NO "Generated with Claude Code"
- ✅ Mention ROADMAP.md update if applicable

### Step 5: Commit
Execute the commit with the message.

### Step 6: Check Versioning
- **Phase complete?** → Create version tag (v0.X.0)
- **Bug fix?** → Optional patch tag (v0.X.Y)
- **Regular commit?** → No tag needed

### Step 7: Create Tag (if needed)
Only for completed phases:
```bash
git tag -a v0.X.0 -m "Release v0.X.0 - Phase N: Title

Key features:
- Feature 1
- Feature 2

Brief description."
```

### Step 8: Push
1. Push commits: `git push origin MVP`
2. Push tags if created: `git push origin v0.X.0`

## Execution Style

- Be proactive - don't ask unless truly ambiguous
- Execute commands directly
- Show output of key commands (git status, git diff summary)
- Provide clear summary at the end

## Summary Format

At the end, provide:
```
✅ Committed Successfully

Type: <type>(<scope>)
Message: <summary>
Files changed: <count>
ROADMAP updated: Yes/No
Version tag: v0.X.0 / None
Pushed to: origin/MVP
```
