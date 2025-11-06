/**
 * Zod validation schemas derived from OpenAPI specification
 */
import { z } from 'zod';

// ========== Enums ==========

export const FlightStatusEnum = z.enum([
  'scheduled',
  'delayed',
  'cancelled',
  'diverted',
  'boarding',
  'departed',
  'arrived',
]);

export const IncidentTypeEnum = z.enum([
  'delay',
  'cancellation',
  'denied_boarding',
  'baggage_delay',
]);

export const ClaimStatusEnum = z.enum([
  'draft',
  'submitted',
  'under_review',
  'approved',
  'rejected',
  'paid',
  'closed',
]);

export const DocumentTypeEnum = z.enum([
  'boarding_pass',
  'id_document',
  'receipt',
  'bank_statement',
  'other',
]);

export const RegionEnum = z.enum(['EU', 'US', 'CA']);

export const RegulationEnum = z.enum(['EU261', 'DOT', 'CTA']);

// ========== Address Schema ==========

export const AddressSchema = z.object({
  street: z.string().min(1, 'Street is required').max(200),
  city: z.string().min(1, 'City is required').max(100),
  postalCode: z.string().min(1, 'Postal code is required').max(20),
  country: z.string().min(1, 'Country is required').max(100),
});

// ========== Flight Schemas ==========

export const FlightInfoSchema = z.object({
  flightNumber: z
    .string()
    .min(2, 'Flight number is required')
    .max(10)
    .regex(/^[A-Z0-9]+$/, 'Flight number must contain only uppercase letters and numbers'),
  airline: z.string().min(1, 'Airline is required').max(100),
  departureDate: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format'),
  departureAirport: z
    .string()
    .length(3, 'Airport code must be 3 characters')
    .regex(/^[A-Z]{3}$/, 'Airport code must be 3 uppercase letters'),
  arrivalAirport: z
    .string()
    .length(3, 'Airport code must be 3 characters')
    .regex(/^[A-Z]{3}$/, 'Airport code must be 3 uppercase letters'),
  scheduledDeparture: z.string().datetime().optional(),
  scheduledArrival: z.string().datetime().optional(),
  actualDeparture: z.string().datetime().nullable().optional(),
  actualArrival: z.string().datetime().nullable().optional(),
  status: FlightStatusEnum.optional(),
  delayMinutes: z.number().int().min(0).nullable().optional(),
});

export const FlightStatusResponseSchema = FlightInfoSchema.extend({
  id: z.string().uuid(),
  lastUpdated: z.string().datetime(),
  dataSource: z.string().optional(),
});

// ========== Customer Schemas ==========

export const CustomerSchema = z.object({
  id: z.string().uuid().optional(),
  email: z.string().email('Invalid email address'),
  firstName: z.string().min(1, 'First name is required').max(50),
  lastName: z.string().min(1, 'Last name is required').max(50),
  phone: z
    .string()
    .regex(/^\+?[\d\s\-()]+$/, 'Invalid phone number format')
    .min(8, 'Phone number is too short')
    .max(20, 'Phone number is too long')
    .nullable()
    .optional(),
  address: AddressSchema.optional(),
  createdAt: z.string().datetime().optional(),
  updatedAt: z.string().datetime().optional(),
});

export const CustomerUpdateSchema = z.object({
  email: z.string().email('Invalid email address').optional(),
  firstName: z.string().min(1).max(50).optional(),
  lastName: z.string().min(1).max(50).optional(),
  phone: z
    .string()
    .regex(/^\+?[\d\s\-()]+$/, 'Invalid phone number format')
    .min(8, 'Phone number is too short')
    .max(20, 'Phone number is too long')
    .nullable()
    .optional(),
  address: AddressSchema.optional(),
});

// ========== Eligibility Schemas ==========

export const EligibilityRequestSchema = z.object({
  flightInfo: FlightInfoSchema,
  customerInfo: z.object({
    email: z.string().email('Invalid email address'),
    region: RegionEnum,
  }),
});

