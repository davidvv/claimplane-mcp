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
  // No need to manually store them in localStorage

  return response.data;
}

/**
 * Login with email and password
 */
export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/login', data);

  // Tokens are automatically stored in HTTP-only cookies by the backend
  // No need to manually store them in localStorage

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
 * Note: With HTTP-only cookies, we can't check authentication from JavaScript.
 * This function returns true optimistically. If the user is not authenticated,
 * API calls will return 401 and the interceptor will redirect to login.
 */
export function isAuthenticated(): boolean {
  // Always return true - let the backend verify authentication
  // 401 errors will trigger redirect to login in the API interceptor
  return true;
}

/**
 * Get stored user info
 *
 * Note: User info is no longer stored in localStorage for security.
 * Use getCurrentUser() to fetch from the backend instead.
 * This function is deprecated and returns null values.
 *
 * @deprecated Use getCurrentUser() instead
 */
export function getStoredUserInfo() {
  return {
    email: null,
    id: null,
    name: null,
  };
}
