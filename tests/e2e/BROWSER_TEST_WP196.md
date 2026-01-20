# Browser Test for Draft Resume UX Fix (WP 196)

## Test Status: API Flow ✅ PASSED

The automated API test confirms that the backend flow is working correctly:
- Magic link generation: ✅
- Token verification: ✅
- Draft claim access: ✅

## Manual Browser Test Required

Since we cannot run automated browser tests (Playwright not available), please perform the following manual test:

### Prerequisites
1. Ensure all services are running: `./start-dev.sh`
2. Draft claim ID: `5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f`
3. Test email: `florian.luhn@outlook.com`

### Test Steps

#### Step 1: Clear Browser State
1. Open browser in **Incognito/Private mode**
2. Navigate to: `http://localhost:3000`
3. Open DevTools (F12)
4. Go to Console tab
5. Clear any existing storage:
   ```javascript
   sessionStorage.clear();
   localStorage.clear();
   ```

#### Step 2: Navigate to Draft Resume URL
1. In the address bar, navigate to:
   ```
   http://localhost:3000/claim/new?resume=5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f
   ```
2. Press Enter

#### Step 3: Verify Redirect to /auth
1. ✅ **VERIFY**: URL should now be `/auth` (with query params)
2. ✅ **VERIFY**: Page shows "Welcome back!" banner
3. ✅ **VERIFY**: Email input field is visible

#### Step 4: Check sessionStorage
1. In DevTools Console, run:
   ```javascript
   sessionStorage.getItem('postLoginRedirect')
   ```
2. ✅ **VERIFY**: Should return: `"/claim/new?resume=5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f"`

#### Step 5: Request Magic Link
1. Enter email: `florian.luhn@outlook.com`
2. Click "Send Magic Link" button
3. ✅ **VERIFY**: Success message appears
4. Watch Console for log messages:
   - Should see: "Pending redirect from sessionStorage"
   - Should see: "Resuming interrupted flow"
   - Should NOT see: "Redirecting to My Claims page"

#### Step 6: Get Magic Link Token
Run this command in terminal:
```bash
docker exec flight_claim_db psql -U postgres -d flight_claim -t -c \
  "SELECT token FROM magic_link_tokens 
   WHERE user_id = '548f8da6-e539-40d5-8050-e5ee73ddca81' 
   ORDER BY created_at DESC LIMIT 1;" | tr -d ' '
```

Copy the token output.

#### Step 7: Navigate to Magic Link
1. In browser address bar, navigate to:
   ```
   http://localhost:3000/auth/magic-link?token=<PASTE_TOKEN_HERE>
   ```
2. Press Enter
3. Wait for verification to complete (2-3 seconds)

#### Step 8: CRITICAL CHECK - Verify Final URL
1. ✅ **VERIFY**: Final URL should be:
   ```
   http://localhost:3000/claim/new?resume=5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f
   ```
2. ❌ **FAIL IF**: URL is `/my-claims` or anything else
3. ✅ **VERIFY**: Draft claim data is loaded in the form
4. ✅ **VERIFY**: Flight number shows "UA988"
5. ✅ **VERIFY**: Route shows "FRA → IAD"

#### Step 9: Check Console Logs
1. In DevTools Console, review all logs
2. ✅ **VERIFY**: No errors related to redirect
3. ✅ **VERIFY**: Saw "Resuming interrupted flow" message
4. ❌ **FAIL IF**: Saw "Redirecting to My Claims page"

### Expected Console Log Flow

```
[INFO] Pending redirect from sessionStorage
[INFO] Resuming interrupted flow: /claim/new?resume=5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f
[SUCCESS] Draft claim loaded
```

### Screenshots to Capture

1. `01_auth_page_welcome_banner.png` - /auth page with "Welcome back!" banner
2. `02_session_storage_check.png` - DevTools showing sessionStorage content
3. `03_final_page_url.png` - Final page showing correct URL and draft data
4. `04_console_logs.png` - Console showing redirect flow logs

### Test Result

- [ ] **PASS**: Redirected to draft resume page after magic link login
- [ ] **FAIL**: Redirected to /my-claims instead

### Notes

Record any observations, errors, or unexpected behavior here:

---

## Automated API Test Results

The following API test was run successfully:

```bash
./tests/e2e/test_draft_resume_manual.sh
```

**Results:**
- ✅ Magic link request: SUCCESS
- ✅ Token generation: SUCCESS  
- ✅ Token verification: SUCCESS
- ✅ Draft claim access: SUCCESS
- ✅ Draft status verified: "draft"

This confirms the backend is working correctly. The browser test is needed to verify the frontend redirect logic.
