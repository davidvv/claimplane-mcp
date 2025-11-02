import { z } from 'zod';

// Base schemas
export const flightInfoSchema = z.object({
  flightNumber: z.string().min(1, 'Flight number is required').regex(/^[A-Z]{2}\d{1,4}$/, 'Flight number must be in format XX1234'),
  airline: z.string().min(1, 'Airline is required'),
  departureDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format'),
  departureAirport: z.string().length(3, 'Airport code must be 3 letters').regex(/^[A-Z]{3}$/, 'Invalid airport code format'),
  arrivalAirport: z.string().length(3, 'Airport code must be 3 letters').regex(/^[A-Z]{3}$/, 'Invalid airport code format'),
  scheduledDeparture: z.string().datetime(),
  scheduledArrival: z.string().datetime(),
  actualDeparture: z.string().datetime().optional().nullable(),
  actualArrival: z.string().datetime().optional().nullable(),
  status: z.enum(['scheduled', 'delayed', 'cancelled', 'diverted', 'boarding', 'departed', 'arrived']),
  delayMinutes: z.number().int().nonnegative().optional().nullable(),
});

export const customerSchema = z.object({
  id: z.string().uuid().optional(),
  email: z.string().email('Invalid email address'),
  firstName: z.string().min(1, 'First name is required').max(50, 'First name must be 50 characters or less'),
  lastName: z.string().min(1, 'Last name is required').max(50, 'Last name must be 50 characters or less'),
  phone: z.string().regex(/^\+?\d{6,}$/, 'Phone number must be at least 6 digits').optional().nullable(),
  address: z.object({
    street: z.string().optional(),
    city: z.string().optional(),
    postalCode: z.string().optional(),
    country: z.string().optional(),
  }).optional(),
});

export const addressSchema = z.object({
  street: z.string().optional(),
  city: z.string().optional(),
  postalCode: z.string().optional(),
  country: z.string().optional(),
});

// Eligibility schemas
export const eligibilityRequestSchema = z.object({
  flightInfo: flightInfoSchema,
  customerInfo: z.object({
    email: z.string().email('Invalid email address'),
    region: z.enum(['EU', 'US', 'CA']),
  }),
});

export const eligibilityResponseSchema = z.object({
  eligible: z.boolean(),
  compensationAmount: z.number().positive().optional().nullable(),
  currency: z.string().optional(),
  regulation: z.enum(['EU261', 'DOT', 'CTA']).optional(),
  reasons: z.array(z.string()).optional(),
  requirements: z.array(z.string()).optional(),
});

// Claim schemas
export const claimSchema = z.object({
  id: z.string().uuid().optional(),
  customerId: z.string().uuid(),
  flightInfo: flightInfoSchema.extend({
    id: z.string().uuid(),
    lastUpdated: z.string().datetime(),
    dataSource: z.string(),
  }),
  incidentType: z.enum(['delay', 'cancellation', 'denied_boarding', 'baggage_delay']),
  status: z.enum(['draft', 'submitted', 'under_review', 'approved', 'rejected', 'paid', 'closed']).optional(),
  compensationAmount: z.number().positive().optional().nullable(),
  currency: z.string().optional(),
  documents: z.array(z.object({
    id: z.string().uuid().optional(),
    filename: z.string(),
    contentType: z.string(),
    size: z.number().int().positive(),
    documentType: z.enum(['boarding_pass', 'id_document', 'receipt', 'bank_statement', 'other']),
    uploadedAt: z.string().datetime().optional(),
    url: z.string().url().optional(),
  })).optional(),
  submittedAt: z.string().datetime().optional(),
  updatedAt: z.string().datetime().optional(),
  notes: z.string().optional().nullable(),
});

export const claimRequestSchema = z.object({
  customerInfo: customerSchema,
  flightInfo: flightInfoSchema,
  incidentType: z.enum(['delay', 'cancellation', 'denied_boarding', 'baggage_delay']),
  notes: z.string().optional().nullable(),
});

// Document schemas
export const documentSchema = z.object({
  id: z.string().uuid().optional(),
  filename: z.string(),
  contentType: z.string(),
  size: z.number().int().positive(),
  documentType: z.enum(['boarding_pass', 'id_document', 'receipt', 'bank_statement', 'other']),
  uploadedAt: z.string().datetime().optional(),
  url: z.string().url().optional(),
});

