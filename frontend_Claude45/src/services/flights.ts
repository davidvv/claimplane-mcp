/**
 * Flight-related API service functions
 */

import apiClient from './api';
import type {
  FlightStatus,
  FlightStatusParams,
  ApiResponse,
  AirportSearchParams,
  AirportSearchResponse,
  RouteSearchParams,
  RouteSearchResponse,
} from '@/types/api';

/**
 * Get flight status and details
 * GET /flights/status/{flightNumber}
 */
export const getFlightStatus = async (
  params: FlightStatusParams
): Promise<FlightStatus> => {
  const { flightNumber, date, refresh = false } = params;

  const response = await apiClient.get<ApiResponse<FlightStatus>>(
    `/flights/status/${flightNumber}`,
    {
      params: { date, refresh },
    }
  );

  // Handle case where flight data is unavailable but claim can still proceed
  if (!response.data.data) {
    if (response.data.canProceedWithClaim) {
      // Return a minimal FlightStatus with manual review flag
      return {
        flightNumber: flightNumber.toUpperCase(),
        airline: '',
        departureDate: date,
        departureAirport: '',
        arrivalAirport: '',
        id: '',
        lastUpdated: new Date().toISOString(),
        dataSource: 'manual',
        requiresManualVerification: true,
      } as FlightStatus;
    }
    throw new Error(response.data.userMessage || 'Flight data not found');
  }

  return response.data.data;
};

/**
 * Search airports by IATA code, name, or city
 * Phase 6.5: Airport autocomplete for route search
 * GET /flights/airports/search
 */
export const searchAirports = async (
  params: AirportSearchParams
): Promise<AirportSearchResponse> => {
  const { query, limit = 10 } = params;

  const response = await apiClient.get<AirportSearchResponse>(
    '/flights/airports/search',
    {
      params: { query, limit },
    }
  );

  return response.data;
};

/**
 * Search for flights on a specific route and date
 * Phase 6.5: Route-based flight search
 * GET /flights/search
 */
export const searchFlightsByRoute = async (
  params: RouteSearchParams
): Promise<RouteSearchResponse> => {
  const { from, to, date, time, force_refresh = false } = params;

  const response = await apiClient.get<RouteSearchResponse>(
    '/flights/search',
    {
      params: {
        from,
        to,
        date,
        time,
        force_refresh,
      },
    }
  );

  return response.data;
};
