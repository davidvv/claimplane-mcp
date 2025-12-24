/**
 * Eligibility-related API service functions
 */

import apiClient from './api';
import type {
  EligibilityRequest,
  EligibilityResponse,
} from '@/types/api';

/**
 * Check compensation eligibility
 * POST /eligibility/check
 */
export const checkEligibility = async (
  request: EligibilityRequest
): Promise<EligibilityResponse> => {
  // Transform frontend format to backend format
  const backendRequest = {
    departure_airport: request.flightInfo.departureAirport,
    arrival_airport: request.flightInfo.arrivalAirport,
    delay_hours: request.flightInfo.delayMinutes ? request.flightInfo.delayMinutes / 60 : null,
    incident_type: request.flightInfo.status === 'cancelled' ? 'cancellation' : 'delay',
  };

  const response = await apiClient.post<any>(
    '/eligibility/check',
    backendRequest
  );

  // Transform backend response to frontend format
  const backendResult = response.data;
  const result: EligibilityResponse = {
    eligible: backendResult.eligible,
    compensationAmount: parseFloat(backendResult.amount),
    currency: 'EUR',
    regulation: 'EU261',
    reasons: [backendResult.reason],
    requirements: backendResult.requires_manual_review ? ['Manual review required'] : [],
  };

  return result;
};
