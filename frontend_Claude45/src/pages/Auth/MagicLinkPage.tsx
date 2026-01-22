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
        console.log('Verifying magic link token...');
        console.log('Token:', token);
        console.log('Claim ID:', claimId);
        console.log('Resume flag:', resume);

        // Read pending redirect BEFORE verification (in case of errors clearing it)
        const pendingRedirect = sessionStorage.getItem('postLoginRedirect');
        console.log('Pending redirect from sessionStorage:', pendingRedirect);

        // Verify magic link token
        const response = await apiClient.post(`/auth/magic-link/verify/${token}`);

        console.log('Magic link verification successful:', response.data);

        // Tokens are automatically stored in HTTP-only cookies by backend
        // Store user info in localStorage for UI purposes only
        if (response.data.user) {
          // Validate that we have email (required for all flows)
          // Note: first_name/last_name may be empty for draft claims where user hasn't filled passenger info yet
          if (!response.data.user.email) {
            console.error('Backend returned incomplete user data during magic link verification');
            setStatus('error');
            setErrorMessage('Login failed: Incomplete user data received. Please contact support.');
            return;
          }

          const displayName = buildDisplayName(
            response.data.user.first_name || '',
            response.data.user.last_name || '',
            response.data.user.email
          );
          localStorage.setItem('user_email', response.data.user.email);
          localStorage.setItem('user_id', response.data.user.id);
          localStorage.setItem('user_name', displayName);
          localStorage.setItem('user_role', response.data.user.role);
        }

        console.log('Authentication cookies set by backend');
        console.log('User:', response.data.user.email, 'ID:', response.data.user.id);

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
            if (pendingRedirect.startsWith('/')) {
              console.log('Resuming interrupted flow:', pendingRedirect);
              navigate(pendingRedirect);
              return;
            } else {
              console.warn('Invalid redirect URL detected, ignoring:', pendingRedirect);
            }
          }

          // Check for draft resume (resume=true parameter from email link)
          if (resume === 'true' && claimId) {
            console.log('Draft resume detected, redirecting to claim form with resume:', claimId);
            navigate(`/claim/new?resume=${claimId}`);
            return;
          }

          if (userRole === 'admin' || userRole === 'superadmin') {
            // Admin users go to admin panel
            console.log('Admin user detected, redirecting to panel dashboard');
            navigate('/panel/dashboard');
          } else if (claimId) {
            // Customer with specific claim goes to status page
            console.log('Redirecting to status page with claim ID:', claimId);
            navigate(`/status?claimId=${claimId}`);
          } else {
            // Customer without claim goes to claims list
            console.log('Redirecting to My Claims page (no specific claim ID)');
            navigate('/my-claims');
          }
        }, 500); // Wait briefly for cookies to be set

      } catch (error: any) {
        console.error('Magic link verification failed:', error);
        console.error('Error response:', error.response?.data);
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
