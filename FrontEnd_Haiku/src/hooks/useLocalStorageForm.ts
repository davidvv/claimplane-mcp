import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook for form data persistence with localStorage
 * @param key - localStorage key
 * @param initialValue - Initial form data
 * @param schema - Optional Zod schema for validation
 * @returns Form data and update functions
 */
export function useLocalStorageForm<T>(
  key: string,
  initialValue: T,
  schema?: any // Zod schema
): {
  data: T;
  setData: (data: T | ((prev: T) => T)) => void;
  clearData: () => void;
  isLoading: boolean;
  error: string | null;
} {
  const [data, setData] = useState<T>(initialValue);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data from localStorage on mount
  useEffect(() => {
    const loadData = () => {
      try {
        const storedData = localStorage.getItem(key);
        if (storedData) {
          const parsedData = JSON.parse(storedData);
          
          // Validate with schema if provided
          if (schema) {
            try {
              const validatedData = schema.parse(parsedData);
              setData(validatedData);
            } catch (validationError) {
              console.warn('Stored data validation failed:', validationError);
              setError('Stored form data is invalid and has been cleared');
              localStorage.removeItem(key);
              setData(initialValue);
            }
          } else {
            setData(parsedData);
          }
        }
      } catch (error) {
        console.error('Failed to load form data from localStorage:', error);
        setError('Failed to load saved form data');
        localStorage.removeItem(key);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [key, schema, initialValue]);

  // Save data to localStorage whenever it changes
  useEffect(() => {
    if (!isLoading) {
      try {
        localStorage.setItem(key, JSON.stringify(data));
      } catch (error) {
        console.error('Failed to save form data to localStorage:', error);
        setError('Failed to save form data');
      }
    }
  }, [data, isLoading, key]);

  // Clear data from localStorage and reset to initial value
  const clearData = useCallback(() => {
    try {
      localStorage.removeItem(key);
      setData(initialValue);
      setError(null);
    } catch (error) {
      console.error('Failed to clear form data:', error);
      setError('Failed to clear form data');
    }
  }, [key, initialValue]);

  return {
    data,
    setData,
    clearData,
    isLoading,
    error,
  };
}

/**
 * Hook for multi-step form progress tracking
 * @param key - localStorage key
 * @param totalSteps - Total number of steps
 * @returns Form progress and navigation functions
 */
export function useFormProgress(
  key: string,
  totalSteps: number
): {
  currentStep: number;
  completedSteps: number[];
  goToStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  completeStep: (step: number) => void;
  isStepCompleted: (step: number) => boolean;
  canProceedToStep: (step: number) => boolean;
} {
  const [currentStep, setCurrentStep] = useState(1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  // Load progress from localStorage
  useEffect(() => {
    const savedProgress = localStorage.getItem(`${key}_progress`);
    if (savedProgress) {
      try {
        const progress = JSON.parse(savedProgress);
        if (progress.currentStep && Array.isArray(progress.completedSteps)) {
          setCurrentStep(progress.currentStep);
          setCompletedSteps(progress.completedSteps);
        }
      } catch (error) {
        console.error('Failed to load form progress:', error);
      }
    }
  }, [key]);

  // Save progress to localStorage
  useEffect(() => {
    const progress = {
      currentStep,
      completedSteps,
    };
    localStorage.setItem(`${key}_progress`, JSON.stringify(progress));
  }, [currentStep, completedSteps]);

  const goToStep = (step: number) => {
    if (step >= 1 && step <= totalSteps) {
      setCurrentStep(step);
    }
  };

  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const completeStep = (step: number) => {
    if (!completedSteps.includes(step)) {
      setCompletedSteps([...completedSteps, step]);
    }
  };

  const isStepCompleted = (step: number): boolean => {
    return completedSteps.includes(step);
  };

  const canProceedToStep = (step: number): boolean => {
    // Can proceed to step 1 always
    if (step === 1) return true;
    
    // Can proceed to step N if step N-1 is completed
    return isStepCompleted(step - 1);
  };

  return {
    currentStep,
    completedSteps,
    goToStep,
    nextStep,
    prevStep,
    completeStep,
    isStepCompleted,
    canProceedToStep,
  };
}

/**
 * Hook for form auto-save with debouncing
 * @param data - Form data to save
 * @param key - localStorage key
 * @param delay - Debounce delay in milliseconds
 */
export function useAutoSave<T>(
  data: T,
  key: string,
  delay: number = 1000
): {
  isSaving: boolean;
  lastSaved: Date | null;
} {
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setIsSaving(true);
      
      try {
        localStorage.setItem(key, JSON.stringify(data));
        setLastSaved(new Date());
      } catch (error) {
        console.error('Auto-save failed:', error);
      } finally {
        setIsSaving(false);
      }
    }, delay);

    return () => clearTimeout(timeoutId);
  }, [data, key, delay]);

  return {
    isSaving,
    lastSaved,
  };
}

/**
 * Hook for form validation with error persistence
 * @param data - Form data to validate
 * @param schema - Zod schema for validation
 * @param key - localStorage key for errors
 * @returns Validation errors and functions
 */
export function useFormValidation<T>(
  data: T,
  schema: any,
  errorKey: string
): {
  errors: Record<string, string[]>;
  validate: () => boolean;
  validateField: (field: string) => boolean;
  clearErrors: () => void;
} {
  const [errors, setErrors] = useState<Record<string, string[]>>({});

  // Load errors from localStorage
  useEffect(() => {
    const savedErrors = localStorage.getItem(errorKey);
    if (savedErrors) {
      try {
        setErrors(JSON.parse(savedErrors));
      } catch (error) {
        console.error('Failed to load validation errors:', error);
      }
    }
  }, [errorKey]);

  // Save errors to localStorage
  useEffect(() => {
    localStorage.setItem(errorKey, JSON.stringify(errors));
  }, [errors, errorKey]);

  const validate = (): boolean => {
    try {
      schema.parse(data);
      setErrors({});
      return true;
    } catch (error) {
      if (error instanceof Error && 'issues' in error) {
        const fieldErrors: Record<string, string[]> = {};
        
        // @ts-ignore - Zod error structure
        error.issues.forEach((issue: any) => {
          const field = issue.path.join('.');
          if (!fieldErrors[field]) {
            fieldErrors[field] = [];
          }
          fieldErrors[field].push(issue.message);
        });
        
        setErrors(fieldErrors);
      }
      return false;
    }
  };

  const validateField = (field: string): boolean => {
    try {
      // Extract field value
      const fieldValue = field.split('.').reduce((obj, key) => obj?.[key], data as any);
      
      // Validate single field
      const fieldSchema = schema.shape[field];
      if (fieldSchema) {
        fieldSchema.parse(fieldValue);
        
        // Clear errors for this field
        setErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors[field];
          return newErrors;
        });
        
        return true;
      }
    } catch (error) {
      if (error instanceof Error && 'issues' in error) {
        const fieldErrors: string[] = [];
        
        // @ts-ignore - Zod error structure
        error.issues.forEach((issue: any) => {
          fieldErrors.push(issue.message);
        });
        
        setErrors(prev => ({
          ...prev,
          [field]: fieldErrors,
        }));
      }
      return false;
    }
    
    return true;
  };

  const clearErrors = () => {
    setErrors({});
    localStorage.removeItem(errorKey);
  };

  return {
    errors,
    validate,
    validateField,
    clearErrors,
  };
}