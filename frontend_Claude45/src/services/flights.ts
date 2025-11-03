/**
 * Flight-related API service functions
 */

import apiClient from './api';
import type {
  FlightStatus,
  FlightStatusParams,
  ApiResponse,
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

  if (!response.data.data) {
    throw new Error('Flight data not found');
  }

  return response.data.data;
};
