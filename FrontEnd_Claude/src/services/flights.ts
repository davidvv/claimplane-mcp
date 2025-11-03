/**
 * Flight service - API calls for flight operations
 */
import api, { unwrapApiResponse, trackEvent } from './api';
import type {
  FlightStatusResponse,
  FlightStatusParams,
  ApiResponse,
} from '@/types/openapi';

export const flightService = {
  /**
   * Get flight status and details
   */
  async getFlightStatus(
    flightNumber: string,
    params: FlightStatusParams
  ): Promise<FlightStatusResponse> {
    const response = await api.get<ApiResponse<FlightStatusResponse>>(
      `/flights/status/${flightNumber}`,
      { params }
    );

    trackEvent('flight_status_checked', {
      flightNumber,
      date: params.date,
    });

    return unwrapApiResponse(response.data);
  },
};
