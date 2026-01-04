/**
 * AirportAutocomplete Component
 *
 * Phase 6.5: Flight Search by Route
 *
 * Purpose:
 * Provides airport search autocomplete functionality for route-based flight search.
 * Users can type an airport name, city, or IATA code to find their departure/arrival airport.
 *
 * Features:
 * - Debounced search (300ms) to reduce API calls
 * - Keyboard navigation support (arrow keys, enter, escape)
 * - Loading state indicator
 * - Error handling
 * - Clear button to reset selection
 */

import React, { useState, useEffect, useRef } from 'react';
import { useDebounce } from '../hooks/useDebounce';
import { searchAirports } from '../services/flights';

export interface Airport {
  iata: string;
  icao?: string;
  name: string;
  city: string;
  country: string;
}

interface AirportAutocompleteProps {
  value?: Airport | null;
  onChange: (airport: Airport | null) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  disabled?: boolean;
  className?: string;
}

export const AirportAutocomplete: React.FC<AirportAutocompleteProps> = ({
  value,
  onChange,
  placeholder = 'Search by city or airport code...',
  label,
  error,
  disabled = false,
  className = '',
}) => {
  const [query, setQuery] = useState<string>(value?.city || value?.iata || '');
  const [results, setResults] = useState<Airport[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [searchError, setSearchError] = useState<string | null>(null);

  const debouncedQuery = useDebounce(query, 300);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch airports when debounced query changes
  useEffect(() => {
    const fetchAirports = async () => {
      // Don't search if query contains parentheses (already selected)
      if (debouncedQuery.includes('(') && debouncedQuery.includes(')')) {
        setResults([]);
        setIsOpen(false);
        return;
      }

      // Only search if query is at least 2 characters
      if (debouncedQuery.length < 2) {
        setResults([]);
        setIsOpen(false);
        return;
      }

      setIsLoading(true);
      setSearchError(null);

      try {
        const response = await searchAirports({
          query: debouncedQuery,
          limit: 10,
        });

        setResults(response.airports || []);
        setIsOpen(true);
        setSelectedIndex(-1);
      } catch (err) {
        console.error('Airport search error:', err);
        setSearchError('Failed to search airports. Please try again.');
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAirports();
  }, [debouncedQuery]);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || results.length === 0) {
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setSelectedIndex(-1);
        break;
    }
  };

  // Handle airport selection
  const handleSelect = (airport: Airport) => {
    setQuery(`${airport.city} (${airport.iata})`);
    onChange(airport);
    setIsOpen(false);
    setSelectedIndex(-1);
  };

  // Handle clear button
  const handleClear = () => {
    setQuery('');
    onChange(null);
    setResults([]);
    setIsOpen(false);
    setSelectedIndex(-1);
  };

  return (
    <div className={`relative ${className}`} ref={wrapperRef}>
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label}
        </label>
      )}

      {/* Input field */}
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (results.length > 0) {
              setIsOpen(true);
            }
          }}
          placeholder={placeholder}
          disabled={disabled}
          className={`
            w-full px-4 py-2 pr-10 border rounded-lg
            focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            disabled:bg-gray-100 disabled:cursor-not-allowed
            dark:bg-gray-800 dark:border-gray-600 dark:text-white
            ${error ? 'border-red-500' : 'border-gray-300'}
          `}
          aria-label={label || placeholder}
          aria-autocomplete="list"
          aria-controls="airport-listbox"
          aria-expanded={isOpen}
        />

        {/* Loading spinner or clear button */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          {isLoading ? (
            <svg
              className="animate-spin h-5 w-5 text-gray-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : query.length > 0 ? (
            <button
              type="button"
              onClick={handleClear}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              aria-label="Clear search"
            >
              <svg
                className="h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          ) : null}
        </div>
      </div>

      {/* Dropdown results */}
      {isOpen && results.length > 0 && (
        <ul
          id="airport-listbox"
          role="listbox"
          className="
            absolute z-50 w-full mt-1 max-h-60 overflow-auto
            bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600
            rounded-lg shadow-lg
          "
        >
          {results.map((airport, index) => (
            <li
              key={airport.iata}
              role="option"
              aria-selected={index === selectedIndex}
              onClick={() => handleSelect(airport)}
              className={`
                px-4 py-2 cursor-pointer
                hover:bg-blue-50 dark:hover:bg-gray-700
                ${index === selectedIndex ? 'bg-blue-100 dark:bg-gray-600' : ''}
              `}
            >
              <div className="font-medium text-gray-900 dark:text-white">
                {airport.name} ({airport.iata})
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                {airport.city}, {airport.country}
                {airport.icao && ` • ${airport.icao}`}
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* No results message */}
      {isOpen && !isLoading && query.length >= 2 && results.length === 0 && (
        <div className="
          absolute z-50 w-full mt-1 p-4
          bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600
          rounded-lg shadow-lg text-center text-gray-500 dark:text-gray-400
        ">
          No airports found for "{query}"
        </div>
      )}

      {/* Error message */}
      {(error || searchError) && (
        <p className="mt-1 text-sm text-red-600 dark:text-red-400">
          {error || searchError}
        </p>
      )}

      {/* Helper text */}
      {!error && !searchError && (
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          Type at least 2 characters to search
        </p>
      )}
    </div>
  );
};
