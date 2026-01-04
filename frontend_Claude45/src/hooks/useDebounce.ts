/**
 * useDebounce Hook
 *
 * Phase 6.5: Flight Search by Route
 *
 * Purpose:
 * Delays the execution of a value update to reduce API calls during rapid
 * user input (e.g., typing in airport autocomplete field).
 *
 * Usage:
 * ```tsx
 * const [searchQuery, setSearchQuery] = useState('');
 * const debouncedQuery = useDebounce(searchQuery, 300);
 *
 * useEffect(() => {
 *   if (debouncedQuery.length >= 2) {
 *     fetchAirports(debouncedQuery);
 *   }
 * }, [debouncedQuery]);
 * ```
 */

import { useState, useEffect } from 'react';

/**
 * Hook that debounces a value.
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns The debounced value
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Set a timeout to update the debounced value after delay
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up the timeout if value changes before delay expires
    // or if component unmounts
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
