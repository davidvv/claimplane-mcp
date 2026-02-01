/**
 * Authentication service - integrates with Phase 3 JWT backend
 * Uses HTTP-only cookies for secure token storage
 */
import apiClient from './api';

/**
 * Helper function to safely build display name from user data
 * Prevents "undefined undefined" issue when name fields are null/undefined
 *
 * @param firstName - User's first name (may be null/undefined)
 * @param lastName - User's last name (may be null/undefined)
 * @param email - User's email as fallback (optional)
 * @returns A safe display name string
 */
export function buildDisplayName(
  firstName: string | null | undefined,
  lastName: string | null | undefined,
  email?: string | null
): string {
  // Trim and filter out null/undefined/empty values
  const first = firstName?.trim();
  const last = lastName?.trim();

  // If we have both parts, concatenate them
  if (first && last) {
    return `${first} ${last}`;
  }

  // If we have only one part, use it
  if (first) return first;
  if (last) return last;

  // Fallback to email or generic "User"
  return email?.trim() || 'User';
}

// Types matching Phase 3 backend
export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    phone: string | null;
    role: 'customer' | 'admin' | 'superadmin';
    is_active: boolean;
    is_email_verified: boolean;
    created_at: string;
    last_login_at: string;
  };
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  };
}

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  address: {
    street: string | null;
    city: string | null;
    postalCode: string | null;
    country: string | null;
  } | null;
  role: 'customer' | 'admin' | 'superadmin';
  is_active: boolean;
  is_email_verified: boolean;
  created_at: string;
  last_login_at: string;
}

/**
 * Register a new user
 */
export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/register', data);

  // Tokens are automatically stored in HTTP-only cookies by the backend
  // Store user info in localStorage for UI purposes only (not security-sensitive)
  if (response.data.user) {
    // Validate that we have all required fields
    if (!response.data.user.email || !response.data.user.first_name || !response.data.user.last_name) {
      console.error('Backend returned incomplete user data during registration');
      throw new Error('Registration failed: Incomplete user data received');
    }

    const displayName = buildDisplayName(
      response.data.user.first_name,
      response.data.user.last_name,
      response.data.user.email
    );
    sessionStorage.setItem('user_email', response.data.user.email);
    sessionStorage.setItem('user_id', response.data.user.id);
    sessionStorage.setItem('user_name', displayName);
    sessionStorage.setItem('user_role', response.data.user.role);
  }

  return response.data;
}

/**
 * Login with email and password
 */
export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/login', data);

  // Tokens are automatically stored in HTTP-only cookies by the backend
  // Store user info in sessionStorage for UI purposes only (not security-sensitive)
  if (response.data.user) {
    // Validate that we have all required fields
    if (!response.data.user.email || !response.data.user.first_name || !response.data.user.last_name) {
      console.error('Backend returned incomplete user data during login');
      throw new Error('Login failed: Incomplete user data received');
    }

    const displayName = buildDisplayName(
      response.data.user.first_name,
      response.data.user.last_name,
      response.data.user.email
    );
    sessionStorage.setItem('user_email', response.data.user.email);
    sessionStorage.setItem('user_id', response.data.user.id);
    sessionStorage.setItem('user_name', displayName);
    sessionStorage.setItem('user_role', response.data.user.role);
  }

  return response.data;
}

/**
 * Logout - revoke refresh token
 */
export async function logout(): Promise<void> {
  try {
    // Backend will read refresh_token from HTTP-only cookie and clear it
    await apiClient.post('/auth/logout');
  } catch (error) {
    // Continue with logout even if API call fails
    console.error('Logout API call failed:', error);
  }

  // Clear user info from sessionStorage (UI state only, tokens are in cookies)
  clearLocalAuthState();

  // Cookies are cleared by the backend
  // Redirect will be handled by the caller
}

/**
 * Get current user profile
 */
export async function getCurrentUser(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>('/customers/me');
  // Map the response to match our interface
  const data = response.data as any;
  return {
    id: data.id,
    email: data.email,
    first_name: data.firstName || data.first_name,
    last_name: data.lastName || data.last_name,
    phone: data.phone,
    address: data.address,
    role: data.role,
    is_active: data.is_active,
    is_email_verified: data.is_email_verified,
    created_at: data.createdAt || data.created_at,
    last_login_at: data.lastLoginAt || data.last_login_at,
  };
}

/**
 * Update current user profile
 */
export async function updateUserProfile(data: Partial<{
  first_name: string;
  last_name: string;
  phone: string;
  street: string;
  city: string;
  postal_code: string;
  country: string;
}>): Promise<UserProfile> {
  const response = await apiClient.put<UserProfile>('/customers/me', data);
  return response.data;
}

/**
 * Refresh access token using refresh token
 */
export async function refreshAccessToken(): Promise<{ access_token: string; refresh_token: string }> {
  // Backend reads refresh_token from HTTP-only cookie
  const response = await apiClient.post<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  }>('/auth/refresh');

  // Tokens are automatically updated in HTTP-only cookies by the backend
  // No need to manually store them

  return {
    access_token: response.data.access_token,
    refresh_token: response.data.refresh_token,
  };
}

/**
 * Change password (requires current password)
 */
export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  await apiClient.post('/auth/password/change', {
    old_password: oldPassword,
    new_password: newPassword,
  });
}

/**
 * Request password reset email
 */
export async function requestPasswordReset(email: string): Promise<void> {
  await apiClient.post('/auth/password/reset-request', { email });
}

/**
 * Confirm password reset with token
 */
export async function confirmPasswordReset(token: string, newPassword: string): Promise<void> {
  await apiClient.post('/auth/password/reset-confirm', {
    token,
    new_password: newPassword,
  });
}

