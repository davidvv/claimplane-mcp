/**
 * Authentication page - Login and Registration
 * Integrated with Phase 3 JWT backend
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { LogIn, UserPlus } from 'lucide-react';
import { z } from 'zod';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import * as authService from '@/services/auth';

// Login schema
const LoginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

// Registration schema (matching Phase 3 backend requirements)
const RegisterSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z
    .string()
    .min(12, 'Password must be at least 12 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),
  confirmPassword: z.string(),
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  phone: z.string().optional(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

type LoginFormData = z.infer<typeof LoginSchema>;
type RegisterFormData = z.infer<typeof RegisterSchema>;

export function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);

  // Login form
  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(LoginSchema),
  });

  // Registration form
  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(RegisterSchema),
  });

  const onLogin = async (data: LoginFormData) => {
    setLoading(true);
    try {
      const response = await authService.login({
        email: data.email,
        password: data.password,
      });

      toast.success(`Welcome back, ${response.user.first_name}!`);

      // Redirect to home or intended page
      const intendedPath = sessionStorage.getItem('intended_path') || '/';
      sessionStorage.removeItem('intended_path');
      navigate(intendedPath);
    } catch (error: any) {
      console.error('Login error:', error);
      toast.error(error.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const onRegister = async (data: RegisterFormData) => {
    setLoading(true);
    try {
      const response = await authService.register({
        email: data.email,
        password: data.password,
        first_name: data.first_name,
        last_name: data.last_name,
        phone: data.phone,
      });

      toast.success(`Welcome, ${response.user.first_name}! Your account has been created.`);

      // Redirect to home
      navigate('/');
    } catch (error: any) {
      console.error('Registration error:', error);
      const errorMessage = error.response?.data?.detail || 'Registration failed. Please try again.';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 dark:bg-gray-900">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center space-x-3">
            <div className="rounded-full bg-primary-100 p-3 dark:bg-primary-900">
              {mode === 'login' ? (
                <LogIn className="h-6 w-6 text-primary-600 dark:text-primary-400" />
              ) : (
                <UserPlus className="h-6 w-6 text-primary-600 dark:text-primary-400" />
              )}
            </div>
            <div>
              <CardTitle>{mode === 'login' ? 'Sign In' : 'Create Account'}</CardTitle>
              <CardDescription>
                {mode === 'login'
                  ? 'Access your EasyAirClaim account'
                  : 'Start your flight compensation claim'}
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        {/* Tab Switcher */}
        <div className="mb-6 flex rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
          <button
            type="button"
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              mode === 'login'
                ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white'
                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
            }`}
            onClick={() => setMode('login')}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              mode === 'register'
                ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white'
                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
            }`}
            onClick={() => setMode('register')}
          >
            Sign Up
          </button>
        </div>

        {/* Login Form */}
        {mode === 'login' && (
          <form onSubmit={loginForm.handleSubmit(onLogin)} className="space-y-6">
            <Input
              type="email"
              label="Email Address"
              placeholder="john.doe@example.com"
              error={loginForm.formState.errors.email?.message}
              required
              autoComplete="email"
              {...loginForm.register('email')}
            />

            <Input
              type="password"
              label="Password"
              placeholder="Enter your password"
              error={loginForm.formState.errors.password?.message}
              required
              autoComplete="current-password"
              {...loginForm.register('password')}
            />

            <Button type="submit" fullWidth loading={loading} disabled={loading}>
              <LogIn className="mr-2 h-4 w-4" />
              Sign In
            </Button>
          </form>
        )}

        {/* Registration Form */}
        {mode === 'register' && (
          <form onSubmit={registerForm.handleSubmit(onRegister)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                type="text"
                label="First Name"
                placeholder="John"
                error={registerForm.formState.errors.first_name?.message}
                required
                {...registerForm.register('first_name')}
              />

              <Input
                type="text"
                label="Last Name"
                placeholder="Doe"
                error={registerForm.formState.errors.last_name?.message}
                required
                {...registerForm.register('last_name')}
              />
            </div>

            <Input
              type="email"
              label="Email Address"
              placeholder="john.doe@example.com"
              error={registerForm.formState.errors.email?.message}
              required
              autoComplete="email"
              {...registerForm.register('email')}
            />

            <Input
              type="tel"
              label="Phone Number (Optional)"
              placeholder="+1 234 567 8900"
              error={registerForm.formState.errors.phone?.message}
              {...registerForm.register('phone')}
            />

            <Input
              type="password"
              label="Password"
              placeholder="Create a strong password"
              error={registerForm.formState.errors.password?.message}
              helperText="Min 12 chars with uppercase, lowercase, number, and special character"
              required
              autoComplete="new-password"
              {...registerForm.register('password')}
            />

            <Input
              type="password"
              label="Confirm Password"
              placeholder="Re-enter your password"
              error={registerForm.formState.errors.confirmPassword?.message}
              required
              autoComplete="new-password"
              {...registerForm.register('confirmPassword')}
            />

            <Button type="submit" fullWidth loading={loading} disabled={loading}>
              <UserPlus className="mr-2 h-4 w-4" />
              Create Account
            </Button>
          </form>
        )}

        {/* Forgot Password Link (Login only) */}
        {mode === 'login' && (
          <div className="mt-4 text-center">
            <button
              type="button"
              className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
              onClick={() => toast.info('Password reset coming soon!')}
            >
              Forgot password?
            </button>
          </div>
        )}
      </Card>
    </div>
  );
}
