import { get, post, put, patch, del } from './api';
import { Claim, ClaimRequest, PaginatedResponse, ListClaimsQuery } from '../types/openapi';

/**
 * List claims with pagination
 * @param query - Query parameters for filtering and pagination
 * @returns Paginated list of claims
 */
export async function listClaims(query?: ListClaimsQuery): Promise<PaginatedResponse<Claim>> {
  const params = new URLSearchParams();
  
  if (query?.page) params.append('page', query.page.toString());
  if (query?.limit) params.append('limit', query.limit.toString());
  if (query?.status) params.append('status', query.status);
  if (query?.customerId) params.append('customerId', query.customerId);
  
  const queryString = params.toString();
  const url = `/claims${queryString ? `?${queryString}` : ''}`;
  
  return get<PaginatedResponse<Claim>>(url);
}

/**
 * Get claim details by ID
 * @param claimId - Claim ID
 * @returns Claim details
 */
export async function getClaim(claimId: string): Promise<Claim> {
  return get<Claim>(`/claims/${claimId}`);
}

/**
 * Submit new claim
 * @param claimRequest - Claim request data
 * @returns Created claim
 */
export async function submitClaim(claimRequest: ClaimRequest): Promise<Claim> {
  return post<Claim>('/claims', claimRequest);
}

/**
 * Update claim (full update)
 * @param claimId - Claim ID
 * @param claim - Updated claim data
 * @returns Updated claim
 */
export async function updateClaim(claimId: string, claim: Claim): Promise<Claim> {
  return put<Claim>(`/claims/${claimId}`, claim);
}

/**
 * Partially update claim
 * @param claimId - Claim ID
 * @param updates - Partial claim updates
 * @returns Updated claim
 */
export async function patchClaim(claimId: string, updates: Partial<Claim>): Promise<Claim> {
  return patch<Claim>(`/claims/${claimId}`, updates);
}

/**
 * Delete claim
 * @param claimId - Claim ID
 */
export async function deleteClaim(claimId: string): Promise<void> {
  return del<void>(`/claims/${claimId}`);
}

/**
 * Get mock claim data (for development)
 * @param claimId - Claim ID
 * @returns Mock claim data
 */
export function getMockClaim(claimId: string): Claim {
  const now = new Date().toISOString();
  
  return {
    id: claimId,
    customerId: '456e7890-e89b-12d3-a456-426614174001',
    flightInfo: {
      id: '123e4567-e89b-12d3-a456-426614174000',
      flightNumber: 'LH1234',
      airline: 'Lufthansa',
      departureDate: '2025-06-15',
      departureAirport: 'FRA',
      arrivalAirport: 'JFK',
      scheduledDeparture: '2025-06-15T14:30:00Z',
      scheduledArrival: '2025-06-15T18:45:00Z',
      actualDeparture: '2025-06-15T16:15:00Z',
      actualArrival: '2025-06-15T20:30:00Z',
      status: 'delayed',
      delayMinutes: 105,
      lastUpdated: now,
      dataSource: 'FlightAware',
    },
    incidentType: 'delay',
    status: 'under_review',
    compensationAmount: 600,
    currency: 'EUR',
    documents: [
      {
        id: 'doc1',
        filename: 'boarding_pass.pdf',
        contentType: 'application/pdf',
        size: 2048576,
        documentType: 'boarding_pass',
        uploadedAt: now,
        url: 'https://example.com/documents/boarding_pass.pdf',
      },
      {
        id: 'doc2',
        filename: 'passport.jpg',
        contentType: 'image/jpeg',
        size: 1024000,
        documentType: 'id_document',
        uploadedAt: now,
        url: 'https://example.com/documents/passport.jpg',
      },
    ],
    submittedAt: now,
    updatedAt: now,
    notes: 'Flight delayed by 3 hours due to technical issues',
  };
}

