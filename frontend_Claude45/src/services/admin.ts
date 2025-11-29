/**
 * Admin service - API calls for admin endpoints
 */
import apiClient from './api';

// ============================================================================
// Types
// ============================================================================

export interface ClaimListItem {
  id: string;
  customer_id: string;
  flight_number: string;
  airline: string;
  departure_airport: string;
  arrival_airport: string;
  scheduled_departure: string;
  actual_departure: string | null;
  scheduled_arrival: string;
  actual_arrival: string | null;
  incident_type: 'delay' | 'cancellation' | 'denied_boarding' | 'missed_connection';
  status: string;
  calculated_compensation: string | null;
  submitted_at: string;
  updated_at: string;
  customer: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    phone: string | null;
  };
  file_count: number;
  note_count: number;
}

export interface PaginatedClaimsResponse {
  claims: ClaimListItem[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface ClaimDetail {
  id: string;
  customer_id: string;
  flight_number: string;
  airline: string;
  departure_airport: string;
  arrival_airport: string;
  scheduled_departure: string;
  actual_departure: string | null;
  scheduled_arrival: string;
  actual_arrival: string | null;
  delay_hours: number | null;
  incident_type: 'delay' | 'cancellation' | 'denied_boarding' | 'missed_connection';
  incident_description: string | null;
  extraordinary_circumstances: boolean;
  status: string;
  rejection_reason: string | null;
  calculated_compensation: string | null;
  submitted_at: string;
  updated_at: string;
  customer: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    phone: string | null;
    street: string | null;
    city: string | null;
    postal_code: string | null;
    country: string | null;
  };
  files: ClaimFile[];
  notes: ClaimNote[];
  status_history: StatusHistory[];
}

export interface ClaimFile {
  id: string;
  claim_id: string;
  document_type: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  status: string;
  validation_status: string | null;
  rejection_reason: string | null;
  uploaded_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

export interface ClaimNote {
  id: string;
  claim_id: string;
  author_id: string;
  note_text: string;
  is_internal: boolean;
  created_at: string;
  author: {
    first_name: string;
    last_name: string;
    email: string;
  };
}

export interface StatusHistory {
  id: string;
  claim_id: string;
  old_status: string;
  new_status: string;
  changed_by: string;
  change_reason: string | null;
  changed_at: string;
  changed_by_user: {
    first_name: string;
    last_name: string;
    email: string;
  };
}

export interface ClaimFilters {
  skip?: number;
  limit?: number;
  status?: string;
  airline?: string;
  incident_type?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface StatusUpdateRequest {
  new_status: string;
  change_reason?: string;
}

export interface AddNoteRequest {
  note_text: string;
  is_internal: boolean;
}

export interface AnalyticsSummary {
  total_claims: number;
  pending_review: number;
  approved: number;
  rejected: number;
  total_compensation: number;
  avg_processing_time_hours: number;
  claims_by_status: Record<string, number>;
  claims_by_airline: Record<string, number>;
  claims_by_incident_type: Record<string, number>;
}

export interface ValidStatusTransitions {
  current_status: string;
  valid_next_statuses: string[];
  status_info: {
    label: string;
    description: string;
    color: string;
  };
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * List all claims with filters and pagination
 */
export async function listClaims(filters: ClaimFilters = {}): Promise<PaginatedClaimsResponse> {
  const params = new URLSearchParams();

  if (filters.skip !== undefined) params.append('skip', filters.skip.toString());
  if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
  if (filters.status) params.append('status', filters.status);
  if (filters.airline) params.append('airline', filters.airline);
  if (filters.incident_type) params.append('incident_type', filters.incident_type);
  if (filters.date_from) params.append('date_from', filters.date_from);
  if (filters.date_to) params.append('date_to', filters.date_to);
  if (filters.search) params.append('search', filters.search);
  if (filters.sort_by) params.append('sort_by', filters.sort_by);
  if (filters.sort_order) params.append('sort_order', filters.sort_order);

  const response = await apiClient.get<PaginatedClaimsResponse>(
    `/admin/claims?${params.toString()}`
  );

  return response.data;
}

/**
 * Get detailed claim information
 */
export async function getClaimDetail(claimId: string): Promise<ClaimDetail> {
  const response = await apiClient.get<ClaimDetail>(`/admin/claims/${claimId}`);
  return response.data;
}

/**
 * Update claim status
 */
export async function updateClaimStatus(
  claimId: string,
  update: StatusUpdateRequest
): Promise<ClaimDetail> {
  const response = await apiClient.put<ClaimDetail>(
    `/admin/claims/${claimId}/status`,
    update
  );
  return response.data;
}

/**
 * Add note to claim
 */
export async function addClaimNote(
  claimId: string,
  note: AddNoteRequest
): Promise<ClaimNote> {
  const response = await apiClient.post<ClaimNote>(
    `/admin/claims/${claimId}/notes`,
    note
  );
  return response.data;
}

/**
 * Get claim notes
 */
export async function getClaimNotes(
  claimId: string,
  includeInternal: boolean = true
): Promise<ClaimNote[]> {
  const response = await apiClient.get<ClaimNote[]>(
    `/admin/claims/${claimId}/notes?include_internal=${includeInternal}`
  );
  return response.data;
}

/**
 * Get claim status history
 */
export async function getClaimStatusHistory(claimId: string): Promise<StatusHistory[]> {
  const response = await apiClient.get<StatusHistory[]>(`/admin/claims/${claimId}/history`);
  return response.data;
}

/**
 * Get valid status transitions for a claim
 */
export async function getValidStatusTransitions(claimId: string): Promise<ValidStatusTransitions> {
  const response = await apiClient.get<ValidStatusTransitions>(
    `/admin/claims/${claimId}/status-transitions`
  );
  return response.data;
}

/**
 * Get analytics summary
 */
export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const response = await apiClient.get<AnalyticsSummary>('/admin/claims/analytics/summary');
  return response.data;
}

/**
 * Download claim file
 */
export async function downloadClaimFile(fileId: string): Promise<Blob> {
  const response = await apiClient.get(`/admin/files/${fileId}/download`, {
    responseType: 'blob',
  });
  return response.data;
}

/**
 * Review/approve file
 */
export async function reviewFile(
  fileId: string,
  approved: boolean,
  rejectionReason?: string
): Promise<ClaimFile> {
  const response = await apiClient.put<ClaimFile>(`/admin/files/${fileId}/review`, {
    approved,
    rejection_reason: rejectionReason,
  });
  return response.data;
}

/**
 * Get pending review files
 */
export async function getPendingReviewFiles(): Promise<ClaimFile[]> {
  const response = await apiClient.get<ClaimFile[]>('/admin/files/pending-review');
  return response.data;
}
