# Pre-Deployment Checklist

Run comprehensive pre-deployment security and readiness verification.

## Instructions

**Execute all checks proactively and provide a deployment readiness report.**

### Step 1: Security Audit (Phase 4.5)
Check all Phase 4.5 security issues from ROADMAP.md:

**Critical Issues (MUST be fixed)**:
- [ ] SQL Injection vulnerabilities fixed?
- [ ] Exposed secrets removed from repository?
- [ ] CORS wildcard configuration fixed?
- [ ] Blacklist bypass fixed?

**High Priority Issues**:
- [ ] Rate limiting implemented?
- [ ] HTTPS configured (or handled by Cloudflare)?
- [ ] Password strength validation consistent?
- [ ] Security headers enabled?
- [ ] JWT token storage (HTTP-only cookies)?

**Medium Priority**:
- [ ] Database connection pool limits set?
- [ ] Security audit logging implemented?
- [ ] Input sanitization for XSS?

### Step 2: Configuration Verification
Check critical environment variables and config:

1. Read `.env.example` and compare with actual `.env` (without showing secrets)
2. Verify in `app/config.py`:
   - `ENVIRONMENT` setting
   - `DEBUG` mode
   - `CORS_ORIGINS` (should not be wildcard)
   - `SECURITY_HEADERS_ENABLED`
3. Check for hardcoded secrets or default passwords

### Step 3: Git Repository Check
1. Run `git status` - Check for uncommitted .env files
2. Check `.gitignore` includes:
   - `.env`
   - `__pycache__/`
   - `*.pyc`
   - `node_modules/`
3. Scan recent commits for accidentally committed secrets:
   ```bash
   git log --all --full-history --source -- ".env"
   ```

### Step 4: Dependency Vulnerabilities
1. Check for known vulnerabilities:
   ```bash
   # Python dependencies (if safety is installed)
   safety check || echo "Safety not installed - skipping"

   # Or just check if requirements are up to date
   pip list --outdated | head -20
   ```

### Step 5: Database & Infrastructure
1. Check database connection settings (without exposing credentials)
2. Verify async connection pool configuration
3. Check Redis configuration for Celery
4. Verify Nextcloud configuration

### Step 6: Authentication & Authorization
1. Verify JWT configuration:
   - Token expiration times reasonable?
   - SECRET_KEY is not default/weak?
2. Check RBAC implementation:
   - Admin-only endpoints protected?
   - Customer data ownership verified?
3. Verify blacklist enforcement

### Step 7: GDPR Compliance
1. Check account deletion workflow exists
2. Verify data export capability (Article 20)
3. Cookie consent implementation status
4. Privacy policy status

### Step 8: Testing Status
1. Check if tests pass:
   ```bash
   pytest --collect-only 2>/dev/null | grep "test session starts" || echo "Tests not configured"
   ```
2. Verify critical flows have tests

## Report Format

Provide output as:

```
🚀 Deployment Readiness Report
Generated: [date]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 SECURITY AUDIT (Phase 4.5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Critical Issues (BLOCKING):
✅ SQL Injection: FIXED
❌ Exposed Secrets: ACTION REQUIRED
✅ CORS Wildcard: FIXED
✅ Blacklist Bypass: FIXED

High Priority:
✅ Rate Limiting: IMPLEMENTED
⚠️ HTTPS: Handled by Cloudflare (testing)
✅ Security Headers: Handled by Cloudflare (testing)
❌ JWT Cookies: NOT IMPLEMENTED (Phase 4.5.14)

Status: 🔴 NOT READY / 🟡 READY FOR TESTING / 🟢 PRODUCTION READY

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENVIRONMENT: [production/development]
DEBUG: [true/false]
CORS_ORIGINS: [specific domains / wildcard]
SECURITY_HEADERS: [enabled/disabled]

Issues Found: [list]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 SECRETS & CREDENTIALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

.env in .gitignore: [yes/no]
.env in repository: [yes/no]
Default passwords: [found/not found]
Hardcoded secrets: [found/not found]

Action Required: [list or "None"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 BLOCKING ISSUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[List all issues that MUST be fixed before deployment]

1. Issue 1
2. Issue 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ WARNINGS (Recommended to fix)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[List recommended fixes]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ READY FOR DEPLOYMENT?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Testing Environment: [YES/NO] - [reason]
Production Environment: [YES/NO] - [reason]

Next Steps:
1. [Action item 1]
2. [Action item 2]
```

## Execution Notes

- Be thorough but concise
- Highlight blocking issues clearly
- Provide actionable next steps
- Don't expose actual secrets in output
- Use color-coded status indicators (🔴🟡🟢)
