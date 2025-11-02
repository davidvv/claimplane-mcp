/**
 * Auto-generated TypeScript types from OpenAPI 3.0.3 specification
 * EasyAirClaim API v1.0.0
 */

// ========== Base Types ==========

export type FlightStatus = 'scheduled' | 'delayed' | 'cancelled' | 'diverted' | 'boarding' | 'departed' | 'arrived';
export type IncidentType = 'delay' | 'cancellation' | 'denied_boarding' | 'baggage_delay';
export type ClaimStatus = 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'paid' | 'closed';
export type DocumentType = 'boarding_pass' | 'id_document' | 'receipt' | 'bank_statement' | 'other';
export type Region = 'EU' | 'US' | 'CA';
export type Regulation = 'EU261' | 'DOT' | 'CTA';

// ========== Address Schema ==========

export interface Address {
  street?: string;
  city?: string;
  postalCode?: string;
  country?: string;
}

// ========== Flight Schemas ==========

export interface FlightInfo {
  flightNumber: string;
  airline: string;
  departureDate: string; // ISO date format
  departureAirport: string; // IATA code
  arrivalAirport: string; // IATA code
  scheduledDeparture?: string; // ISO datetime
  scheduledArrival?: string; // ISO datetime
  actualDeparture?: string | null; // ISO datetime
  actualArrival?: string | null; // ISO datetime
  status?: FlightStatus;
  delayMinutes?: number | null;
}

export interface FlightStatusResponse extends FlightInfo {
  id: string; // UUID
  lastUpdated: string; // ISO datetime
  dataSource?: string;
}

// ========== Customer Schemas ==========

export interface Customer {
  id?: string; // UUID (readonly)
  email: string;
  firstName: string;
  lastName: string;
  phone?: string | null;
  address?: Address;
  createdAt?: string; // ISO datetime (readonly)
  updatedAt?: string; // ISO datetime (readonly)
}

export interface CustomerUpdate {
  email?: string;
  firstName?: string;
  lastName?: string;
  phone?: string | null;
  address?: Address;
}

// ========== Eligibility Schemas ==========

export interface EligibilityRequest {
  flightInfo: FlightInfo;
  customerInfo: {
    email: string;
    region: Region;
  };
}

export interface EligibilityResponse {
  eligible: boolean;
  compensationAmount?: number | null;
  currency?: string;
  regulation?: Regulation;
  reasons?: string[];
  requirements?: string[];
}

// ========== Document Schemas ==========

export interface Document {
  id: string; // UUID (readonly)
  filename: string;
  contentType: string;
  size: number; // bytes
  documentType: DocumentType;
  uploadedAt: string; // ISO datetime (readonly)
  url?: string; // Temporary secure URL (readonly)
}

// ========== Claim Schemas ==========

export interface Claim {
  id: string; // UUID (readonly)
  customerId: string; // UUID
  flightInfo: FlightStatusResponse;
  incidentType: IncidentType;
  status: ClaimStatus; // readonly
  compensationAmount?: number | null;
  currency?: string;
  documents?: Document[];
  submittedAt?: string; // ISO datetime (readonly)
  updatedAt?: string; // ISO datetime (readonly)
  notes?: string | null;
}

export interface ClaimRequest {
  customerInfo: Customer;
  flightInfo: FlightInfo;
  incidentType: IncidentType;
  notes?: string | null;
}

export interface ClaimUpdate {
  status?: ClaimStatus;
  notes?: string;
}

export interface ClaimPartialUpdate {
  customerId?: string;
  flightInfo?: FlightInfo;
  incidentType?: IncidentType;
  notes?: string | null;
}

// ========== API Response Wrappers ==========

export interface ApiResponse<T = unknown> {
  success: boolean;
  message?: string;
  timestamp: string; // ISO datetime
  data?: T;
}

export interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: string[];
  };
  timestamp: string; // ISO datetime
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  hasNext: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

// ========== Health Check ==========

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

// ========== Query Parameters ==========

export interface FlightStatusParams {
  date: string; // YYYY-MM-DD
  refresh?: boolean;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
}

export interface CustomerListParams extends PaginationParams {
  email?: string;
}

export interface ClaimListParams extends PaginationParams {
  status?: ClaimStatus;
  customerId?: string;
}

// ========== Form Data Types ==========

export interface DocumentUploadForm {
  file: File;
  documentType: DocumentType;
}

// ========== Utility Types ==========

export type ApiError = ErrorResponse;

export type UnwrapApiResponse<T> = T extends ApiResponse<infer U> ? U : never;
