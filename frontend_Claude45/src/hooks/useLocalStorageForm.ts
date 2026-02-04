/**
 * Custom hook for persisting form data to sessionStorage
 * Allows users to resume their claim form if they refresh the page
 */

import { useState } from 'react';

export function useSessionStorageForm<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  // Get initial value from sessionStorage or use provided initialValue
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.sessionStorage.getItem(key);
      if (!item || item === 'undefined' || item === 'null') return initialValue;
      return JSON.parse(item);
    } catch (error) {
      console.error(`Error loading ${key} from sessionStorage:`, error);
      return initialValue;
    }
  });

  // Update sessionStorage when value changes
  const setValue = (value: T | ((prev: T) => T)) => {
    try {
      setStoredValue((prev) => {
        const nextValue = value instanceof Function ? value(prev) : value;
        window.sessionStorage.setItem(key, JSON.stringify(nextValue));
        return nextValue;
      });
    } catch (error) {
      console.error(`Error saving ${key} to sessionStorage:`, error);
    }
  };

  // Clear the stored value
  const clearValue = () => {
    try {
      window.sessionStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.error(`Error clearing ${key} from sessionStorage:`, error);
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
  draftClaimId?: string;
  draftAccessToken?: string;
}

export function useClaimFormPersistence() {
  const [formData, setFormData, clearFormData] = useSessionStorageForm<ClaimFormData>(
    'claimplane_form_data',
    { currentStep: 1 }
  );

  const updateStep = (step: number) => {
    setFormData((prev: ClaimFormData) => ({ ...prev, currentStep: step }));
  };

  const updateFlightData = (data: any) => {
    setFormData((prev: ClaimFormData) => ({ ...prev, flightData: data }));
  };

  const updateEligibilityData = (data: any) => {
    setFormData((prev: ClaimFormData) => ({ ...prev, eligibilityData: data }));
  };

  const updatePassengerData = (data: any) => {
    setFormData((prev: ClaimFormData) => ({ ...prev, passengerData: data }));
  };

  const updateDocuments = (docs: any[]) => {
    setFormData((prev: ClaimFormData) => ({ ...prev, documents: docs }));
  };

  const updateDraftInfo = (id?: string, token?: string) => {
    setFormData((prev: ClaimFormData) => ({ ...prev, draftClaimId: id, draftAccessToken: token }));
  };

  return {
    formData,
    updateStep,
    updateFlightData,
    updateEligibilityData,
    updatePassengerData,
    updateDocuments,
    updateDraftInfo,
    clearFormData,
  };
}
