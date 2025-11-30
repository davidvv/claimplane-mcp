/**
 * Authentication service - integrates with Phase 3 JWT backend
 */
import apiClient from './api';
import { storeAuthTokens, storeAccessTokenOnly, clearAuthTokens } from '@/utils/tokenStorage';

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

  // Store tokens safely (clears old tokens first)
  if (response.data.tokens) {
    storeAuthTokens(
      response.data.tokens.access_token,
      response.data.tokens.refresh_token,
      response.data.user.email,
      response.data.user.id,
      `${response.data.user.first_name} ${response.data.user.last_name}`
    );
  }

  return response.data;
}

/**
 * Login with email and password
 */
export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/login', data);

  // Store tokens safely (clears old tokens first)
  if (response.data.tokens) {
    storeAuthTokens(
      response.data.tokens.access_token,
      response.data.tokens.refresh_token,
      response.data.user.email,
      response.data.user.id,
      `${response.data.user.first_name} ${response.data.user.last_name}`
    );
  }

  return response.data;
}

/**
 * Logout - revoke refresh token
 */
export async function logout(): Promise<void> {
  const refreshToken = localStorage.getItem('refresh_token');

  if (refreshToken) {
    try {
      await apiClient.post('/auth/logout', { refresh_token: refreshToken });
    } catch (error) {
      // Continue with local logout even if API call fails
      console.error('Logout API call failed:', error);
    }
  }

  // Clear all auth data safely
  clearAuthTokens();
}

/**
 * Get current user profile
 */
export async function getCurrentUser(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>('/auth/me');
  return response.data;
}

/**
 * Refresh access token using refresh token
 */
export async function refreshAccessToken(): Promise<{ access_token: string; refresh_token: string }> {
  const refreshToken = localStorage.getItem('refresh_token');

  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await apiClient.post<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  }>('/auth/refresh', { refresh_token: refreshToken });

  // Update stored tokens safely (clears old tokens first)
  const userEmail = localStorage.getItem('user_email') || '';
  const userId = localStorage.getItem('user_id') || '';
  const userName = localStorage.getItem('user_name') || '';

  storeAuthTokens(
    response.data.access_token,
    response.data.refresh_token,
    userEmail,
    userId,
    userName
  );

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
 */
export function isAuthenticated(): boolean {
  return !!localStorage.getItem('auth_token');
}

/**
 * Get stored user info (from localStorage)
 */
export function getStoredUserInfo() {
  return {
    email: localStorage.getItem('user_email'),
    id: localStorage.getItem('user_id'),
    name: localStorage.getItem('user_name'),
  };
}