export const documentUploadFormSchema = z.object({
  file: z.instanceof(File),
  documentType: z.enum(['boarding_pass', 'id_document', 'receipt', 'bank_statement', 'other']),
});

// Form validation schemas
export const flightLookupSchema = z.object({
  flightNumber: z.string()
    .min(1, 'Flight number is required')
    .regex(/^[A-Z]{2}\d{1,4}$/, 'Flight number must be in format XX1234 (e.g., LH1234)'),
  date: z.string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')
    .refine((date) => {
      const selectedDate = new Date(date);
      const today = new Date();
      const maxDate = new Date();
      maxDate.setFullYear(today.getFullYear() + 1);
      return selectedDate <= maxDate && selectedDate >= new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
    }, 'Date must be within the past year and up to 1 year in the future'),
});

export const passengerInfoSchema = z.object({
  email: z.string().email('Invalid email address'),
  firstName: z.string().min(1, 'First name is required').max(50, 'First name must be 50 characters or less'),
  lastName: z.string().min(1, 'Last name is required').max(50, 'Last name must be 50 characters or less'),
  phone: z.string().regex(/^\+?\d{6,}$/, 'Phone number must be at least 6 digits').optional().or(z.literal('')),
  address: z.object({
    street: z.string().optional(),
    city: z.string().optional(),
    postalCode: z.string().optional(),
    country: z.string().optional(),
  }).optional(),
});

export const claimStatusSchema = z.object({
  claimId: z.string().uuid('Invalid claim ID format'),
});

// File upload validation
export const fileUploadSchema = z.object({
  file: z.instanceof(File)
    .refine((file) => file.size <= 10 * 1024 * 1024, 'File size must be 10MB or less')
    .refine((file) => ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'].includes(file.type), 'Only PDF, JPG, and PNG files are allowed'),
  documentType: z.enum(['boarding_pass', 'id_document', 'receipt', 'bank_statement', 'other']),
});

// API response schemas
export const apiResponseSchema = z.object({
  success: z.boolean(),
  message: z.string().optional(),
  timestamp: z.string().datetime(),
});

export const errorResponseSchema = z.object({
  success: z.literal(false),
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.array(z.string()).optional(),
  }),
  timestamp: z.string().datetime(),
});

// Pagination schema
export const paginatedResponseSchema = z.object({
  data: z.array(z.any()),
  pagination: z.object({
    page: z.number().int().positive(),
    limit: z.number().int().positive(),
    total: z.number().int().nonnegative(),
    hasNext: z.boolean(),
  }),
});

// JWT payload schema
export const jwtPayloadSchema = z.object({
  sub: z.string(),
  email: z.string().email(),
  exp: z.number(),
  iat: z.number(),
});

// Form progress schema
export const formProgressSchema = z.object({
  currentStep: z.number().int().min(1).max(4),
  data: z.object({
    flightInfo: flightInfoSchema.optional(),
    eligibility: eligibilityResponseSchema.optional(),
    customerInfo: customerSchema.optional(),
    documents: z.array(documentSchema).optional(),
  }),
  completedSteps: z.array(z.number().int().min(1).max(4)),
});

// Type exports
export type FlightInfo = z.infer<typeof flightInfoSchema>;
export type Customer = z.infer<typeof customerSchema>;
export type Address = z.infer<typeof addressSchema>;
export type EligibilityRequest = z.infer<typeof eligibilityRequestSchema>;
export type EligibilityResponse = z.infer<typeof eligibilityResponseSchema>;
export type Claim = z.infer<typeof claimSchema>;
export type ClaimRequest = z.infer<typeof claimRequestSchema>;
export type Document = z.infer<typeof documentSchema>;
export type DocumentUploadFormData = z.infer<typeof documentUploadFormSchema>;
export type ApiResponse<T = any> = z.infer<typeof apiResponseSchema> & { data?: T };
export type ErrorResponse = z.infer<typeof errorResponseSchema>;
export type PaginatedResponse<T = any> = z.infer<typeof paginatedResponseSchema> & { data: T[] };
export type JWTPayload = z.infer<typeof jwtPayloadSchema>;
export type FormProgress = z.infer<typeof formProgressSchema>;