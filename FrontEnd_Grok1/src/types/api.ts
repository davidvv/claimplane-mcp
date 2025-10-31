// Generated types from OpenAPI 3.0.3 specification

export interface FlightInfo {
  flightNumber: string;
  airline: string;
  departureDate: string;
  departureAirport: string;
  arrivalAirport: string;
  scheduledDeparture?: string;
  scheduledArrival?: string;
  actualDeparture?: string | null;
  actualArrival?: string | null;
  status: 'scheduled' | 'delayed' | 'cancelled' | 'diverted' | 'boarding' | 'departed' | 'arrived';
  delayMinutes?: number | null;
}

export interface FlightStatus extends FlightInfo {
  id: string;
  lastUpdated: string;
  dataSource: string;
}

export interface Customer {
  id?: string;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string | null;
  address?: Address;
  createdAt?: string;
  updatedAt?: string;
}

export interface Address {
  street?: string;
  city?: string;
  postalCode?: string;
  country?: string;
}

export interface EligibilityRequest {
  flightInfo: FlightInfo;
  customerInfo: {
    email: string;
    region: 'EU' | 'US' | 'CA';
  };
}

export interface EligibilityResponse {
  eligible: boolean;
  compensationAmount?: number | null;
  currency?: string;
  regulation?: 'EU261' | 'DOT' | 'CTA';
  reasons?: string[];
  requirements?: string[];
}

export interface Claim {
  id?: string;
  customerId: string;
  flightInfo: FlightStatus;
  incidentType: 'delay' | 'cancellation' | 'denied_boarding' | 'baggage_delay';
  status?: 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'paid' | 'closed';
  compensationAmount?: number | null;
  currency?: string;
  documents?: Document[];
  submittedAt?: string;
  updatedAt?: string;
  notes?: string | null;
}

export interface ClaimRequest {
  customerInfo: Customer;
  flightInfo: FlightInfo;
  incidentType: 'delay' | 'cancellation' | 'denied_boarding' | 'baggage_delay';
  notes?: string | null;
}

export interface Document {
  id?: string;
  filename: string;
  contentType: string;
  size: number;
  documentType: 'boarding_pass' | 'id_document' | 'receipt' | 'bank_statement' | 'other';
  uploadedAt?: string;
  url?: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  timestamp: string;
  data?: T;
}

export interface ErrorResponse {
  success: boolean;
  error: {
    code: string;
    message: string;
    details?: string[];
  };
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    hasNext: boolean;
  };
}