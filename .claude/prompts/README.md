# Custom Slash Commands

This directory contains custom slash commands for the EasyAirClaim project. These commands streamline common workflows and reduce repetitive instructions.

## Available Commands

### `/commit` - Automated Commit Workflow
**Purpose**: Automate the entire git commit process following best practices

**Usage**:
```
/commit
```

**What it does**:
1. Checks if ROADMAP.md needs updating
2. Updates ROADMAP.md if needed (phase completion or progress)
3. Reviews changes with `git status` and `git diff`
4. Stages files (excluding __pycache__, .env, etc.)
5. Writes Conventional Commit message (NO Claude attribution)
6. Creates version tag if phase complete
7. Pushes to GitHub

**When to use**: After completing any feature, bug fix, or documentation change

**Example output**:
```
✅ Committed Successfully

Type: feat(auth)
Message: implement JWT refresh token rotation
Files changed: 5
ROADMAP updated: Yes (marked task complete)
Version tag: None (in-progress phase)
Pushed to: origin/MVP
```

---

### `/phase-status` - Phase Progress Verification
**Purpose**: Quickly check actual implementation status vs. ROADMAP.md

**Usage**:
```
/phase-status
```

**What it does**:
1. Reads current phase from ROADMAP.md
2. Verifies implementation against codebase
3. Calculates actual completion percentage
4. Identifies discrepancies between roadmap and reality
5. Provides recommendations

**When to use**:
- Before updating roadmap
- When starting a new session
- To verify phase completion claims

**Example output**:
```
📊 Phase Status Report

Current Phase: Phase 4 - Customer Account Management
Roadmap Status: 80% complete
Actual Status: 45% complete
Discrepancy: -35%

✅ What's Complete:
- Account endpoints (app/routers/account.py:1-150)
- Database models (app/models.py:641-687)

❌ What's Missing:
- Admin deletion interface (marked done but not found)
- GDPR data export endpoint

🔍 Recommendations:
- Update ROADMAP.md percentage to 45%
- Mark admin interface as incomplete
```

---

### `/deploy-check` - Pre-Deployment Verification
**Purpose**: Comprehensive security and readiness audit before deployment

**Usage**:
```
/deploy-check
```

**What it does**:
1. Verifies all Phase 4.5 security issues are resolved
2. Checks configuration (CORS, DEBUG, ENVIRONMENT)
3. Scans for exposed secrets in git history
4. Checks dependency vulnerabilities
5. Verifies authentication and authorization
6. Checks GDPR compliance readiness
7. Provides deployment readiness assessment

**When to use**:
- Before deploying to testing/staging
- Before production deployment
- After security patches
- Weekly security checks

**Example output**:
```
🚀 Deployment Readiness Report

🔒 SECURITY AUDIT (Phase 4.5)
Critical Issues (BLOCKING):
✅ SQL Injection: FIXED
❌ Exposed Secrets: ACTION REQUIRED (rotate SMTP password)
✅ CORS Wildcard: FIXED

Status: 🟡 READY FOR TESTING (1 blocking issue for production)

📋 BLOCKING ISSUES
1. Rotate exposed SMTP credentials (see SECURITY_ACTION_REQUIRED.md)

✅ READY FOR DEPLOYMENT?
Testing Environment: YES
Production Environment: NO - Fix blocking issue first
```

---

### `/test` - Test Suite Runner
**Purpose**: Run tests and provide detailed results with coverage analysis

**Usage**:
```
/test
```

**What it does**:
1. Checks conda environment is activated
2. Runs pytest with coverage
3. Analyzes pass/fail results
4. Identifies low-coverage modules
5. Suggests tests to add
6. Highlights failures with fixes

**When to use**:
- After implementing features
- Before committing
- Before deployment
- After refactoring

**Example output**:
```
🧪 Test Suite Report

📊 Summary:
Tests Run: 45
Passed: ✅ 43 (95.6%)
Failed: ❌ 2 (4.4%)
Coverage: 78%

❌ Failed Tests:
1. test_authentication_flow
   File: app/tests/test_auth.py:45
   Error: AssertionError: Expected 200, got 401
   Suggestion: Check if JWT token is being passed correctly

📈 Coverage Analysis:
Low Coverage Files (<80%):
- app/services/file_service.py: 58%

💡 Recommendations:
1. Fix 2 failing tests in test_auth.py
2. Add error handling tests for file_service.py
```

---

## How Slash Commands Work

Slash commands are custom prompts stored in `.claude/prompts/`. When you type `/command-name`, Claude Code automatically loads and executes the prompt from `command-name.md`.

**Benefits**:
- No need to type long instructions
- Consistent execution every time
- Proactive automation (I do the work, not just suggest)
- Saves 5-10 messages per workflow

---

## Creating New Commands

To create a new slash command:

1. Create a markdown file in `.claude/prompts/`
   ```bash
   touch .claude/prompts/my-command.md
   ```

2. Write instructions for what I should do
   ```markdown
   # My Command

   Execute these steps:
   1. Do thing A
   2. Do thing B
   3. Report results
   ```

3. Use the command:
   ```
   /my-command
   ```

---

## Best Practices

### When to Use Slash Commands vs. Regular Messages

**Use slash commands for**:
- Repeated workflows (commits, tests, deploys)
- Multi-step processes with clear steps
- Audits and verification tasks
- Following documented procedures

**Use regular messages for**:
- Exploratory questions
- One-off tasks
- Brainstorming
- Ambiguous requirements

### Combining Commands

You can combine commands in one message:
```
/test
Then if tests pass, /commit
```

Or run sequentially:
```
/phase-status
```
*(after results)*
```
Update roadmap based on your findings, then /commit
```

---

## Command Customization

Feel free to modify these commands to match your workflow:

**Example modifications**:
- Change commit message format
- Add additional security checks to `/deploy-check`
- Customize test coverage thresholds
- Add notification steps

Just edit the `.md` file for the command!

---

## Troubleshooting

**Command not found?**
- Ensure file is in `.claude/prompts/`
- Ensure filename matches command (e.g., `/test` → `test.md`)
- No spaces in command names

**Command doesn't work as expected?**
- Check the `.md` file for typos
- Make instructions explicit and actionable
- Test with simple instructions first

**Want to see what a command does?**
```
Show me what /commit does
```

---

## Version History

- **v1.0** (2025-12-29): Initial command creation
  - `/commit` - Automated commit workflow
  - `/phase-status` - Phase verification
  - `/deploy-check` - Deployment readiness
  - `/test` - Test suite runner

---

## Related Files

- `.claude/skills/commit-workflow.md` - Detailed commit workflow documentation
- `ROADMAP.md` - Project roadmap and phase tracking
- `VERSIONING.md` - Version bump guidelines
- `CLAUDE.md` - Project instructions

---

**Remember**: Slash commands are shortcuts to make you more efficient. Use them liberally!
