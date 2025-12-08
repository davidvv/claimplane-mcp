# Git Pull Reminder Skill

## Purpose
This skill ensures Claude Code always pulls the latest changes from GitHub before starting work on the codebase, unless explicitly instructed otherwise by the user.

## When to Use
**AUTOMATICALLY** at the start of EVERY new conversation or work session, UNLESS the user specifically says otherwise (e.g., "don't pull", "work on local changes", "I just pulled").

## Workflow

### 1. Check Git Status First
Before pulling, always check if there are uncommitted local changes:

```bash
git status
```

**If there are uncommitted changes:**
- Alert the user: "You have uncommitted local changes. Would you like me to stash them before pulling, or should we skip the pull?"
- Wait for user decision
- If user says to stash: `git stash`
- If user says to skip: Skip the pull and proceed with work

**If working directory is clean:**
- Proceed with pull

### 2. Pull Latest Changes
```bash
git pull origin $(git branch --show-current)
```

### 3. Handle Merge Conflicts
If conflicts occur:
- Alert the user immediately
- List conflicting files
- Ask: "There are merge conflicts in [files]. Would you like me to help resolve them, or would you prefer to handle them manually?"

### 4. Restore Stashed Changes (if applicable)
If changes were stashed in step 1:
```bash
git stash pop
```

If conflicts occur during stash pop, alert the user.

### 5. Confirm Success
After successful pull, briefly confirm:
- "Pulled latest changes from [branch]"
- Only mention if there were actual updates (not if already up to date)

## Important Notes

- **Default behavior**: ALWAYS pull at session start unless user says otherwise
- **Respect user intent**: If user says "don't pull" or mentions working on local uncommitted changes, skip the pull
- **Be concise**: Don't make a big deal about it - just do it and confirm briefly
- **Safety first**: Never lose user's local changes - always check status first

## Examples

### Example 1: Clean Pull
```
User: "Help me add a new feature"
Claude: [Checks git status - clean]
Claude: [Runs git pull]
Claude: "Pulled latest changes from MVP. Ready to help with the new feature!"
```

### Example 2: Local Changes
```
User: "Can you review my code?"
Claude: [Checks git status - uncommitted changes detected]
Claude: "You have uncommitted changes in 3 files. Should I stash them before pulling the latest version, or work with your current local changes?"
```

### Example 3: User Explicitly Says Not To
```
User: "Don't pull, I'm working on local changes. Help me debug this function."
Claude: [Skips pull entirely]
Claude: "Sure, let me help you debug that function."
```

## Integration with Development Workflow

This skill complements the existing development workflow:
1. **First**: Pull latest (this skill)
2. **Then**: Activate conda environment (per DEVELOPMENT_WORKFLOW.md)
3. **Finally**: Start working on tasks

---

**Status**: Active
**Created**: 2025-12-07
**Auto-trigger**: Yes (at session start)
