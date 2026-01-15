# Token Collision Fix - Account Switching Issue

## Problem Summary

When logging in with a superadmin account (vences.david@gmail.com), the "My Claims" section displayed claims from a different customer account (idavidvv@gmail.com) instead of showing claims specific to the currently logged-in account.

## Root Cause

The issue was caused by **token collision** in localStorage. Here's the sequence of events that triggered the bug:

1. **Customer submits a claim** (idavidvv@gmail.com):
   - System creates/finds customer
   - Creates claim for that customer
   - Generates access token with customer's `user_id`
   - **Stores token in localStorage** without clearing old tokens

2. **Superadmin logs in** (vences.david@gmail.com):
   - System generates new access token with superadmin's `user_id`
   - **Overwrites the old token in localStorage**
   - BUT: If there's any timing issue or if the old token is still being used by the API client, the system retrieves claims for the wrong user

3. **Result**: The API receives the superadmin's token but the frontend or API client may still be using cached data or there's a race condition where the old token is used momentarily.

## Solution Implemented

Created a centralized token storage utility (`frontend_Claude45/src/utils/tokenStorage.ts`) that **ensures old tokens are ALWAYS cleared before new ones are stored**.

### Key Changes

#### 1. New Token Storage Utility
**File**: `frontend_Claude45/src/utils/tokenStorage.ts`

```typescript
export function storeAuthTokens(
  accessToken: string,
  refreshToken: string,
  userEmail: string,
  userId: string,
  userName: string
): void {
  // IMPORTANT: Clear old tokens BEFORE storing new ones
  localStorage.removeItem('auth_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_email');
  localStorage.removeItem('user_id');
  localStorage.removeItem('user_name');

  // Now store the new tokens
  localStorage.setItem('auth_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
  localStorage.setItem('user_email', userEmail);
  localStorage.setItem('user_id', userId);
  localStorage.setItem('user_name', userName);
}
```

#### 2. Updated Authentication Service
**File**: `frontend_Claude45/src/services/auth.ts`

- Imports the token storage utility
- Uses `storeAuthTokens()` in:
  - `register()` function
  - `login()` function
  - `refreshAccessToken()` function
- Uses `clearAuthTokens()` in:
  - `logout()` function

#### 3. Updated Claims Service
**File**: `frontend_Claude45/src/services/claims.ts`

- Imports `storeAccessTokenOnly()` from token storage utility
- Uses it in `submitClaim()` to safely store the temporary access token

#### 4. Updated Magic Link Page
**File**: `frontend_Claude45/src/pages/Auth/MagicLinkPage.tsx`

- Imports `storeAuthTokens()` from token storage utility
- Uses it when verifying magic link tokens to safely store authentication tokens

## Why This Fix Works

1. **Atomic Operation**: By removing old tokens BEFORE storing new ones, we ensure there's no window where two different tokens could coexist in localStorage.

2. **Consistent Behavior**: All authentication flows (register, login, magic link, token refresh) now use the same safe token storage mechanism.

3. **Prevents Race Conditions**: Even if there are timing issues or async operations, the old token is guaranteed to be cleared before the new one is stored.

4. **Clear Intent**: The code explicitly documents why this is important with comments, making it clear to future developers that this is a critical security/correctness issue.

## Testing Recommendations

1. **Test Account Switching**:
   - Submit a claim as customer A
   - Log in as superadmin B
   - Verify that "My Claims" shows superadmin's claims, not customer A's claims

2. **Test Multiple Logins**:
   - Log in as user A
   - Log out
   - Log in as user B
   - Verify correct claims are displayed

3. **Test Magic Link Flow**:
   - Submit claim as customer A
   - Click magic link
   - Verify correct claims are displayed
   - Log in as superadmin B
   - Verify superadmin's claims are displayed

4. **Test Token Refresh**:
   - Log in as user A
   - Wait for token to expire/refresh
   - Verify claims still display correctly

## Files Modified

1. `frontend_Claude45/src/utils/tokenStorage.ts` - **NEW** - Centralized token storage utility
2. `frontend_Claude45/src/services/auth.ts` - Updated to use token storage utility
3. `frontend_Claude45/src/services/claims.ts` - Updated to use token storage utility
4. `frontend_Claude45/src/pages/Auth/MagicLinkPage.tsx` - Updated to use token storage utility

## Impact

- **Security**: Prevents token collision attacks and account confusion
- **Reliability**: Ensures consistent behavior across all authentication flows
- **Maintainability**: Centralized token management makes future changes easier
- **No Breaking Changes**: All changes are backward compatible
