/**
 * Custom hook for persisting form data to localStorage
 * Allows users to resume their claim form if they refresh the page
 */

import { useState } from 'react';

export function useLocalStorageForm<T>(
  key: string,
  initialValue: T
): [T, (value: T) => void, () => void] {
  // Get initial value from localStorage or use provided initialValue
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error loading ${key} from localStorage:`, error);
      return initialValue;
    }
  });

  // Update localStorage when value changes
  const setValue = (value: T) => {
    try {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error saving ${key} to localStorage:`, error);
    }
  };

  // Clear the stored value
  const clearValue = () => {
    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.error(`Error clearing ${key} from localStorage:`, error);
    }
  };

  return [storedValue, setValue, clearValue];
}

/**
 * Hook specifically for the claim form wizard
 */
interface ClaimFormData {
  currentStep: number;
  flightData?: any;
  eligibilityData?: any;
  passengerData?: any;
  documents?: any[];
}

export function useClaimFormPersistence() {
  const [formData, setFormData, clearFormData] = useLocalStorageForm<ClaimFormData>(
    'claimplane_form_data',
    { currentStep: 1 }
  );

  const updateStep = (step: number) => {
    setFormData({ ...formData, currentStep: step });
  };

  const updateFlightData = (data: any) => {
    setFormData({ ...formData, flightData: data });
  };

  const updateEligibilityData = (data: any) => {
    setFormData({ ...formData, eligibilityData: data });
  };

  const updatePassengerData = (data: any) => {
    setFormData({ ...formData, passengerData: data });
  };

  const updateDocuments = (docs: any[]) => {
    setFormData({ ...formData, documents: docs });
  };

  return {
    formData,
    updateStep,
    updateFlightData,
    updateEligibilityData,
    updatePassengerData,
    updateDocuments,
    clearFormData,
  };
}
