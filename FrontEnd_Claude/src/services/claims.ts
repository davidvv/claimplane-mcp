/**
 * Claims service - API calls for claim operations
 */
import api, { unwrapApiResponse, trackEvent } from './api';
import type {
  Claim,
  ClaimRequest,
  ClaimUpdate,
  ClaimPartialUpdate,
  ClaimListParams,
  PaginatedResponse,
  ApiResponse,
} from '@/types/openapi';

export const claimService = {
  /**
   * List claims (paginated)
   */
  async listClaims(params?: ClaimListParams): Promise<PaginatedResponse<Claim>> {
    const response = await api.get<PaginatedResponse<Claim>>('/claims', { params });
    return response.data;
  },

  /**
   * Get claim by ID
   */
  async getClaim(claimId: string): Promise<Claim> {
    const response = await api.get<ApiResponse<Claim>>(`/claims/${claimId}`);
    return unwrapApiResponse(response.data);
  },

  /**
   * Submit new claim (auto-registers user if not authenticated)
   */
  async createClaim(claimRequest: ClaimRequest): Promise<Claim> {
    try {
      // First try authenticated submission
      const response = await api.post<ApiResponse<Claim>>('/claims', claimRequest);
      const claim = unwrapApiResponse(response.data);

      trackEvent('claim_submitted', {
        claimId: claim.id,
        incidentType: claim.incidentType,
        compensationAmount: claim.compensationAmount,
      });

      return claim;
    } catch (error: any) {
      // If 401/403 (not authenticated), auto-register and retry
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.log('Not authenticated, attempting auto-registration...');

        // Auto-register with minimal info - use simple password for now
        const { register } = await import('./auth');
        const simplePassword = 'TempPass123!'; // Simple temporary password (will be reset via email)

        try {
          await register({
            email: claimRequest.customerInfo.email,
            password: simplePassword,
            first_name: claimRequest.customerInfo.firstName,
            last_name: claimRequest.customerInfo.lastName,
            phone: claimRequest.customerInfo.phone || undefined,
          });

          // Retry claim submission now that user is authenticated
          const response = await api.post<ApiResponse<Claim>>('/claims', claimRequest);
          const claim = unwrapApiResponse(response.data);

          trackEvent('claim_submitted_with_autoregister', {
            claimId: claim.id,
            incidentType: claim.incidentType,
            compensationAmount: claim.compensationAmount,
          });

          // TODO: Send magic link/password reset email automatically
          console.log('User auto-registered. Password reset email should be sent.');

          return claim;
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
  },

  /**
   * Update claim status (admin only)
   */
  async updateClaim(claimId: string, update: ClaimUpdate): Promise<Claim> {
    const response = await api.put<ApiResponse<Claim>>(`/claims/${claimId}`, update);
    return unwrapApiResponse(response.data);
  },

  /**
   * Partially update claim
   */
  async patchClaim(claimId: string, updates: ClaimPartialUpdate): Promise<Claim> {
    const response = await api.patch<ApiResponse<Claim>>(`/claims/${claimId}`, updates);
    return unwrapApiResponse(response.data);
  },
};
