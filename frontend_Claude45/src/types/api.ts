/**
 * Auto-generated TypeScript types from OpenAPI 3.0.3 specification
 * ClaimPlane API v1.0.0
 */

// ==================== Flight Types ====================
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
  status?: 'scheduled' | 'delayed' | 'cancelled' | 'diverted' | 'boarding' | 'departed' | 'arrived' | 'Arrived';
  delay?: number | null; // Delay in minutes (negative = early)
  delayMinutes?: number | null; // Legacy field, use delay instead
  distanceKm?: number | null; // Great circle distance in kilometers
  flights?: FlightSegment[]; // List of flight segments for multi-leg journeys
}

export interface FlightStatus extends FlightInfo {
  id: string; // UUID
  lastUpdated: string; // ISO datetime
  dataSource: string;
}

// ==================== Customer Types ====================
export interface Address {
  street?: string;
  city?: string;
  postalCode?: string;
  country?: string;
}

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

export interface CustomerCreateInfo {
  email: string;
  firstName: string;
  lastName: string;
  phone?: string | null;
  address?: Address;
}

// ==================== Eligibility Types ====================
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

// ==================== Document Types ====================
export type DocumentType = 'boarding_pass' | 'id_document' | 'receipt' | 'bank_statement' | 'other';

export interface Document {
  id?: string; // UUID (readonly)
  filename: string;
  originalFilename: string; // Original filename uploaded by user
  contentType: string;
  size: number; // bytes
  documentType: DocumentType;
  uploadedAt?: string; // ISO datetime (readonly)
  url?: string; // Secure download URL (readonly)
}

// ==================== Claim Types ====================
export type IncidentType = 'delay' | 'cancellation' | 'denied_boarding' | 'baggage_delay';
export type ClaimStatus = 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'paid' | 'closed';

export interface Claim {
  id?: string; // UUID (readonly)
  customerId: string; // UUID
  flightInfo: FlightStatus;
  incidentType: IncidentType;
  status?: ClaimStatus; // (readonly)
  compensationAmount?: number | null;
  currency?: string;
  documents?: Document[];
  submittedAt?: string; // ISO datetime (readonly)
  updatedAt?: string; // ISO datetime (readonly)
  notes?: string | null;
}

export interface ClaimRequest {
  customerInfo: CustomerCreateInfo;
  flightInfo: FlightInfo;
  incidentType: IncidentType;
  notes?: string | null;
  bookingReference?: string | null;
  ticketNumber?: string | null;
  termsAccepted: boolean;
  claimId?: string;  // Workflow v2: Draft claim ID to finalize
}

// ==================== API Response Types ====================
export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
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

// ==================== Request/Query Parameter Types ====================
export interface FlightStatusParams {
  flightNumber: string;
  date: string; // YYYY-MM-DD
  refresh?: boolean;
}

// ==================== Phase 6.5: Flight Search by Route Types ====================
export interface Airport {
  iata: string; // 3-letter IATA code
  icao?: string; // 4-letter ICAO code
  name: string; // Airport name
  city: string; // City name
  country: string; // Country name or code
}

export interface AirportSearchParams {
  query: string; // Search query (IATA code, city, or airport name)
  limit?: number; // Max results (default: 10, max: 50)
}

export interface AirportSearchResponse {
  airports: Airport[];
  total: number;
}

export interface FlightSearchResult {
  flightNumber: string;
  airline?: string;
  airlineIata?: string;
  departureAirport: string;
  departureAirportName?: string;
  arrivalAirport: string;
  arrivalAirportName?: string;
  scheduledDeparture?: string; // ISO 8601
  scheduledArrival?: string; // ISO 8601
  actualDeparture?: string; // ISO 8601
  actualArrival?: string; // ISO 8601
  status: string;
  delayMinutes?: number;
  distanceKm?: number;
  estimatedCompensation?: number; // EUR
}

export interface RouteSearchParams {
  from: string; // Departure airport IATA code
  to: string; // Arrival airport IATA code
  date: string; // Flight date (YYYY-MM-DD)
  time?: string; // Optional time filter (morning/afternoon/evening or HH:MM)
  force_refresh?: boolean; // Force API call (bypass cache)
}

export interface RouteSearchResponse {
  flights: FlightSearchResult[];
  total: number;
  cached: boolean;
  apiCreditsUsed: number;
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

export interface DocumentUploadRequest {
  file: File;
  documentType: DocumentType;
}

// ==================== Health Check ====================
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version: string;
}

// ==================== OCR Types ====================
export interface Passenger {
  firstName?: string | null;
  lastName?: string | null;
  ticketNumber?: string | null;
  bookingReference?: string | null;
}

export interface BoardingPassData {
  flightNumber?: string | null;
  departureAirport?: string | null;
  arrivalAirport?: string | null;
  flightDate?: string | null; // YYYY-MM-DD
  departureTime?: string | null; // HH:MM
  arrivalTime?: string | null; // HH:MM
  passengerName?: string | null; // e.g., "SURNAME/FIRSTNAME"
  bookingReference?: string | null;
  seatNumber?: string | null;
  airline?: string | null;
  passengers?: Passenger[]; // List of passengers for multi-pax claims
  flights?: FlightSegment[]; // List of flight segments for multi-leg journeys
}

// Flight segment for multi-leg journeys
export interface FlightSegment {
  flightNumber?: string | null;
  departureAirport?: string | null;
  arrivalAirport?: string | null;
  departureDate?: string | null; // YYYY-MM-DD
  departureTime?: string | null; // HH:MM
  arrivalTime?: string | null; // HH:MM
  airline?: string | null;
  // Leg type classification
  legType?: 'outbound' | 'outbound_connection' | 'return' | 'return_connection' | null;
  // Trip index: groups flights into logical trips (1=outbound, 2=return, etc.)
  tripIndex?: number | null;
}

// Field-level confidence scores (backend returns just numbers)
export interface FieldConfidenceScores {
  flightNumber?: number;
  departureAirport?: number;
  arrivalAirport?: number;
  flightDate?: number;
  departureTime?: number;
  arrivalTime?: number;
  passengerName?: number;
  bookingReference?: number;
  seatNumber?: number;
  airline?: number;
}

export interface OCRResponse {
  success: boolean;
  data: BoardingPassData;
  fieldConfidence: FieldConfidenceScores;
  confidenceScore: number;
  rawText?: string;
  errors?: string[];
  warnings?: string[];
  processingTimeMs?: number;
  uploadedFileId?: string;  // ID of saved file for later linking to claim
}
