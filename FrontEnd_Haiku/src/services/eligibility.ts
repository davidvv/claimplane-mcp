import { post } from './api';
import { EligibilityRequest, EligibilityResponse } from '../types/openapi';

/**
 * Check compensation eligibility
 * @param request - Eligibility check request with flight and customer info
 * @returns Eligibility response
 */
export async function checkEligibility(request: EligibilityRequest): Promise<EligibilityResponse> {
  return post<EligibilityResponse>('/eligibility/check', request);
}

/**
 * Get mock eligibility response (for development)
 * @param request - Eligibility request
 * @returns Mock eligibility response
 */
export function getMockEligibilityResponse(request: EligibilityRequest): EligibilityResponse {
  const { flightInfo } = request;
  
  // Determine eligibility based on flight delay and region
  const isEligible = flightInfo.delayMinutes && flightInfo.delayMinutes >= 180; // 3+ hours delay
  const region = request.customerInfo.region;
  
  let compensationAmount: number | null = null;
  let regulation: 'EU261' | 'DOT' | 'CTA' = 'EU261';
  let currency = 'EUR';
  
  if (isEligible) {
    switch (region) {
      case 'EU':
        compensationAmount = 600;
        regulation = 'EU261';
        currency = 'EUR';
        break;
      case 'US':
        compensationAmount = 1350;
        regulation = 'DOT';
        currency = 'USD';
        break;
      case 'CA':
        compensationAmount = 1000;
        regulation = 'CTA';
        currency = 'CAD';
        break;
    }
  }
  
  return {
    eligible: isEligible,
    compensationAmount,
    currency,
    regulation,
    reasons: isEligible ? [
      `Flight delayed by ${flightInfo.delayMinutes} minutes`,
      `Departure within ${region} jurisdiction`,
      'Delay within airline control'
    ] : [
      'Flight delay less than 3 hours',
      'Delay due to extraordinary circumstances'
    ],
    requirements: isEligible ? [
      'Boarding pass copy',
      'Valid ID or passport',
      'Proof of booking'
    ] : [],
  };
}

/**
 * Calculate potential compensation amount
 * @param delayMinutes - Flight delay in minutes
 * @param region - Passenger region (EU, US, CA)
 * @param distance - Flight distance in km (optional)
 * @returns Compensation amount and currency
 */
export function calculateCompensation(
  delayMinutes: number,
  region: 'EU' | 'US' | 'CA',
  distance?: number
): { amount: number; currency: string } {
  if (delayMinutes < 180) {
    return { amount: 0, currency: 'EUR' };
  }
  
  switch (region) {
    case 'EU':
      // EU261 compensation based on distance and delay
      if (distance) {
        if (distance <= 1500) {
          return { amount: 250, currency: 'EUR' };
        } else if (distance <= 3500) {
          return { amount: 400, currency: 'EUR' };
        } else {
          return { amount: 600, currency: 'EUR' };
        }
      }
      return { amount: 600, currency: 'EUR' };
      
    case 'US':
      // DOT compensation for tarmac delays
      return { amount: 1350, currency: 'USD' };
      
    case 'CA':
      // CTA compensation
      return { amount: 1000, currency: 'CAD' };
      
    default:
      return { amount: 0, currency: 'EUR' };
  }
}

/**
 * Get eligibility requirements based on region
 * @param region - Passenger region
 * @returns List of required documents
 */
export function getEligibilityRequirements(region: 'EU' | 'US' | 'CA'): string[] {
  const baseRequirements = [
    'Boarding pass copy',
    'Valid ID or passport',
    'Proof of booking'
  ];
  
  switch (region) {
    case 'EU':
      return [
        ...baseRequirements,
        'EU261 claim form (if applicable)',
        'Receipts for additional expenses'
      ];
    case 'US':
      return [
        ...baseRequirements,
        'DOT complaint form (if applicable)',
        'Proof of damages'
      ];
    case 'CA':
      return [
        ...baseRequirements,
        'CTA complaint form (if applicable)',
        'Proof of Canadian residency'
      ];
    default:
      return baseRequirements;
  }
}

/**
 * Check if delay qualifies for compensation
 * @param delayMinutes - Flight delay in minutes
 * @param region - Passenger region
 * @returns Whether delay qualifies for compensation
 */
export function qualifiesForCompensation(delayMinutes: number, region: 'EU' | 'US' | 'CA'): boolean {
  switch (region) {
    case 'EU':
      return delayMinutes >= 180; // 3+ hours for EU261
    case 'US':
      return delayMinutes >= 120; // 2+ hours for DOT
    case 'CA':
      return delayMinutes >= 180; // 3+ hours for CTA
    default:
      return false;
  }
}