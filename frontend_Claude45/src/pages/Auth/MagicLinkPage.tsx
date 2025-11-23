import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import apiClient from '@/services/api';

export function MagicLinkPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const verifyToken = async () => {
      const token = searchParams.get('token');
      const claimId = searchParams.get('claim_id');

      if (!token) {
        setStatus('error');
        setErrorMessage('No token provided');
        return;
      }

      try {
        console.log('Verifying magic link token...');
        console.log('Token:', token);
        console.log('Claim ID:', claimId);

        // Verify magic link token
        const response = await apiClient.post(`/auth/magic-link/verify/${token}`);

        console.log('Magic link verification successful:', response.data);

        // Store tokens and ensure they're available before redirecting
        try {
          localStorage.setItem('auth_token', response.data.tokens.access_token);
          localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
          localStorage.setItem('user_email', response.data.user.email);
          localStorage.setItem('user_id', response.data.user.id);
          localStorage.setItem('user_name', `${response.data.user.first_name} ${response.data.user.last_name}`);
          
          // Verify tokens are stored
          const storedToken = localStorage.getItem('auth_token');
          if (!storedToken) {
            throw new Error('Failed to store authentication token');
          }

          console.log('Authentication tokens stored successfully');
          console.log('User:', response.data.user.email, 'ID:', response.data.user.id);

          setStatus('success');

          // Ensure authentication state is ready before redirecting
          setTimeout(() => {
            if (claimId) {
              console.log('Redirecting to status page with claim ID:', claimId);
              navigate(`/status?claimId=${claimId}`);
            } else {
              console.log('Redirecting to My Claims page (no specific claim ID)');
              navigate('/my-claims');
            }
          }, 1000); // Wait for tokens to be fully stored
        } catch (storageError) {
          console.error('Failed to store authentication tokens:', storageError);
          setStatus('error');
          setErrorMessage('Failed to complete authentication. Please try again.');
        }

      } catch (error: any) {
        console.error('Magic link verification failed:', error);
        console.error('Error response:', error.response?.data);
        setStatus('error');
        setErrorMessage(error.response?.data?.detail || 'Invalid or expired link');
      }
    };

    verifyToken();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
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
              {searchParams.get('claim_id')
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
