/**
 * Zod validation schemas derived from OpenAPI specification
 * Used for form validation with React Hook Form
 */

import { z } from 'zod';

// ==================== Common Schemas ====================
const isoDateSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format (YYYY-MM-DD)');
const isoDateTimeSchema = z.string().datetime();
const uuidSchema = z.string().uuid();
const emailSchema = z.string().email('Invalid email address');

// ==================== Address Schema ====================
export const addressSchema = z.object({
  street: z.string().optional(),
  city: z.string().optional(),
  postalCode: z.string().optional(),
  country: z.string().optional(),
});

// ==================== Flight Schemas ====================
export const flightInfoSchema = z.object({
  flightNumber: z.string()
    .min(2, 'Flight number is required')
    .regex(/^[A-Z0-9]{2,3}\d{1,4}$/i, 'Invalid flight number format (e.g., LH1234)'),
  airline: z.string().min(2, 'Airline name is required'),
  departureDate: isoDateSchema,
  departureAirport: z.string()
    .length(3, 'Airport code must be 3 characters')
    .regex(/^[A-Z]{3}$/, 'Invalid IATA airport code'),
  arrivalAirport: z.string()
    .length(3, 'Airport code must be 3 characters')
    .regex(/^[A-Z]{3}$/, 'Invalid IATA airport code'),
  scheduledDeparture: isoDateTimeSchema.optional(),
  scheduledArrival: isoDateTimeSchema.optional(),
  actualDeparture: isoDateTimeSchema.nullable().optional(),
  actualArrival: isoDateTimeSchema.nullable().optional(),
  status: z.enum([
    'scheduled',
    'delayed',
    'cancelled',
    'diverted',
    'boarding',
    'departed',
    'arrived'
  ]).optional(),
  delayMinutes: z.number().int().min(0).nullable().optional(),
});

export const flightStatusSchema = flightInfoSchema.extend({
  id: uuidSchema,
  lastUpdated: isoDateTimeSchema,
  dataSource: z.string(),
});

// ==================== Customer Schemas ====================
export const customerSchema = z.object({
  id: uuidSchema.optional(),
  email: emailSchema,
  firstName: z.string()
    .min(1, 'First name is required')
    .max(50, 'First name must be less than 50 characters'),
  lastName: z.string()
    .min(1, 'Last name is required')
    .max(50, 'Last name must be less than 50 characters'),
  phone: z.string()
    .regex(/^\+?[\d\s\-()]+$/, 'Invalid phone number format')
    .min(8, 'Phone number is too short')
    .max(20, 'Phone number is too long')
    .nullable()
    .optional(),
  address: addressSchema.optional(),
  createdAt: isoDateTimeSchema.optional(),
  updatedAt: isoDateTimeSchema.optional(),
});

// ==================== Eligibility Schemas ====================
export const eligibilityRequestSchema = z.object({
  flightInfo: flightInfoSchema,
  customerInfo: z.object({
    email: emailSchema,
    region: z.enum(['EU', 'US', 'CA'], {
      errorMap: () => ({ message: 'Region must be EU, US, or CA' }),
    }),
  }),
});

export const eligibilityResponseSchema = z.object({
  eligible: z.boolean(),
  compensationAmount: z.number().positive().nullable().optional(),
  currency: z.string().optional(),
  regulation: z.enum(['EU261', 'DOT', 'CTA']).optional(),
  reasons: z.array(z.string()).optional(),
  requirements: z.array(z.string()).optional(),
});

// ==================== Document Schemas ====================
export const documentTypeSchema = z.enum([
  'boarding_pass',
  'id_document',
  'receipt',
  'bank_statement',
  'other'
]);

export const documentSchema = z.object({
  id: uuidSchema.optional(),
  filename: z.string().min(1, 'Filename is required'),
  contentType: z.string(),
  size: z.number().int().positive(),
  documentType: documentTypeSchema,
  uploadedAt: isoDateTimeSchema.optional(),
  url: z.string().url().optional(),
});

