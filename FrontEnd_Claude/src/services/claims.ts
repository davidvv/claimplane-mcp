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
   * Submit new claim
   */
  async createClaim(claimRequest: ClaimRequest): Promise<Claim> {
    const response = await api.post<ApiResponse<Claim>>('/claims', claimRequest);

    const claim = unwrapApiResponse(response.data);

    trackEvent('claim_submitted', {
      claimId: claim.id,
      incidentType: claim.incidentType,
      compensationAmount: claim.compensationAmount,
    });

    return claim;
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
