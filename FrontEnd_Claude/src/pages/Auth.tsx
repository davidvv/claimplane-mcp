/**
 * Authentication page (stub for future JWT implementation)
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { LogIn, AlertCircle } from 'lucide-react';
import { LoginSchema, type LoginFormData } from '@/schemas/validation';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';

/**
 * STUB AUTHENTICATION
 * This is a mock login for demonstration purposes.
 * In Phase 3, this will be replaced with JWT-based authentication.
 */
export function AuthPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(LoginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setLoading(true);

    // Mock authentication delay
    setTimeout(() => {
      // Generate mock JWT token
      const mockToken = btoa(
        JSON.stringify({
          email: data.email,
          userId: 'mock-user-id',
          exp: Date.now() + 3600000, // 1 hour
        })
      );

      // Store token in localStorage
      localStorage.setItem('auth_token', mockToken);
      localStorage.setItem('user_email', data.email);

      toast.success('Login successful!');
      setLoading(false);

      // Redirect to home or intended page
      navigate('/');
    }, 1000);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 dark:bg-gray-900">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center space-x-3">
            <div className="rounded-full bg-primary-100 p-3 dark:bg-primary-900">
              <LogIn className="h-6 w-6 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <CardTitle>Sign In</CardTitle>
              <CardDescription>Access your EasyAirClaim account</CardDescription>
            </div>
          </div>
        </CardHeader>

        {/* Mock Authentication Notice */}
        <div className="mb-6 rounded-lg bg-yellow-50 p-4 dark:bg-yellow-900/20">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-yellow-600 dark:text-yellow-400" />
            <div className="text-sm text-yellow-800 dark:text-yellow-200">
              <p className="font-medium">Development Mode</p>
              <p className="mt-1">
                This is a stub authentication for demonstration. Use any email/password to log
                in. Full JWT authentication will be implemented in Phase 3.
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Input
            type="email"
            label="Email Address"
            placeholder="john.doe@example.com"
            error={errors.email?.message}
            required
            autoComplete="email"
            {...register('email')}
          />

          <Input
            type="password"
            label="Password"
            placeholder="Enter your password"
            error={errors.password?.message}
            helperText="Minimum 8 characters"
            required
            autoComplete="current-password"
            {...register('password')}
          />

          <Button type="submit" fullWidth loading={loading} disabled={loading}>
            <LogIn className="mr-2 h-4 w-4" />
            Sign In
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Don't have an account?{' '}
            <button
              type="button"
              className="font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400"
              onClick={() => toast.info('Registration coming soon in Phase 3')}
            >
              Sign up
            </button>
          </p>
        </div>
      </Card>
    </div>
  );
}
