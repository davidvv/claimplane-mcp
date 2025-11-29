/**
 * Authentication Information Page
 * Explains the passwordless authentication system
 */

import { useState } from 'react';
import { Mail, CheckCircle, Shield, Clock, Send } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import apiClient from '@/services/api';

// Magic link request schema
const magicLinkSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
});

type MagicLinkForm = z.infer<typeof magicLinkSchema>;

export function Auth() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<MagicLinkForm>({
    resolver: zodResolver(magicLinkSchema),
  });

  const onSubmit = async (data: MagicLinkForm) => {
    setIsLoading(true);
    try {
      await apiClient.post('/auth/magic-link/request', { email: data.email });

      toast.success('Magic link sent!', {
        description: 'Check your email for the login link. It will arrive shortly.',
      });

      form.reset();
    } catch (error: any) {
      console.error('Magic link request error:', error);
      toast.error('Request failed', {
        description: error.response?.data?.detail || 'Please try again later.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="py-12 md:py-20">
      <div className="container max-w-3xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            Passwordless Authentication
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            We use magic links for secure, password-free access. No passwords to remember, no passwords to forget.
          </p>
        </div>

        {/* Login Form */}
        <Card className="mb-12 border-primary/20 shadow-lg">
          <CardHeader className="text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Send className="w-8 h-8 text-primary" />
            </div>
            <CardTitle className="text-2xl">Access Your Account</CardTitle>
            <CardDescription>
              Enter your email to receive a magic link and log in instantly
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 w-5 h-5 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="your@email.com"
                    className="pl-11 h-12 text-base"
                    {...form.register('email')}
                    disabled={isLoading}
                  />
                </div>
                {form.formState.errors.email && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.email.message}
                  </p>
                )}
              </div>

              <Button type="submit" disabled={isLoading} className="w-full h-12 text-base">
                {isLoading ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Sending Magic Link...
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5 mr-2" />
                    Send Magic Link
                  </>
                )}
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                A secure login link will be sent to your email
              </p>
            </form>
          </CardContent>
        </Card>

        <div className="grid gap-6 md:grid-cols-2 mb-8">
          {/* How It Works */}
          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <Mail className="w-6 h-6 text-primary" />
              </div>
              <CardTitle>How It Works</CardTitle>
              <CardDescription>Simple, secure authentication via email</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-3">
                <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-xs font-semibold text-primary">1</span>
                </div>
                <div>
                  <p className="font-medium">Submit Your Claim</p>
                  <p className="text-sm text-muted-foreground">No account or login required</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-xs font-semibold text-primary">2</span>
                </div>
                <div>
                  <p className="font-medium">Check Your Email</p>
                  <p className="text-sm text-muted-foreground">We'll send you a secure magic link</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-xs font-semibold text-primary">3</span>
                </div>
                <div>
                  <p className="font-medium">Click the Link</p>
                  <p className="text-sm text-muted-foreground">Instantly logged in, view your claim</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Benefits */}
          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <CardTitle>Why Magic Links?</CardTitle>
              <CardDescription>Modern, secure, and convenient</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium">No Passwords</p>
                  <p className="text-sm text-muted-foreground">Nothing to create, store, or remember</p>
                </div>
              </div>
              <div className="flex gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium">More Secure</p>
                  <p className="text-sm text-muted-foreground">No password leaks or brute force attacks</p>
                </div>
              </div>
              <div className="flex gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium">One-Click Access</p>
                  <p className="text-sm text-muted-foreground">Instant authentication from your email</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Important Information */}
        <Card className="mb-8">
          <CardHeader>
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center mb-4">
              <Clock className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <CardTitle>Important Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-3">
              <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
              <p className="text-muted-foreground">
                <strong className="text-foreground">Magic links expire after 48 hours</strong> for security.
                If your link expires, simply submit a new claim or request a new link.
              </p>
            </div>
            <div className="flex gap-3">
              <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
              <p className="text-muted-foreground">
                <strong className="text-foreground">Links are single-use only</strong>.
                Once you click a magic link and log in, that link cannot be used again.
              </p>
            </div>
            <div className="flex gap-3">
              <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
              <p className="text-muted-foreground">
                <strong className="text-foreground">Your session lasts 7 days</strong>.
                After logging in via magic link, you'll stay logged in for a week.
              </p>
            </div>
            <div className="flex gap-3">
              <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
              <p className="text-muted-foreground">
                <strong className="text-foreground">Check your spam folder</strong> if you don't see the email.
                Magic link emails are sent instantly from noreply@easyairclaim.com.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Call to Action */}
        <div className="text-center space-y-4">
          <Button
            size="lg"
            onClick={() => navigate('/claim/new')}
            className="px-8"
          >
            Submit a Claim
          </Button>
          <p className="text-sm text-muted-foreground">
            No registration required. Get started in seconds.
          </p>
        </div>

        {/* FAQ */}
        <Card className="mt-12">
          <CardHeader>
            <CardTitle>Frequently Asked Questions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-semibold mb-2">What if I don't receive the magic link email?</h3>
              <p className="text-sm text-muted-foreground">
                Check your spam/junk folder first. If you still don't see it, verify you entered the correct
                email address when submitting your claim. You can submit another claim to receive a new magic link.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Can I use magic links on multiple devices?</h3>
              <p className="text-sm text-muted-foreground">
                Yes! Once you log in via a magic link, your session is valid for 7 days on that device.
                You can click a new magic link on a different device to log in there as well.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Is this more secure than passwords?</h3>
              <p className="text-sm text-muted-foreground">
                Absolutely. Magic links eliminate common security issues like weak passwords, password reuse,
                and phishing attacks. Each link is unique, time-limited, and single-use.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Do I need to create an account?</h3>
              <p className="text-sm text-muted-foreground">
                No! Your account is automatically created when you submit your first claim.
                We use your email address to identify you, and magic links to authenticate you.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
