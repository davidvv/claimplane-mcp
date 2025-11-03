// Generated from OpenAPI 3.0.3 specification
// EasyAirClaim API Types

// Flight-related types
export interface FlightInfo {
  flightNumber: string;
  airline: string;
  departureDate: string;
  departureAirport: string;
  arrivalAirport: string;
  scheduledDeparture: string;
  scheduledArrival: string;
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

// Customer-related types
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

// Eligibility types
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

// Claim types
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

// Document types
export interface Document {
  id?: string;
  filename: string;
  contentType: string;
  size: number;
  documentType: 'boarding_pass' | 'id_document' | 'receipt' | 'bank_statement' | 'other';
  uploadedAt?: string;
  url?: string;
}

// Response types
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  timestamp: string;
  data?: T;
}

export interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: string[];
  };
  timestamp: string;
}

export interface PaginatedResponse<T = any> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    hasNext: boolean;
  };
}

// API endpoint parameter types
export interface FlightStatusParams {
  flightNumber: string;
  date: string;
  refresh?: boolean;
}

export interface ClaimStatusParams {
  claimId: string;
}

export interface DocumentUploadParams {
  claimId: string;
}

export interface DocumentDownloadParams {
  documentId: string;
}

// Query parameters
export interface ListCustomersQuery {
  page?: number;
  limit?: number;
  email?: string;
}

export interface ListClaimsQuery {
  page?: number;
  limit?: number;
  status?: 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'paid' | 'closed';
  customerId?: string;
}

// Form data types
export interface DocumentUploadFormData {
  file: File;
  documentType: 'boarding_pass' | 'id_document' | 'receipt' | 'bank_statement' | 'other';
}

// JWT token type
export interface JWTPayload {
  sub: string;
  email: string;
  exp: number;
  iat: number;
}

// Theme types
export type Theme = 'light' | 'dark' | 'system';

// Form progress types
export interface FormProgress {
  currentStep: number;
  data: {
    flightInfo?: FlightInfo;
    eligibility?: EligibilityResponse;
    customerInfo?: Customer;
    documents?: Document[];
  };
  completedSteps: number[];
}