export const EligibilityResponseSchema = z.object({
  eligible: z.boolean(),
  compensationAmount: z.number().nullable().optional(),
  currency: z.string().optional(),
  regulation: RegulationEnum.optional(),
  reasons: z.array(z.string()).optional(),
  requirements: z.array(z.string()).optional(),
});

// ========== Document Schemas ==========

export const DocumentSchema = z.object({
  id: z.string().uuid(),
  filename: z.string(),
  contentType: z.string(),
  size: z.number().int().positive(),
  documentType: DocumentTypeEnum,
  uploadedAt: z.string().datetime(),
  url: z.string().url().optional(),
});

export const DocumentUploadSchema = z.object({
  file: z.instanceof(File).refine(
    (file) => file.size <= 10 * 1024 * 1024,
    'File size must be less than 10MB'
  ).refine(
    (file) => ['application/pdf', 'image/jpeg', 'image/png'].includes(file.type),
    'File must be PDF, JPG, or PNG'
  ),
  documentType: DocumentTypeEnum,
});

// ========== Claim Schemas ==========

export const ClaimSchema = z.object({
  id: z.string().uuid(),
  customerId: z.string().uuid(),
  flightInfo: FlightStatusResponseSchema,
  incidentType: IncidentTypeEnum,
  status: ClaimStatusEnum,
  compensationAmount: z.number().nullable().optional(),
  currency: z.string().optional(),
  documents: z.array(DocumentSchema).optional(),
  submittedAt: z.string().datetime().optional(),
  updatedAt: z.string().datetime().optional(),
  notes: z.string().max(1000).nullable().optional(),
});

export const ClaimRequestSchema = z.object({
  customerInfo: CustomerSchema,
  flightInfo: FlightInfoSchema,
  incidentType: IncidentTypeEnum,
  notes: z.string().max(1000).nullable().optional(),
});

// ========== Multi-Step Form Schemas ==========

// Step 1: Flight Lookup
export const Step1FlightLookupSchema = z.object({
  flightNumber: z
    .string()
    .min(2, 'Flight number is required')
    .max(10)
    .transform((val) => val.toUpperCase()),
  departureDate: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format'),
});

// Step 2: Eligibility Check (auto-submitted, no validation needed)

// Step 3: Passenger Info
export const Step3PassengerInfoSchema = z.object({
  email: z.string().email('Invalid email address'),
  firstName: z.string().min(1, 'First name is required').max(50),
  lastName: z.string().min(1, 'Last name is required').max(50),
  phone: z
    .string()
    .regex(/^\+?[\d\s\-()]+$/, 'Invalid phone number format')
    .min(8, 'Phone number is too short')
    .max(20, 'Phone number is too long')
    .nullable()
    .optional(),
  region: RegionEnum,
  address: z.object({
    street: z.string().min(1, 'Street is required').max(200),
    city: z.string().min(1, 'City is required').max(100),
    postalCode: z.string().min(1, 'Postal code is required').max(20),
    country: z.string().min(1, 'Country is required').max(100),
  }),
  incidentType: IncidentTypeEnum,
  notes: z.string().max(1000).optional(),
});

// Step 4: Review (no validation, just display)

// ========== Claim Status Form ==========

export const ClaimStatusLookupSchema = z.object({
  claimId: z.string().uuid('Invalid Claim ID format'),
});

// ========== Auth Schemas ==========

export const LoginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

// ========== Export types inferred from schemas ==========

export type FlightInfoFormData = z.infer<typeof FlightInfoSchema>;
export type CustomerFormData = z.infer<typeof CustomerSchema>;
export type Step1FormData = z.infer<typeof Step1FlightLookupSchema>;
export type Step3FormData = z.infer<typeof Step3PassengerInfoSchema>;
export type ClaimStatusFormData = z.infer<typeof ClaimStatusLookupSchema>;
export type LoginFormData = z.infer<typeof LoginSchema>;
export type DocumentUploadFormData = z.infer<typeof DocumentUploadSchema>;
