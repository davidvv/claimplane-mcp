import { useState } from 'react';
import { useDebouncedCallback } from 'use-debounce';

interface UseAutoSaveOptions<T> {
  onSave: (data: T) => Promise<void>;
  debounceMs?: number;
  enabled?: boolean;
}

/**
 * Custom hook for debounced auto-saving of form data.
 */
export function useAutoSave<T>({ onSave, debounceMs = 2000, enabled = true }: UseAutoSaveOptions<T>) {
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const debouncedSave = useDebouncedCallback(async (data: T) => {
    if (!enabled) return;
    
    setIsSaving(true);
    setError(null);
    try {
      await onSave(data);
      setLastSaved(new Date());
    } catch (e) {
      setError('Auto-save failed');
      console.error('Auto-save error:', e);
    } finally {
      setIsSaving(false);
    }
  }, debounceMs);

  // Return trigger function to be used in useEffect or event handlers
  return {
    triggerSave: debouncedSave,
    isSaving,
    lastSaved,
    error,
  };
}
