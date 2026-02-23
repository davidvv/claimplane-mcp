/**
 * Custom hook for managing dark mode preference
 * Persists to localStorage and applies class to document
 * 
 * SSR-safe: Uses useEffect for localStorage access
 */

import { useState, useEffect } from 'react';

export function useDarkMode() {
  // Start with safe default for SSR
  const [isDark, setIsDark] = useState<boolean>(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize from localStorage/system preference after mount (client-side only)
  useEffect(() => {
    // Check localStorage first
    const stored = localStorage.getItem('theme');
    if (stored) {
      setIsDark(stored === 'dark');
    } else {
      // Fall back to system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setIsDark(prefersDark);
    }
    setIsInitialized(true);
  }, []);

  useEffect(() => {
    // Skip if not initialized yet (SSR or initial mount)
    if (!isInitialized) return;
    
    // Apply theme class to document
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark, isInitialized]);

  const toggleDarkMode = () => {
    setIsDark(!isDark);
  };

  return { isDark, toggleDarkMode };
}
