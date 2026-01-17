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
  const delayMinutes = request.flightInfo.delay ?? request.flightInfo.delayMinutes ?? null;

  // Check for cancellation (handle both American and British spelling)
  const status = request.flightInfo.status?.toLowerCase() || '';
  const isCancelled = status === 'cancelled' || status === 'canceled';

  const backendRequest = {
    departure_airport: request.flightInfo.departureAirport,
    arrival_airport: request.flightInfo.arrivalAirport,
    delay_hours: delayMinutes !== null ? delayMinutes / 60 : null,
    incident_type: isCancelled ? 'cancellation' : 'delay',
    distance_km: request.flightInfo.distanceKm ?? null,  // Pass distance from API
    flights: request.flightInfo.flights?.map(f => ({
      departure_airport: f.departureAirport || '',
      arrival_airport: f.arrivalAirport || '',
      flight_number: f.flightNumber || undefined
    })).filter(f => f.departure_airport && f.arrival_airport),
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
