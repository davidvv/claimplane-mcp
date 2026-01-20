# Test Plan: Draft Resume UX (WP 196)

## Test Date: 2026-01-20

## Overview
This test validates the fix for the race condition in draft claim resume flow. The fix addresses:
1. **Race Condition**: Using useRef to prevent double verification in React Strict Mode
2. **SessionStorage Timing**: Reading sessionStorage BEFORE it's cleared
3. **Immediate Cleanup**: Clearing sessionStorage immediately after reading (not in setTimeout)

## Prerequisites
- Services running via `./start-dev.sh`
- Browser with DevTools open (Console tab)
- Test email: `florian.luhn@outlook.com`
- Test draft ID: `5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f`
- Customer ID: `548f8da6-e539-40d5-8050-e5ee73ddca81`

## Test Procedure

### Step 1: Initial Setup
1. Open browser to http://localhost:3000
2. Open DevTools Console (F12)
3. Clear browser cookies/logout if logged in
4. Verify you're logged out (no user menu visible)

### Step 2: Initiate Draft Resume Flow
1. Navigate to: `http://localhost:3000/claim/new?resume=5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f`
2. **Expected**: Automatic redirect to `/auth` page
3. **Expected**: Banner appears with message "Welcome back! You'll be returned to your draft claim after logging in."
4. **Verify Console**: Check for log showing sessionStorage was set:
   ```
   postLoginRedirect set to: /claim/new?resume=5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f
   ```

### Step 3: Request Magic Link
1. On `/auth` page, enter email: `florian.luhn@outlook.com`
2. Click "Send Magic Link" button
3. **Expected**: Success toast "Magic link sent!"
4. **Expected**: Email field clears

### Step 4: Get Magic Link Token
Choose ONE of these methods:

**Method A: Backend Logs (Recommended)**
```bash
docker compose logs api | grep "Magic link token" | tail -1
```

**Method B: Database Query**
```bash
docker compose exec db psql -U postgres -d flight_claim_db -c "SELECT token, expires_at FROM magic_link_tokens WHERE user_id = '548f8da6-e539-40d5-8050-e5ee73ddca81' ORDER BY created_at DESC LIMIT 1;"
```

Copy the token value (long alphanumeric string).

### Step 5: Verify Magic Link
1. Construct URL: `http://localhost:3000/auth/verify?token=<YOUR_TOKEN>`
2. Navigate to this URL
3. **CRITICAL CONSOLE CHECKS**:
   ```
   ✓ "Verifying magic link token..."
   ✓ "Pending redirect from sessionStorage: /claim/new?resume=5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f"
   ✓ "Magic link verification successful:"
   ✓ "Resuming interrupted flow: /claim/new?resume=5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f"
   
   ✗ Should NOT see: "Redirecting to My Claims page"
   ```

### Step 6: Verify Final State
1. **Final URL**: Must be `/claim/new?resume=5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f`
2. **Page Content**: Draft claim form loads in Step 3
3. **Pre-filled Data**:
   - Flight number: UA988
   - Departure: FRA (Frankfurt)
   - Arrival: IAD (Washington Dulles)
   - Date: 2025-08-18
   - Compensation: €600.00
4. **User Menu**: Shows "Florian Luhn" in top right

## Success Criteria

### ✅ Pass Conditions
- [ ] User lands on `/claim/new?resume=<draft_id>` (NOT `/my-claims`)
- [ ] Console shows "Resuming interrupted flow" message
- [ ] Console does NOT show "Redirecting to My Claims page"
- [ ] Draft data loads correctly in form
- [ ] No double verification (check for duplicate API calls in Network tab)
- [ ] sessionStorage cleared after use (check Application tab)

### ❌ Fail Conditions
- User redirected to `/my-claims`
- Console shows "Redirecting to My Claims page"
- Draft data doesn't load
- Double verification occurs (duplicate POST to `/auth/magic-link/verify`)
- sessionStorage not cleared

## Code References

### Key Files
- **Frontend**: `frontend_Claude45/src/pages/Auth/MagicLinkPage.tsx:36-92`
  - Line 36-38: Read sessionStorage BEFORE verification
  - Line 13: useRef to prevent double execution
  - Line 73-75: Clear sessionStorage immediately after reading

- **Frontend**: `frontend_Claude45/src/pages/Auth.tsx:32-33`
  - Banner display logic

## Debugging Tips

### If Test Fails

1. **Check sessionStorage timing**:
   - Add breakpoint at MagicLinkPage.tsx:38
   - Verify `pendingRedirect` contains correct URL
   - Step through to line 86 and verify it's still available

2. **Check for double execution**:
   - Network tab: Filter for `/auth/magic-link/verify`
   - Should see only ONE request
   - If two requests: useRef isn't working

3. **Check navigation logic**:
   - MagicLinkPage.tsx:83-92
   - Verify pendingRedirect is truthy
   - Verify it starts with '/'
   - Check navigate() is called with correct URL

4. **Check sessionStorage clearing**:
   - DevTools > Application > Storage > Session Storage
   - After login, `postLoginRedirect` should be removed

## Test Results

### Run 1: [DATE/TIME]
- **Tester**: 
- **Result**: [ ] PASS / [ ] FAIL
- **Notes**:

### Issues Found
1. 
2. 
3. 

### Screenshots
- [ ] Browser at /auth page with banner
- [ ] Console logs during verification
- [ ] Final page with loaded draft

---

## Technical Notes

### The Race Condition Fix

**Problem**: React Strict Mode calls useEffect twice in development, causing:
1. First call: Reads sessionStorage, verifies token, clears sessionStorage in setTimeout
2. Second call: Reads sessionStorage (still there), verifies token again, gets error (token used)
3. sessionStorage cleared by first call's setTimeout AFTER second call reads it

**Solution**:
1. `useRef` prevents second execution entirely
2. Read sessionStorage BEFORE verification API call
3. Clear sessionStorage immediately (not in setTimeout)
4. setTimeout only used for final navigation (cookie propagation)

### sessionStorage Flow
```
User clicks resume link
  ↓
RequireAuth sets: sessionStorage.postLoginRedirect = "/claim/new?resume=..."
  ↓
Redirect to /auth
  ↓
Auth page shows banner (reads sessionStorage)
  ↓
User requests magic link
  ↓
User clicks magic link → /auth/verify?token=...
  ↓
MagicLinkPage:
  1. Read pendingRedirect = sessionStorage.getItem('postLoginRedirect')
  2. Verify token (API call)
  3. Clear sessionStorage.removeItem('postLoginRedirect')
  4. setTimeout → navigate(pendingRedirect)
```

### Why setTimeout Still Used
The 500ms setTimeout is kept for the final navigation to ensure:
- HTTP-only cookies are properly set by browser
- Authentication state propagates before navigation
- Avoid race condition between cookie setting and API calls on next page
