/**
 * useAuthSync hook
 *
 * Automatically synchronizes authentication state between localStorage and backend cookies.
 * Handles session validation on mount and prevents stale UI state.
 */
import { useEffect, useState } from 'react';
import { syncAuthState, isAuthenticated } from '../services/auth';

interface UseAuthSyncResult {
  isValidating: boolean;
  isAuthenticated: boolean;
  error: Error | null;
}

/**
 * Hook to synchronize authentication state
 *
 * Validates session with backend on mount and updates localStorage accordingly.
 * This prevents the issue where user name appears in UI but session has expired.
 *
 * @param validateOnMount - Whether to validate session when component mounts (default: true)
 * @returns Object containing validation status and auth state
 *
 * @example
 * ```tsx
 * function App() {
 *   const { isValidating, isAuthenticated } = useAuthSync();
 *
 *   if (isValidating) {
 *     return <LoadingSpinner />;
 *   }
 *
 *   return isAuthenticated ? <Dashboard /> : <Login />;
 * }
 * ```
 */
export function useAuthSync(validateOnMount: boolean = true): UseAuthSyncResult {
  const [isValidating, setIsValidating] = useState(validateOnMount);
  const [authenticated, setAuthenticated] = useState(isAuthenticated());
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function validateAuth() {
      if (!validateOnMount) {
        setIsValidating(false);
        return;
      }

      try {
        setIsValidating(true);
        setError(null);

        // Validate session with backend
        const isValid = await syncAuthState();

        if (isMounted) {
          setAuthenticated(isValid);
          setIsValidating(false);
        }
      } catch (err) {
        if (isMounted) {
          setError(err as Error);
          setAuthenticated(false);
          setIsValidating(false);
        }
      }
    }

    validateAuth();

    // Cleanup function
    return () => {
      isMounted = false;
    };
  }, [validateOnMount]);

  return {
    isValidating,
    isAuthenticated: authenticated,
    error,
  };
}

/**
 * Hook to periodically sync authentication state
 *
 * Validates session at regular intervals to detect session expiration
 * while user is actively using the app.
 *
 * @param intervalMs - Interval in milliseconds (default: 5 minutes)
 * @param enabled - Whether periodic sync is enabled (default: true)
 *
 * @example
 * ```tsx
 * function Dashboard() {
 *   // Validate session every 5 minutes
 *   usePeriodicAuthSync(5 * 60 * 1000);
 *
 *   return <div>Dashboard content</div>;
 * }
 * ```
 */
export function usePeriodicAuthSync(intervalMs: number = 5 * 60 * 1000, enabled: boolean = true) {
  useEffect(() => {
    if (!enabled || !isAuthenticated()) {
      return;
    }

    const interval = setInterval(async () => {
      // Only validate if user still appears logged in
      if (isAuthenticated()) {
        await syncAuthState();
      }
    }, intervalMs);

    return () => clearInterval(interval);
  }, [intervalMs, enabled]);
}
