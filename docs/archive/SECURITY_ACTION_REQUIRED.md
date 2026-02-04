# 🚨 SECURITY ACTION REQUIRED

## Exposed SMTP Credentials - Immediate Action Needed

### What Happened
Your `.env` file containing SMTP credentials was committed to git history (commit 1c12739e). This means the following Gmail app password is exposed in your git repository:

**Exposed Gmail Account:** `claimplane@gmail.com`
**Exposed App Password:** `ybikt nslj gyzf zhpg`

### Required Actions

#### 1. Rotate SMTP Credentials (CRITICAL - Do This First)

**Gmail App-Specific Password Rotation:**

1. **Revoke the exposed app password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Find the app password named for this application
   - Click "Remove" to revoke it

2. **Generate a new app password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other (Custom name)" → Name it "ClaimPlane Production"
   - Copy the generated 16-character password

3. **Update your `.env` file:**
   ```bash
   SMTP_PASSWORD=your-new-16-character-password-here
   ```

4. **Restart your application:**
   ```bash
   # If using Docker
   docker-compose restart api celery_worker
   
   # If running locally
   # Kill and restart your uvicorn and celery processes
   ```

#### 2. Verify .env is Now Untracked

The `.env` file has been removed from git tracking. Verify:

```bash
git status
# Should show .env as untracked (red)

git ls-files | grep "^\.env$"
# Should return nothing
```

#### 3. Use .env.example for New Setups

A new `.env.example` file has been created without sensitive data. Use this as a template:

```bash
cp .env.example .env
# Then fill in your actual values
```

#### 4. Clean Git History (Optional but Recommended)

**WARNING:** This rewrites git history. Only do this if:
- This is a private repository
- You can coordinate with all team members
- You understand the implications

**Option A: Use BFG Repo-Cleaner (Recommended)**
```bash
# Install BFG
brew install bfg  # macOS
# or download from: https://rtyley.github.io/bfg-repo-cleaner/

# Backup your repo first
cp -r /path/to/flight_claim /path/to/flight_claim_backup

# Remove .env from all commits
bfg --delete-files .env flight_claim
cd flight_claim
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

**Option B: Use git-filter-repo**
```bash
# Install git-filter-repo
pip install git-filter-repo

# Backup first
cp -r /path/to/flight_claim /path/to/flight_claim_backup

# Remove .env
git filter-repo --invert-paths --path .env

# Force push (coordinate with team first!)
git push origin --force --all
```

#### 5. Monitor for Suspicious Activity

- Check your Gmail account for suspicious activity
- Review recent sent emails from claimplane@gmail.com
- Enable 2FA on the Gmail account if not already enabled
- Consider creating a new Gmail account if you suspect compromise

### What We've Fixed

✅ Untracked `.env` from git  
✅ Created `.env.example` template  
✅ `.env` is in `.gitignore` (already was)  
✅ All future commits won't include `.env`

### Still TODO

❌ **You must manually rotate the SMTP password** (see step 1 above)  
⚠️ **Optional:** Clean git history to remove old .env commits

### Testing Email After Rotation

After rotating credentials, test email sending:

```bash
# Check celery worker logs
docker-compose logs -f celery_worker

# Or if running locally
# Check your celery terminal output
```

Try sending a test claim submission email to verify the new credentials work.

---

**Questions?** Check the security audit: `docs/SECURITY_AUDIT_v0.2.0.md`

**Next Steps:** After rotating credentials, continue with remaining security fixes in `ROADMAP.md` Phase 4.5
