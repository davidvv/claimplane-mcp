/**
 * Claim-related API service functions
 */

import apiClient from './api';
import type {
  Claim,
  ClaimRequest,
  ClaimListParams,
  PaginatedResponse,
  ApiResponse,
} from '@/types/api';

/**
 * List claims with pagination and filters
 * GET /claims
 */
export const listClaims = async (
  params?: ClaimListParams
): Promise<PaginatedResponse<Claim>> => {
  const response = await apiClient.get<PaginatedResponse<Claim>>('/claims', {
    params,
  });

  return response.data;
};

/**
 * Get specific claim details
 * GET /claims/{claimId}
 */
export const getClaim = async (claimId: string): Promise<Claim> => {
  const response = await apiClient.get<Claim>(`/claims/${claimId}`);

  if (!response.data) {
    throw new Error('Claim not found');
  }

  return response.data;
};

/**
 * Submit new claim (passwordless - auto-creates customer and sends magic link)
 * POST /claims/submit
 *
 * Returns claim data and also stores access token for immediate authentication,
 * allowing document uploads without clicking the magic link first.
 */
export const submitClaim = async (request: ClaimRequest): Promise<Claim> => {
  // Use passwordless endpoint - auto-creates customer, sends magic link, and returns access token
  const response = await apiClient.post<{
    claim: Claim;
    accessToken: string;
    tokenType: string;
  }>('/claims/submit', request);

  if (!response.data || !response.data.claim) {
    throw new Error('Failed to submit claim');
  }

  // Store access token for immediate authentication (allows document uploads)
  if (response.data.accessToken) {
    localStorage.setItem('auth_token', response.data.accessToken);
    console.log('[submitClaim] Access token stored for immediate authentication');
  }

  return response.data.claim;
};

/**
 * Update claim status (admin)
 * PUT /claims/{claimId}
 */
export const updateClaim = async (
  claimId: string,
  data: { status: string; notes?: string }
): Promise<Claim> => {
  const response = await apiClient.put<ApiResponse<Claim>>(
    `/claims/${claimId}`,
    data
  );

  if (!response.data.data) {
    throw new Error('Failed to update claim');
  }

  return response.data.data;
};

/**
 * Partially update claim
 * PATCH /claims/{claimId}
 */
export const patchClaim = async (
  claimId: string,
  data: Partial<ClaimRequest>
): Promise<Claim> => {
  const response = await apiClient.patch<ApiResponse<Claim>>(
    `/claims/${claimId}`,
    data
  );

  if (!response.data.data) {
    throw new Error('Failed to update claim');
  }

  return response.data.data;
};
