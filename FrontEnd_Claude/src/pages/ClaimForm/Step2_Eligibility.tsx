/**
 * Step 2: Eligibility Check
 */
import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { CheckCircle, XCircle, AlertCircle, Plane, MapPin, Clock } from 'lucide-react';
import { eligibilityService } from '@/services/eligibility';
import { useClaimStore } from '@/store/claimStore';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Loading';
import { formatCurrency, formatDate, formatDelay } from '@/lib/utils';

export function Step2Eligibility() {
  const { formData, updateFormData, nextStep, previousStep, setLoading, loading } =
    useClaimStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    checkEligibility();
  }, []);

  const checkEligibility = async () => {
    if (!formData.flightStatus) {
      toast.error('Flight information missing');
      previousStep();
      return;
    }

    setChecking(true);
    setLoading(true);

    try {
      const eligibility = await eligibilityService.checkEligibility({
        flightInfo: formData.flightStatus,
        customerInfo: {
          email: formData.email || 'temp@example.com', // Temp for check
          region: 'EU', // Default to EU, will be updated in Step 3
        },
      });

      updateFormData({ eligibility });
      toast.success('Eligibility check complete!');
    } catch (error) {
      console.error('Eligibility check error:', error);
      toast.error('Failed to check eligibility. Please try again.');
    } finally {
      setChecking(false);
      setLoading(false);
    }
  };

  if (checking || !formData.eligibility) {
    return (
      <Card className="mx-auto max-w-2xl">
        <div className="flex flex-col items-center justify-center py-16">
          <Spinner className="mb-4" />
          <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
            Checking your eligibility...
          </p>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            This will only take a moment
          </p>
        </div>
      </Card>
    );
  }

  const { eligibility, flightStatus } = formData;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Eligibility Result */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Eligibility Result</CardTitle>
              <CardDescription>Based on {eligibility.regulation} regulations</CardDescription>
            </div>
            {eligibility.eligible ? (
              <CheckCircle className="h-12 w-12 text-green-600" />
            ) : (
              <XCircle className="h-12 w-12 text-red-600" />
            )}
          </div>
        </CardHeader>

        <div className="space-y-4">
          {eligibility.eligible ? (
            <div className="rounded-lg bg-green-50 p-6 dark:bg-green-900/20">
              <h3 className="text-lg font-semibold text-green-900 dark:text-green-100">
                Good news! You're eligible for compensation
              </h3>
              <p className="mt-2 text-3xl font-bold text-green-700 dark:text-green-400">
                {formatCurrency(eligibility.compensationAmount, eligibility.currency)}
              </p>
              <p className="mt-1 text-sm text-green-700 dark:text-green-300">
                Estimated compensation under {eligibility.regulation}
              </p>
            </div>
          ) : (
            <div className="rounded-lg bg-red-50 p-6 dark:bg-red-900/20">
              <h3 className="text-lg font-semibold text-red-900 dark:text-red-100">
                Unfortunately, this flight may not be eligible
              </h3>
              <p className="mt-2 text-sm text-red-700 dark:text-red-300">
                You can still submit your claim, and we'll review it manually.
              </p>
            </div>
          )}

          {/* Reasons */}
          {eligibility.reasons && eligibility.reasons.length > 0 && (
            <div>
              <h4 className="mb-2 font-medium text-gray-900 dark:text-gray-100">
                Why {eligibility.eligible ? "you're eligible" : 'this may not qualify'}:
              </h4>
              <ul className="space-y-2">
                {eligibility.reasons.map((reason, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-gray-500" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {reason}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Requirements */}
          {eligibility.requirements && eligibility.requirements.length > 0 && (
            <div>
              <h4 className="mb-2 font-medium text-gray-900 dark:text-gray-100">
                Required documents:
              </h4>
              <ul className="space-y-2">
                {eligibility.requirements.map((req, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-primary-600" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">{req}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </Card>

      {/* Flight Details */}
      {flightStatus && (
        <Card>
          <CardHeader>
            <CardTitle>Flight Details</CardTitle>
          </CardHeader>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Plane className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    {flightStatus.airline} {flightStatus.flightNumber}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(flightStatus.departureDate)}
                  </p>
                </div>
              </div>
              <Badge variant={flightStatus.status === 'delayed' ? 'warning' : 'info'}>
                {flightStatus.status}
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <MapPin className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    {flightStatus.departureAirport} → {flightStatus.arrivalAirport}
                  </p>
                </div>
              </div>
            </div>

            {flightStatus.delayMinutes && flightStatus.delayMinutes > 0 && (
              <div className="flex items-center space-x-3">
                <Clock className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    Delay: {formatDelay(flightStatus.delayMinutes)}
                  </p>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={previousStep}>
          Back
        </Button>
        <Button onClick={nextStep} disabled={loading}>
          Continue to Passenger Info
        </Button>
      </div>
    </div>
  );
}
