/**
 * Success page after claim submission
 */
import { useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle, Mail, FileText } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';

export function SuccessPage() {
  const [searchParams] = useSearchParams();
  const claimId = searchParams.get('claimId');

  useEffect(() => {
    // Confetti animation or celebration effect
    console.log('Claim submitted successfully!', claimId);
  }, [claimId]);

  return (
    <div className="min-h-screen bg-gray-50 py-12 dark:bg-gray-900">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-2xl">
          {/* Success Icon */}
          <div className="mb-8 text-center">
            <div className="mx-auto mb-6 inline-block rounded-full bg-green-100 p-6 dark:bg-green-900">
              <CheckCircle className="h-20 w-20 text-green-600 dark:text-green-400" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100">
              Claim Submitted Successfully!
            </h1>
            <p className="mt-4 text-xl text-gray-600 dark:text-gray-400">
              Your claim has been received and is being processed
            </p>
          </div>

          {/* Claim ID */}
          {claimId && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Your Claim ID</CardTitle>
                <CardDescription>
                  Save this ID to track your claim status
                </CardDescription>
              </CardHeader>

              <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
                <code className="block break-all text-sm font-mono text-gray-900 dark:text-gray-100">
                  {claimId}
                </code>
              </div>

              <div className="mt-4">
                <Link to={`/status?claimId=${claimId}`}>
                  <Button variant="outline" fullWidth>
                    <FileText className="mr-2 h-4 w-4" />
                    View Claim Status
                  </Button>
                </Link>
              </div>
            </Card>
          )}

          {/* Next Steps */}
          <Card className="mb-6">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Mail className="h-5 w-5 text-primary-600" />
                <CardTitle>What Happens Next?</CardTitle>
              </div>
            </CardHeader>

            <ol className="space-y-4">
              <li className="flex items-start space-x-3">
                <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-600 dark:bg-primary-900 dark:text-primary-400">
                  1
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    Email Confirmation
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    You'll receive a confirmation email with your Claim ID and next steps
                  </p>
                </div>
              </li>

              <li className="flex items-start space-x-3">
                <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-600 dark:bg-primary-900 dark:text-primary-400">
                  2
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    Claim Review
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Our team will review your claim and verify all details within 24-48 hours
                  </p>
                </div>
              </li>

              <li className="flex items-start space-x-3">
                <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-600 dark:bg-primary-900 dark:text-primary-400">
                  3
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    Airline Communication
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    We'll contact the airline on your behalf to process your compensation claim
                  </p>
                </div>
              </li>

              <li className="flex items-start space-x-3">
                <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-600 dark:bg-primary-900 dark:text-primary-400">
                  4
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    Get Compensated
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Once approved, you'll receive your compensation directly to your account
                  </p>
                </div>
              </li>
            </ol>
          </Card>

          {/* Additional Info */}
          <Card className="mb-6">
            <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
              <h3 className="font-medium text-blue-900 dark:text-blue-100">
                Important Reminders
              </h3>
              <ul className="ml-4 mt-2 list-disc space-y-1 text-sm text-blue-800 dark:text-blue-200">
                <li>Check your email for the confirmation message</li>
                <li>You can track your claim status anytime using your Claim ID</li>
                <li>We may contact you if we need additional documents</li>
                <li>Average processing time is 4-8 weeks</li>
              </ul>
            </div>
          </Card>

          {/* Action Buttons */}
          <div className="flex flex-col gap-4 sm:flex-row">
            <Link to="/" className="flex-1">
              <Button variant="outline" fullWidth>
                Back to Home
              </Button>
            </Link>
            <Link to="/claim" className="flex-1">
              <Button variant="secondary" fullWidth>
                File Another Claim
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
