import { get } from './api';
import { FlightStatus, FlightStatusParams } from '../types/openapi';

/**
 * Get flight status and details
 * @param params - Flight number, date, and optional refresh parameter
 * @returns Flight status information
 */
export async function getFlightStatus(params: FlightStatusParams): Promise<FlightStatus> {
  const { flightNumber, date, refresh } = params;
  const queryParams = new URLSearchParams({
    date,
    ...(refresh && { refresh: refresh.toString() }),
  });
  
  return get<FlightStatus>(`/flights/status/${flightNumber}?${queryParams.toString()}`);
}

/**
 * Get flight status with mock data (for development)
 * @param params - Flight number and date
 * @returns Mock flight status
 */
export function getMockFlightStatus(params: FlightStatusParams): FlightStatus {
  const { flightNumber, date } = params;
  
  return {
    id: '123e4567-e89b-12d3-a456-426614174000',
    flightNumber,
    airline: getAirlineName(flightNumber.substring(0, 2)),
    departureDate: date,
    departureAirport: 'FRA',
    arrivalAirport: 'JFK',
    scheduledDeparture: `${date}T14:30:00Z`,
    scheduledArrival: `${date}T18:45:00Z`,
    actualDeparture: `${date}T16:15:00Z`,
    actualArrival: `${date}T20:30:00Z`,
    status: 'delayed',
    delayMinutes: 105,
    lastUpdated: new Date().toISOString(),
    dataSource: 'FlightAware',
  };
}

/**
 * Get airline name from IATA code
 * @param iataCode - 2-letter IATA code
 * @returns Airline name
 */
function getAirlineName(iataCode: string): string {
  const airlines: Record<string, string> = {
    'LH': 'Lufthansa',
    'BA': 'British Airways',
    'AF': 'Air France',
    'KL': 'KLM',
    'IB': 'Iberia',
    'AY': 'Finnair',
    'SK': 'SAS',
    'LX': 'Swiss',
    'OS': 'Austrian Airlines',
    'TP': 'TAP Air Portugal',
    'AZ': 'ITA Airways',
    'UA': 'United Airlines',
    'AA': 'American Airlines',
    'DL': 'Delta Air Lines',
    'AC': 'Air Canada',
    'VS': 'Virgin Atlantic',
    'DY': 'Norwegian',
    'U2': 'easyJet',
    'FR': 'Ryanair',
    'EW': 'Eurowings',
  };
  
  return airlines[iataCode.toUpperCase()] || 'Unknown Airline';
}

/**
 * Validate flight number format
 * @param flightNumber - Flight number to validate
 * @returns Whether the flight number is valid
 */
export function isValidFlightNumber(flightNumber: string): boolean {
  return /^[A-Z]{2}\d{1,4}$/.test(flightNumber.toUpperCase());
}

/**
 * Format flight number (ensure uppercase)
 * @param flightNumber - Flight number to format
 * @returns Formatted flight number
 */
export function formatFlightNumber(flightNumber: string): string {
  return flightNumber.toUpperCase().trim();
}