/**
 * Check if user is authenticated
 *
 * Note: With HTTP-only cookies, we can't check the actual tokens from JavaScript.
 * This checks if we have VALID user info in sessionStorage (set after successful login).
 * The backend will ultimately verify authentication via HTTP-only cookies.
 *
 * This is for UI purposes only - the actual auth is verified by the backend.
 */
export function isAuthenticated(): boolean {
  // Get user info and let getStoredUserInfo() validate and clean up if needed
  const userInfo = getStoredUserInfo();

  // Must have both email and name to be considered authenticated
  return !!(userInfo.email && userInfo.name);
}

/**
 * Get stored user info
 *
 * Note: This returns user info stored in sessionStorage for UI purposes.
 * The actual authentication is verified by the backend via HTTP-only cookies.
 * Tokens are NOT stored in sessionStorage - only user display info.
 *
 * This function detects and CLEARS broken/invalid user data to force re-login.
 */
export function getStoredUserInfo() {
  const email = sessionStorage.getItem('user_email');
  const id = sessionStorage.getItem('user_id');
  const name = sessionStorage.getItem('user_name');
  const role = sessionStorage.getItem('user_role');

  // If no auth data exists at all, this is a guest state - return empty and stop here.
  // We check for email, name, and id to cover all bases of a partial session.
  // This prevents the "invalid user data" check from triggering incorrectly for guests.
  if (!email && !name && !id) {
    return {
      email: null,
      id: null,
      name: null,
      role: null,
    };
  }

  // Detect broken names (e.g., "undefined undefined", "null null", "null undefined", etc.)
  // This helps catch issues where name fields were concatenated incorrectly.
  const isBrokenName = name && (
    name.includes('undefined') ||
    name.includes('null') ||
    name.trim() === '' ||
    name === '[object Object]' // Just in case
  );

  // If we have SOME data but it's broken or incomplete (missing required fields),
  // then we clear it to force a clean login state. 
  // We only reach here if at least one of (email, name, id) is present.
  if (isBrokenName || !email || !name) {
    console.warn('Detected invalid user data in sessionStorage, clearing auth state');
    console.warn('Broken data:', { email, id, name, role });
    clearLocalAuthState();
    return {
      email: null,
      id: null,
      name: null,
      role: null,
    };
  }

  return {
    email,
    id,
    name,
    role,
  };
}

/**
 * Clear local authentication state
 *
 * Removes user info from sessionStorage.
 * Note: This does NOT clear HTTP-only cookies - call logout() for that.
 */
export function clearLocalAuthState(): void {
  sessionStorage.removeItem('user_email');
  sessionStorage.removeItem('user_id');
  sessionStorage.removeItem('user_name');
  sessionStorage.removeItem('user_role');
}

/**
 * Validate current session with backend
 *
 * Checks if the HTTP-only cookies are still valid by calling /auth/me
 * If session is invalid, automatically clears localStorage to sync UI state
 *
 * @returns Promise<boolean> - true if session is valid, false otherwise
 */
export async function validateSession(): Promise<boolean> {
  try {
    // If no localStorage data, no need to validate
    if (!isAuthenticated()) {
      return false;
    }

    // Call /auth/me to validate cookies
    const response = await apiClient.get('/auth/me');

    // If successful, session is valid
    // Optionally update sessionStorage with latest user data
    if (response.data) {
      const userData = response.data;
      const displayName = buildDisplayName(
        userData.first_name,
        userData.last_name,
        userData.email
      );

      // If the backend gave us invalid data (no email or broken names), clear session
      if (!userData.email || !userData.first_name || !userData.last_name) {
        console.warn('Backend returned invalid user data, clearing session');
        console.warn('Invalid data:', {
          email: userData.email,
          first_name: userData.first_name,
          last_name: userData.last_name
        });
        clearLocalAuthState();
        return false;
      }

      sessionStorage.setItem('user_email', userData.email);
      sessionStorage.setItem('user_id', userData.id);
      sessionStorage.setItem('user_name', displayName);
      sessionStorage.setItem('user_role', userData.role);
      return true;
    }

    return false;
  } catch (error: any) {
    // If 401, cookies are invalid - clear sessionStorage
    if (error.response?.status === 401) {
      console.log('Session expired - clearing local auth state');
      clearLocalAuthState();
      return false;
    }

    // For other errors (network, 500, etc.), assume session might still be valid
    // Don't clear sessionStorage on network errors
    console.error('Session validation error (network issue, keeping local state):', error);
    return isAuthenticated(); // Return current sessionStorage state
  }
}

/**
 * Synchronize authentication state
 *
 * Ensures sessionStorage is in sync with actual session state.
 * Call this on app initialization and periodically during use.
 *
 * @returns Promise<boolean> - true if user is authenticated
 */
export async function syncAuthState(): Promise<boolean> {
  return await validateSession();
}

/**
 * Set a temporary auth token for API calls (used by draft claims workflow)
 *
 * This is used when we receive an access token from the /claims/draft endpoint
 * before the user has fully authenticated. The token is stored for API calls.
 *
 * Note: This is a client-side token for the draft workflow, separate from
 * the HTTP-only cookie-based auth used for logged-in users.
 */
let draftAuthToken: string | null = null;

export function setAuthToken(token: string | null): void {
  draftAuthToken = token;
  if (token) {
    sessionStorage.setItem('draftAuthToken', token);
  } else {
    sessionStorage.removeItem('draftAuthToken');
  }
}

export function getAuthToken(): string | null {
  return draftAuthToken || sessionStorage.getItem('draftAuthToken');
}
