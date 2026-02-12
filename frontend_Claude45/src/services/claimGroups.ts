/**
 * Claim Groups Service
 * 
 * API calls for multi-passenger claim groups (Phase 5)
 */

import apiClient from './api';

export interface ClaimGroup {
  id: string;
  group_name: string | null;
  flight_number: string;
  flight_date: string;
  total_claims: number;
  total_compensation: number | null;
  status_summary: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export interface ClaimGroupDetail extends ClaimGroup {
  account_holder_id: string;
  consent_confirmed: boolean;
  consent_confirmed_at: string | null;
  claims: Array<{
    id: string;
    status: string;
    compensation_amount: number | null;
    passenger_name: string;
  }>;
}

/**
 * Get all claim groups for the current user
 */
export async function getMyClaimGroups(): Promise<ClaimGroup[]> {
  const response = await apiClient.get('/claim-groups/me');
  if (response.data.success) {
    return response.data.data || [];
  }
  throw new Error(response.data.message || 'Failed to fetch claim groups');
}

/**
 * Get a specific claim group by ID
 */
export async function getClaimGroup(groupId: string): Promise<ClaimGroupDetail> {
  const response = await apiClient.get(`/claim-groups/${groupId}`);
  if (response.data.success) {
    return response.data.data;
  }
  throw new Error(response.data.message || 'Failed to fetch claim group');
}

/**
 * Create a new claim group
 */
export async function createClaimGroup(data: {
  flight_number: string;
  flight_date: string;
  group_name?: string;
}): Promise<ClaimGroup> {
  const response = await apiClient.post('/claim-groups', data);
  if (response.data.success) {
    return response.data.data;
  }
  throw new Error(response.data.message || 'Failed to create claim group');
}

/**
 * Confirm consent for a claim group
 */
export async function confirmGroupConsent(groupId: string): Promise<void> {
  const response = await apiClient.post(`/claim-groups/${groupId}/consent`);
  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to confirm consent');
  }
}
