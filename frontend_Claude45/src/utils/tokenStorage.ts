/**
 * Token storage utility - handles safe token management
 * 
 * CRITICAL: This utility ensures old tokens are cleared before new ones are stored.
 * This prevents token collision issues when switching between different user accounts.
 * 
 * Without this safeguard, a user could:
 * 1. Submit a claim as customer A (token stored)
 * 2. Log in as superadmin B
 * 3. See claims from customer A instead of superadmin B
 */

/**
 * Safely store authentication tokens by clearing old ones first.
 * This is critical when switching between different user accounts.
 */
export function storeAuthTokens(
  accessToken: string,
  refreshToken: string,
  userEmail: string,
  userId: string,
  userName: string
): void {
  // IMPORTANT: Clear old tokens BEFORE storing new ones
  // This prevents token collision when switching between accounts
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

  console.log('[storeAuthTokens] Tokens safely stored for user:', userEmail);
}

/**
 * Safely store only the access token (for claim submission).
 * Clears old token before storing new one.
 */
export function storeAccessTokenOnly(accessToken: string): void {
  // IMPORTANT: Clear old token BEFORE storing new one
  // This prevents token collision when switching between accounts
  localStorage.removeItem('auth_token');
  localStorage.setItem('auth_token', accessToken);
  console.log('[storeAccessTokenOnly] Access token safely stored');
}

/**
 * Clear all authentication tokens and user data.
 */
export function clearAuthTokens(): void {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_email');
  localStorage.removeItem('user_id');
  localStorage.removeItem('user_name');
  localStorage.removeItem('easyairclaim_form_data');
  console.log('[clearAuthTokens] All authentication tokens cleared');
}
