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
 * Submit new claim (auto-registers user if not authenticated)
 * POST /claims
 */
export const submitClaim = async (request: ClaimRequest): Promise<Claim> => {
  try {
    // First try authenticated submission
    const response = await apiClient.post<ApiResponse<Claim>>('/claims', request);

    if (!response.data.data) {
      throw new Error('Failed to submit claim');
    }

    return response.data.data;
  } catch (error: any) {
    // If 401/403 (not authenticated), auto-register and retry
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.log('Not authenticated, attempting auto-registration...');

      // Auto-register with minimal info - use simple password for now
      const { register } = await import('./auth');
      const simplePassword = 'TempPass123!'; // Simple temporary password (will be reset via email)

      try {
        await register({
          email: request.customerInfo.email,
          password: simplePassword,
          first_name: request.customerInfo.firstName,
          last_name: request.customerInfo.lastName,
          phone: request.customerInfo.phone || undefined,
        });

        // Retry claim submission now that user is authenticated
        const response = await apiClient.post<ApiResponse<Claim>>('/claims', request);

        if (!response.data.data) {
          throw new Error('Failed to submit claim after registration');
        }

        // TODO: Send magic link/password reset email automatically
        console.log('User auto-registered. Password reset email should be sent.');

        return response.data.data;
      } catch (registerError: any) {
        // If registration fails (e.g., email already exists), show helpful message
        if (registerError.response?.status === 400) {
          throw new Error('An account with this email already exists. Please login first.');
        }
        throw registerError;
      }
    }
    throw error;
  }
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
