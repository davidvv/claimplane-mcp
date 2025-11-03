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
  const response = await apiClient.get<ApiResponse<Claim>>(`/claims/${claimId}`);

  if (!response.data.data) {
    throw new Error('Claim not found');
  }

  return response.data.data;
};

/**
 * Submit new claim
 * POST /claims
 */
export const submitClaim = async (request: ClaimRequest): Promise<Claim> => {
  const response = await apiClient.post<ApiResponse<Claim>>('/claims', request);

  if (!response.data.data) {
    throw new Error('Failed to submit claim');
  }

  return response.data.data;
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
