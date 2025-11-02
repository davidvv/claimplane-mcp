/**
 * Eligibility service - API calls for eligibility checking
 */
import api, { unwrapApiResponse, trackEvent } from './api';
import type {
  EligibilityRequest,
  EligibilityResponse,
  ApiResponse,
} from '@/types/openapi';

export const eligibilityService = {
  /**
   * Check compensation eligibility
   */
  async checkEligibility(request: EligibilityRequest): Promise<EligibilityResponse> {
    const response = await api.post<ApiResponse<EligibilityResponse>>(
      '/eligibility/check',
      request
    );

    const result = unwrapApiResponse(response.data);

    trackEvent('eligibility_checked', {
      eligible: result.eligible,
      compensationAmount: result.compensationAmount,
      regulation: result.regulation,
    });

    return result;
  },
};