/**
 * Get mock paginated claims (for development)
 * @param page - Page number
 * @param limit - Items per page
 * @returns Mock paginated claims
 */
export function getMockClaims(page: number = 1, limit: number = 20): PaginatedResponse<Claim> {
  const total = 45;
  const totalPages = Math.ceil(total / limit);
  const hasNext = page < totalPages;
  
  const claims: Claim[] = Array.from({ length: Math.min(limit, total - (page - 1) * limit) }, (_, i) => {
    const index = (page - 1) * limit + i;
    return {
      id: `claim-${index}`,
      customerId: `customer-${index}`,
      flightInfo: {
        id: `flight-${index}`,
        flightNumber: `LH${1000 + index}`,
        airline: 'Lufthansa',
        departureDate: '2025-06-15',
        departureAirport: 'FRA',
        arrivalAirport: 'JFK',
        scheduledDeparture: '2025-06-15T14:30:00Z',
        scheduledArrival: '2025-06-15T18:45:00Z',
        actualDeparture: '2025-06-15T16:15:00Z',
        actualArrival: '2025-06-15T20:30:00Z',
        status: 'delayed',
        delayMinutes: 105,
        lastUpdated: new Date().toISOString(),
        dataSource: 'FlightAware',
      },
      incidentType: 'delay',
      status: index % 5 === 0 ? 'approved' : index % 4 === 0 ? 'rejected' : index % 3 === 0 ? 'paid' : 'under_review',
      compensationAmount: index % 5 === 0 ? 600 : null,
      currency: 'EUR',
      documents: [],
      submittedAt: new Date(Date.now() - index * 24 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - index * 24 * 60 * 60 * 1000).toISOString(),
      notes: `Claim ${index} notes`,
    };
  });
  
  return {
    data: claims,
    pagination: {
      page,
      limit,
      total,
      hasNext,
    },
  };
}

/**
 * Get claim status display information
 * @param status - Claim status
 * @returns Status display information
 */
export function getClaimStatusInfo(status: Claim['status']) {
  const statusInfo = {
    draft: { label: 'Draft', color: 'gray', icon: '📝' },
    submitted: { label: 'Submitted', color: 'blue', icon: '📤' },
    under_review: { label: 'Under Review', color: 'yellow', icon: '🔍' },
    approved: { label: 'Approved', color: 'green', icon: '✅' },
    rejected: { label: 'Rejected', color: 'red', icon: '❌' },
    paid: { label: 'Paid', color: 'green', icon: '💰' },
    closed: { label: 'Closed', color: 'gray', icon: '🔒' },
  };
  
  return statusInfo[status || 'draft'];
}

/**
 * Get claim timeline steps
 * @param claim - Claim data
 * @returns Timeline steps
 */
export function getClaimTimeline(claim: Claim) {
  const steps = [
    {
      id: 'submitted',
      label: 'Claim Submitted',
      description: 'Your claim has been received',
      date: claim.submittedAt,
      completed: true,
      current: claim.status === 'submitted',
    },
    {
      id: 'under_review',
      label: 'Under Review',
      description: 'We are reviewing your claim',
      date: claim.status === 'under_review' ? claim.updatedAt : null,
      completed: ['approved', 'rejected', 'paid', 'closed'].includes(claim.status || ''),
      current: claim.status === 'under_review',
    },
    {
      id: 'approved',
      label: 'Claim Approved',
      description: 'Your claim has been approved',
      date: claim.status === 'approved' || claim.status === 'paid' ? claim.updatedAt : null,
      completed: ['approved', 'paid', 'closed'].includes(claim.status || ''),
      current: claim.status === 'approved',
    },
    {
      id: 'paid',
      label: 'Compensation Paid',
      description: 'Payment has been processed',
      date: claim.status === 'paid' ? claim.updatedAt : null,
      completed: claim.status === 'paid' || claim.status === 'closed',
      current: claim.status === 'paid',
    },
  ];
  
  return steps;
}