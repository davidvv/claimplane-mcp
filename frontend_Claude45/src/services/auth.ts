/**
 * Authentication service - integrates with Phase 3 JWT backend
 * Uses HTTP-only cookies for secure token storage
 */
import apiClient from './api';

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
    localStorage.setItem('user_email', response.data.user.email);
    localStorage.setItem('user_id', response.data.user.id);
    localStorage.setItem('user_name', `${response.data.user.first_name} ${response.data.user.last_name}`);
    localStorage.setItem('user_role', response.data.user.role);
  }

  return response.data;
}

/**
 * Login with email and password
 */
export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/login', data);

  // Tokens are automatically stored in HTTP-only cookies by the backend
  // Store user info in localStorage for UI purposes only (not security-sensitive)
  if (response.data.user) {
    localStorage.setItem('user_email', response.data.user.email);
    localStorage.setItem('user_id', response.data.user.id);
    localStorage.setItem('user_name', `${response.data.user.first_name} ${response.data.user.last_name}`);
    localStorage.setItem('user_role', response.data.user.role);
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

  // Clear user info from localStorage (UI state only, tokens are in cookies)
  localStorage.removeItem('user_email');
  localStorage.removeItem('user_id');
  localStorage.removeItem('user_name');
  localStorage.removeItem('user_role');

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
 * This checks if we have user info in localStorage (set after successful login).
 * The backend will ultimately verify authentication via HTTP-only cookies.
 *
 * This is for UI purposes only - the actual auth is verified by the backend.
 */
export function isAuthenticated(): boolean {
  // Check if we have user info (set after successful login)
  return !!localStorage.getItem('user_email');
}

/**
 * Get stored user info
 *
 * Note: This returns user info stored in localStorage for UI purposes.
 * The actual authentication is verified by the backend via HTTP-only cookies.
 * Tokens are NOT stored in localStorage - only user display info.
 */
export function getStoredUserInfo() {
  return {
    email: localStorage.getItem('user_email'),
    id: localStorage.getItem('user_id'),
    name: localStorage.getItem('user_name'),
    role: localStorage.getItem('user_role'),
  };
}
