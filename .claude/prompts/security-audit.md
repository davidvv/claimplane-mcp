# Security Audit

Perform comprehensive security scan of the entire codebase and configuration.

## Instructions

Execute all security checks proactively and provide detailed vulnerability report.

### Step 1: Code Scanning
Search for common security vulnerabilities:

1. **SQL Injection**:
   - Search for f-strings in SQL queries: `Grep` for `f".*SELECT|UPDATE|DELETE|INSERT`
   - Search for string concatenation in queries: `Grep` for `+.*WHERE|SET`
   - Check repositories for proper parameterization

2. **Hardcoded Secrets**:
   - Search for passwords: `Grep` for `password.*=.*["'](?!{|<)`
   - Search for API keys: `Grep` for `api_key.*=.*["']`
   - Search for tokens: `Grep` for `token.*=.*["']`
   - Search for SECRET_KEY hardcoded values

3. **XSS Vulnerabilities**:
   - Search for unescaped HTML: `Grep` for `innerHTML|dangerouslySetInnerHTML`
   - Check email templates for proper escaping
   - Search for direct DOM manipulation

4. **Authentication Issues**:
   - Check for missing auth decorators: Find routes without `Depends(get_current_user)`
   - Search for commented auth: `Grep` for `# .*Depends\(get_current`
   - Check for hardcoded admin credentials

5. **File Upload Vulnerabilities**:
   - Check MIME type validation
   - Check file size limits
   - Check for path traversal: `Grep` for `\.\.\/|\.\.\\`
   - Verify file extension whitelist

### Step 2: Dependency Vulnerabilities
```bash
# Check for outdated packages with known vulnerabilities
pip list --outdated

# If safety is installed, run it
command -v safety && safety check || echo "Safety not installed"
```

### Step 3: Configuration Security
Check all config files:

1. `app/config.py`:
   - DEBUG mode settings
   - SECRET_KEY strength
   - CORS configuration
   - Allowed hosts

2. `.env.example` vs `.env`:
   - Verify no secrets in .env.example
   - Check for default/weak values

3. `docker-compose.yml`:
   - Check for exposed ports
   - Check for default passwords
   - Verify environment variable usage

### Step 4: OWASP Top 10 Check
Verify protection against:

1. **A01:2021 - Broken Access Control**
   - IDOR protection in file downloads
   - Role-based access control enforcement
   - Ownership verification

2. **A02:2021 - Cryptographic Failures**
   - Password hashing (bcrypt)
   - File encryption (Fernet)
   - HTTPS usage
   - JWT secret strength

3. **A03:2021 - Injection**
   - SQL injection (parameterized queries)
   - Command injection
   - LDAP injection

4. **A05:2021 - Security Misconfiguration**
   - Debug mode in production
   - Default credentials
   - Unnecessary services enabled

5. **A07:2021 - Identification and Authentication Failures**
   - Weak password policy
   - Session timeout
   - Account lockout

### Step 5: Git History Scan
Check for accidentally committed secrets:

```bash
# Search for .env files in history
git log --all --full-history --source -- ".env"

# Search for common secret patterns
git log -p --all | grep -i "password\|secret\|api_key" | head -50
```

### Step 6: Frontend Security
1. Check for API keys in frontend code
2. Verify CORS configuration
3. Check for sensitive data in localStorage
4. Verify JWT token storage method

## Report Format

```
🔒 SECURITY AUDIT REPORT
Generated: [timestamp]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 CRITICAL VULNERABILITIES (Fix Immediately)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[List critical issues with CVSS scores if known]

1. SQL Injection in customer_repository.py:27
   CVSS: 9.0 (Critical)
   Impact: Complete database compromise
   Fix: Use parameterized queries with bindparam()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟠 HIGH SEVERITY (Fix Before Production)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[List high severity issues]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 MEDIUM SEVERITY (Recommended to Fix)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[List medium severity issues]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 LOW SEVERITY / INFORMATIONAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[List low severity issues and best practices]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ SECURITY STRENGTHS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- JWT authentication implemented
- Password hashing with bcrypt (12 rounds)
- File encryption with Fernet
- Rate limiting on auth endpoints
- RBAC properly enforced

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Critical: X
High: Y
Medium: Z
Low: A
Total: B

Security Score: [0-100]

Production Ready: [YES/NO]
Recommendations: [number] issues to fix

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 PRIORITY ACTION ITEMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [Most critical action]
2. [Second priority]
3. [Third priority]
```

## Execution Notes

- Be thorough - scan every file type (Python, TypeScript, config)
- Provide file paths and line numbers for all findings
- Include CVSS scores if applicable
- Prioritize by severity and exploitability
- Suggest specific fixes, not just "fix this"
- Don't expose actual secret values in report
