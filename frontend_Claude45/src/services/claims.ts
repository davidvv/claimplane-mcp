/**
 * Claim-related API service functions
 */

import apiClient from './api';
import type {
  Claim,
  ClaimRequest,
  ClaimListParams,
  ApiResponse,
  OCRResponse,
} from '@/types/api';

/**
 * List claims with pagination and filters
 * GET /claims
 */
export const listClaims = async (
  params?: ClaimListParams
): Promise<Claim[]> => {
  // Convert camelCase params to snake_case for backend
  const apiParams: any = { ...params };
  if (params?.includeDrafts !== undefined) {
    apiParams.include_drafts = params.includeDrafts;
    delete apiParams.includeDrafts;
  }

  const response = await apiClient.get<Claim[]>('/claims/', {
    params: apiParams,
  });

  return response.data;
};

/**
 * Delete a claim (only if draft)
 * DELETE /claims/{claimId}
 */
export const deleteClaim = async (claimId: string): Promise<void> => {
  await apiClient.delete(`/claims/${claimId}`);
};

/**
 * Get specific claim details
 * GET /claims/{claimId}
 * 
 * @param claimId - The claim UUID
 * @param includeDetails - If true, include passengers and contact info (for draft resume)
 */
export const getClaim = async (claimId: string, includeDetails: boolean = false): Promise<Claim> => {
  const params = includeDetails ? { include_details: 'true' } : {};
  const response = await apiClient.get<Claim>(`/claims/${claimId}`, { params });

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

  // Set user info in localStorage to consider them authenticated
  // This allows viewing the claim details immediately on the Status page
  const claim = response.data.claim;
  if (claim.contactInfo) {
    sessionStorage.setItem('user_email', claim.contactInfo.email || '');
    sessionStorage.setItem('user_id', claim.customerId);
    
    // Attempt to get name from passengers or contact info
    let displayName = 'User';
    if (claim.passengers && claim.passengers.length > 0) {
      const primaryPax = claim.passengers[0];
      displayName = `${primaryPax.firstName} ${primaryPax.lastName}`;
    }
    sessionStorage.setItem('user_name', displayName);
    sessionStorage.setItem('user_role', 'customer');
  }

  // Access token is automatically stored in HTTP-only cookie by the backend
  // No need to manually store it

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

/**
 * Extract data from boarding pass using OCR
 * POST /claims/ocr-boarding-pass
 */
export const ocrBoardingPass = async (file: File): Promise<OCRResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<OCRResponse>('/claims/ocr-boarding-pass', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  if (!response.data) {
    throw new Error('OCR processing failed');
  }

  return response.data;
};
