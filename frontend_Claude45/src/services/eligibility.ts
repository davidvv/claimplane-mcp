/**
 * Eligibility-related API service functions
 */

import apiClient from './api';
import type {
  EligibilityRequest,
  EligibilityResponse,
  ApiResponse,
} from '@/types/api';

/**
 * Check compensation eligibility
 * POST /eligibility/check
 */
export const checkEligibility = async (
  request: EligibilityRequest
): Promise<EligibilityResponse> => {
  const response = await apiClient.post<ApiResponse<EligibilityResponse>>(
    '/eligibility/check',
    request
  );

  if (!response.data.data) {
    throw new Error('Eligibility data not found');
  }

  return response.data.data;
};
