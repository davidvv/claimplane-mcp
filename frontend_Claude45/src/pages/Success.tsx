/**
 * Claim submission success page
 */

import { useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle, Mail, Search, FileText } from 'lucide-react';
import confetti from 'canvas-confetti';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { getShortClaimId } from '@/lib/utils';

export function Success() {
  const [searchParams] = useSearchParams();
  const claimId = searchParams.get('claimId');

  useEffect(() => {
    // Trigger confetti animation
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
    });
  }, []);

  return (
    <div className="py-12 md:py-20">
      <div className="container max-w-3xl">
        {/* Success Message */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/20 mb-6">
            <CheckCircle className="w-12 h-12 text-green-600" />
          </div>

          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            Claim Submitted Successfully!
          </h1>
          <p className="text-xl text-muted-foreground">
            We've received your compensation claim and will begin processing it
            immediately.
          </p>
        </div>

        {/* Claim ID */}
        {claimId && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Your Claim ID</CardTitle>
              <CardDescription>
                Save this ID to track your claim status
              </CardDescription>
            </CardHeader>

            <CardContent>
              <div className="bg-muted rounded-lg p-6 text-center">
                <p className="text-sm text-muted-foreground mb-2">Claim ID</p>
                <p className="text-2xl font-mono font-bold">
                  {getShortClaimId(claimId)}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Full ID: {claimId}
                </p>
              </div>

              <div className="mt-4">
                <Link to={`/status?claimId=${claimId}`}>
                  <Button variant="outline" className="w-full">
                    <Search className="w-4 h-4 mr-2" />
                    View Claim Status
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Next Steps */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>What Happens Next?</CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                <Mail className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">1. Confirmation Email</h3>
                <p className="text-sm text-muted-foreground">
                  You'll receive a confirmation email with your claim details and Claim
                  ID within the next few minutes.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                <Search className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">2. Expert Review</h3>
                <p className="text-sm text-muted-foreground">
                  Our team will review your claim and contact the airline on your
                  behalf. This typically takes 2-4 weeks.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                <CheckCircle className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">3. Get Paid</h3>
                <p className="text-sm text-muted-foreground">
                  Once approved, you'll receive your compensation directly to your bank
                  account within 8-12 weeks.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Important Information */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Important Information</CardTitle>
          </CardHeader>

          <CardContent className="space-y-3 text-sm">
            <div className="flex items-start gap-2">
              <FileText className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
              <p className="text-muted-foreground">
                <strong>Check your email:</strong> We've sent a confirmation email with
                all the details. Please check your spam folder if you don't see it.
              </p>
            </div>

            <div className="flex items-start gap-2">
              <FileText className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
              <p className="text-muted-foreground">
                <strong>Track your claim:</strong> You can check the status of your
                claim anytime using your Claim ID on our status page.
              </p>
            </div>

            <div className="flex items-start gap-2">
              <FileText className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
              <p className="text-muted-foreground">
                <strong>No hidden fees:</strong> We only charge our commission (20% +
                VAT) if your claim is successful. No win, no fee.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Link to="/" className="flex-1">
            <Button variant="outline" className="w-full">
              Back to Home
            </Button>
          </Link>
          {claimId && (
            <Link to={`/status?claimId=${claimId}`} className="flex-1">
              <Button className="w-full">
                <Search className="w-4 h-4 mr-2" />
                Track Claim Status
              </Button>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