// File upload validation (for client-side)
export const fileUploadSchema = z.object({
  file: z.custom<File>((val) => val instanceof File, 'Please select a file'),
  documentType: documentTypeSchema,
}).refine(
  (data) => {
    // Max file size: 10MB
    return data.file.size <= 10 * 1024 * 1024;
  },
  { message: 'File size must be less than 10MB', path: ['file'] }
).refine(
  (data) => {
    // Allowed file types
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    return allowedTypes.includes(data.file.type);
  },
  { message: 'File must be PDF, JPG, or PNG', path: ['file'] }
);

// ==================== Claim Schemas ====================
export const incidentTypeSchema = z.enum([
  'delay',
  'cancellation',
  'denied_boarding',
  'baggage_delay'
]);

export const claimStatusSchema = z.enum([
  'draft',
  'submitted',
  'under_review',
  'approved',
  'rejected',
  'paid',
  'closed'
]);

export const claimSchema = z.object({
  id: uuidSchema.optional(),
  customerId: uuidSchema,
  flightInfo: flightStatusSchema,
  incidentType: incidentTypeSchema,
  status: claimStatusSchema.optional(),
  compensationAmount: z.number().positive().nullable().optional(),
  currency: z.string().optional(),
  documents: z.array(documentSchema).optional(),
  submittedAt: isoDateTimeSchema.optional(),
  updatedAt: isoDateTimeSchema.optional(),
  notes: z.string().nullable().optional(),
});

export const claimRequestSchema = z.object({
  customerInfo: customerSchema,
  flightInfo: flightInfoSchema,
  incidentType: incidentTypeSchema,
  notes: z.string().max(1000, 'Notes must be less than 1000 characters').nullable().optional(),
});

// ==================== Form-Specific Schemas ====================

// Step 1: Flight Lookup
export const flightLookupSchema = z.object({
  flightNumber: z.string()
    .min(2, 'Flight number is required')
    .regex(/^[A-Z0-9]{2,3}\d{1,4}$/i, 'Invalid flight number format (e.g., LH1234)'),
  departureDate: z.string()
    .min(1, 'Departure date is required')
    .refine((val) => val !== '' && val !== undefined && val !== null, {
      message: 'Departure date is required',
    })
    .refine((val) => /^\d{4}-\d{2}-\d{2}$/.test(val), {
      message: 'Invalid date format (YYYY-MM-DD)',
    }),
});

// Step 2: Eligibility (auto-populated, minimal validation)
export const eligibilityFormSchema = z.object({
  email: emailSchema,
});

// Step 3: Passenger Information
export const passengerInfoSchema = z.object({
  firstName: z.string()
    .min(1, 'First name is required')
    .max(50, 'First name must be less than 50 characters'),
  lastName: z.string()
    .min(1, 'Last name is required')
    .max(50, 'Last name must be less than 50 characters'),
  email: emailSchema,
  phone: z.string()
    .regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone number format (e.g., +49123456789)')
    .optional()
    .or(z.literal('')),
  street: z.string().min(1, 'Street address is required'),
  city: z.string().min(1, 'City is required'),
  postalCode: z.string().min(1, 'Postal code is required'),
  country: z.string().min(1, 'Country is required'),
  bookingReference: z.string()
    .max(20, 'Booking reference must be less than 20 characters')
    .optional()
    .or(z.literal('')),
  ticketNumber: z.string()
    .max(20, 'Ticket number must be less than 20 characters')
    .regex(/^(\d{13})?$/, 'Ticket number must be 13 digits')
    .optional()
    .or(z.literal('')),
  incidentType: incidentTypeSchema,
  notes: z.string().max(1000, 'Notes must be less than 1000 characters').optional(),
});

// Claim Status Lookup
export const claimStatusLookupSchema = z.object({
  claimId: z.string()
    .min(1, 'Claim ID is required')
    .uuid('Invalid Claim ID format. Please enter the full Claim ID from your email (e.g., 123e4567-e89b-12d3-a456-426614174000)'),
});

// Auth (Mock)
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

// ==================== Type Inference ====================
export type FlightLookupForm = z.infer<typeof flightLookupSchema>;
export type EligibilityForm = z.infer<typeof eligibilityFormSchema>;
export type PassengerInfoForm = z.infer<typeof passengerInfoSchema>;
export type ClaimStatusLookupForm = z.infer<typeof claimStatusLookupSchema>;
export type LoginForm = z.infer<typeof loginSchema>;
export type FileUploadForm = z.infer<typeof fileUploadSchema>;
