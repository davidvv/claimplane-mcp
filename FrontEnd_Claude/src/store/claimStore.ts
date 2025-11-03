/**
 * Zustand store for multi-step claim form state
 */
import { create } from 'zustand';
import type {
  FlightStatusResponse,
  EligibilityResponse,
  Customer,
  IncidentType,
  Region,
} from '@/types/openapi';

interface ClaimFormData {
  // Step 1: Flight Info
  flightNumber: string;
  departureDate: string;
  flightStatus?: FlightStatusResponse;

  // Step 2: Eligibility
  eligibility?: EligibilityResponse;

  // Step 3: Passenger Info
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  region?: Region;
  address?: {
    street: string;
    city: string;
    postalCode: string;
    country: string;
  };
  incidentType?: IncidentType;
  notes?: string;

  // Result
  claimId?: string;
}

interface ClaimState {
  currentStep: number;
  formData: ClaimFormData;
  loading: boolean;
  error: string | null;

  // Actions
  setCurrentStep: (step: number) => void;
  updateFormData: (data: Partial<ClaimFormData>) => void;
  nextStep: () => void;
  previousStep: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  resetForm: () => void;
}

const initialFormData: ClaimFormData = {
  flightNumber: '',
  departureDate: '',
  email: '',
  firstName: '',
  lastName: '',
};

export const useClaimStore = create<ClaimState>((set) => ({
  currentStep: 0,
  formData: initialFormData,
  loading: false,
  error: null,

  setCurrentStep: (step) => set({ currentStep: step }),

  updateFormData: (data) =>
    set((state) => ({
      formData: { ...state.formData, ...data },
    })),

  nextStep: () =>
    set((state) => ({
      currentStep: Math.min(state.currentStep + 1, 3),
    })),

  previousStep: () =>
    set((state) => ({
      currentStep: Math.max(state.currentStep - 1, 0),
    })),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  resetForm: () =>
    set({
      currentStep: 0,
      formData: initialFormData,
      loading: false,
      error: null,
    }),
}));
