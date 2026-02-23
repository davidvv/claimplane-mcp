import { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import apiClient from '@/services/api';
import { buildDisplayName } from '@/services/auth';

export function MagicLinkPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [errorMessage, setErrorMessage] = useState('');
  const resume = searchParams.get('resume');
  const claimId = searchParams.get('claim_id');
  
  // Prevent double verification in React Strict Mode (development)
  const hasVerified = useRef(false);

  useEffect(() => {
    const verifyToken = async () => {
      // Prevent double execution
      if (hasVerified.current) {
        return;
      }
      hasVerified.current = true;
      const token = searchParams.get('token');

      if (!token) {
        setStatus('error');
        setErrorMessage('No token provided');
        return;
      }

      try {
        // Log only in development without sensitive data
        if (import.meta.env.DEV) {
          console.log('[MagicLink] Verifying token...');
        }

        // Read pending redirect BEFORE verification (in case of errors clearing it)
        const pendingRedirect = sessionStorage.getItem('postLoginRedirect');

        // Verify magic link token
        const response = await apiClient.post(`/auth/magic-link/verify/${token}`);

        // Log success in dev only
        if (import.meta.env.DEV) {
          console.log('[MagicLink] Verification successful');
        }

        // Tokens are automatically stored in HTTP-only cookies by backend
        // Store user info in sessionStorage for UI purposes only
        if (response.data.user) {
          // Validate that we have email (required for all flows)
          // Note: first_name/last_name may be empty for draft claims where user hasn't filled passenger info yet
          if (!response.data.user.email) {
            console.error('[MagicLink] Incomplete user data received');
            setStatus('error');
            setErrorMessage('Login failed: Incomplete user data received. Please contact support.');
            return;
          }

          const displayName = buildDisplayName(
            response.data.user.first_name || '',
            response.data.user.last_name || '',
            response.data.user.email
          );
          sessionStorage.setItem('user_email', response.data.user.email);
          sessionStorage.setItem('user_id', response.data.user.id);
          sessionStorage.setItem('user_name', displayName);
          sessionStorage.setItem('user_role', response.data.user.role);
        }

        if (import.meta.env.DEV) {
          console.log('[MagicLink] Authentication complete');
        }

        setStatus('success');

        // Clear redirect from sessionStorage (we already read it above)
        if (pendingRedirect) {
          sessionStorage.removeItem('postLoginRedirect');
        }

        // Ensure cookies are set before redirecting
        setTimeout(() => {
          // Check user role and redirect accordingly
          const userRole = response.data.user.role;
          
          // Check for pending redirect from interrupted flow (e.g., draft resume link)
          if (pendingRedirect) {
            // Validate redirect is safe (must start with /) to prevent open redirect attacks
            if (pendingRedirect.startsWith('/') && !pendingRedirect.startsWith('//')) {
              if (import.meta.env.DEV) {
                console.log('[MagicLink] Resuming interrupted flow');
              }
              navigate(pendingRedirect);
              return;
            } else {
              console.warn('[MagicLink] Invalid redirect URL detected, ignoring');
            }
          }

          // Check for draft resume (resume=true parameter from email link)
          if (resume === 'true' && claimId) {
            if (import.meta.env.DEV) {
              console.log('[MagicLink] Draft resume detected, redirecting');
            }
            navigate(`/claim/new?resume=${claimId}`);
            return;
          }

          if (userRole === 'admin' || userRole === 'superadmin') {
            // Admin users go to admin panel
            if (import.meta.env.DEV) {
              console.log('[MagicLink] Admin user, redirecting to dashboard');
            }
            navigate('/panel/dashboard');
          } else if (claimId) {
            // Customer with specific claim goes to status page
            if (import.meta.env.DEV) {
              console.log('[MagicLink] Redirecting to status page');
            }
            navigate(`/status?claimId=${claimId}`);
          } else {
            // Customer without claim goes to claims list
            if (import.meta.env.DEV) {
              console.log('[MagicLink] Redirecting to My Claims');
            }
            navigate('/my-claims');
          }
        }, 500); // Wait briefly for cookies to be set

      } catch (error: any) {
        console.error('[MagicLink] Verification failed:', error.message || 'Unknown error');
        setStatus('error');
        setErrorMessage(error.response?.data?.detail || 'Invalid or expired link');
      }
    };

    verifyToken();
  }, [searchParams, navigate, resume, claimId]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="max-w-md w-full space-y-8 p-8">
        {status === 'verifying' && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <h2 className="mt-6 text-xl font-semibold">Verifying your link...</h2>
            <p className="mt-2 text-muted-foreground">Please wait a moment</p>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            <div className="text-6xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-green-600">Success!</h2>
            <p className="mt-2 text-muted-foreground">
              {resume === 'true'
                ? 'Redirecting to resume your draft claim...'
                : claimId
                  ? 'Redirecting you to your claim...'
                  : 'Redirecting you to your claims dashboard...'}
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div className="text-6xl mb-4">✕</div>
            <h2 className="text-2xl font-bold text-red-600">Link Invalid</h2>
            <p className="mt-2 text-muted-foreground">{errorMessage}</p>
            <p className="mt-4 text-sm">
              Magic links expire after 48 hours. Please request a new one.
            </p>
            <button
              onClick={() => navigate('/')}
              className="mt-6 px-4 py-2 bg-primary text-white rounded hover:bg-primary/90"
            >
              Go to Home
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
