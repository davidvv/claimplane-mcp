import { useState, useRef } from 'react';
import { useDebouncedCallback } from 'use-debounce';

interface UseAutoSaveOptions<T> {
  onSave: (data: T) => Promise<void>;
  debounceMs?: number;
  enabled?: boolean;
}

/**
 * Custom hook for debounced auto-saving of form data.
 * Includes a deep comparison check to prevent redundant saves and infinite loops.
 */
export function useAutoSave<T>({ onSave, debounceMs = 2000, enabled = true }: UseAutoSaveOptions<T>) {
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const lastSavedDataRef = useRef<string>('');

  const debouncedSave = useDebouncedCallback(async (data: T) => {
    if (!enabled) return;
    
    // Prevent redundant saves if data hasn't changed
    const dataString = JSON.stringify(data);
    if (dataString === lastSavedDataRef.current) {
      return;
    }
    
    setIsSaving(true);
    setError(null);
    try {
      await onSave(data);
      lastSavedDataRef.current = dataString;
      setLastSaved(new Date());
    } catch (e) {
      setError('Auto-save failed');
      console.error('Auto-save error:', e);
    } finally {
      setIsSaving(false);
    }
  }, debounceMs);

  // Perform an immediate save without debounce
  const forceSave = async (data: T) => {
    if (!enabled) return;
    
    const dataString = JSON.stringify(data);
    setIsSaving(true);
    setError(null);
    try {
      await onSave(data);
      lastSavedDataRef.current = dataString;
      setLastSaved(new Date());
      return true;
    } catch (e: any) {
      const errorMsg = e.response?.data?.detail || e.message || "Save failed";
      setError(errorMsg);
      console.error("Auto-save error:", e);
      throw e;
    } finally {
      setIsSaving(false);
    }
  };

  return {
    triggerSave: debouncedSave,
    forceSave,
    isSaving,
    lastSaved,
    error,
  };
}
