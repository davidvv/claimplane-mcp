# Branch Management Policy

## DO NOT create auto-generated branches!

**Work on these branches only:**
- `UI` - Frontend development
- `MVP` - Main development branch (backend)
- `main` - Production-ready code

## For Claude Code CLI users:
- Always work on the current branch
- Commit directly to `UI` or `MVP` branches
- Only create feature branches for major features (use descriptive names)

## For Claude Code Web users:
- Those auto-generated branches with session IDs (like `claude/check-ui-branch-sync-011CUpm...`) are created by Claude Code Web
- **Switch to Claude Code CLI** or manually merge and delete those branches immediately

## Branch Naming Convention:
- ✅ Good: `feature/magic-links`, `fix/phone-validation`, `UI`, `MVP`
- ❌ Bad: `claude/check-ui-branch-sync-011CUpmwZWMqQnurm8yXrz73`

## Current Status:
- **Active branch**: `UI`
- **All changes**: Should be committed to `UI` branch
- Auto-generated branches have been deleted

---
Last updated: 2025-11-06
