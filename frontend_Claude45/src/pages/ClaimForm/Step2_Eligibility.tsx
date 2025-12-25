/**
 * Step 2: Eligibility Check
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { CheckCircle, XCircle, Mail, Euro } from 'lucide-react';
import { toast } from 'sonner';

import { eligibilityFormSchema, type EligibilityForm } from '@/schemas/validation';
import { checkEligibility } from '@/services/eligibility';
import type { FlightStatus, EligibilityResponse } from '@/types/api';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { formatCurrency } from '@/lib/utils';

interface Step2Props {
  flightData: FlightStatus;
  initialData: EligibilityResponse | null;
  onComplete: (data: EligibilityResponse, email: string) => void;
  onBack: () => void;
}

export function Step2_Eligibility({
  flightData,
  initialData,
  onComplete,
  onBack,
}: Step2Props) {
  const [isLoading, setIsLoading] = useState(false);
  const [eligibilityResult, setEligibilityResult] = useState<EligibilityResponse | null>(
    initialData
  );
  const [submittedEmail, setSubmittedEmail] = useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EligibilityForm>({
    resolver: zodResolver(eligibilityFormSchema),
    defaultValues: {
      region: 'EU',
    },
  });

  const onSubmit = async (data: EligibilityForm) => {
    setIsLoading(true);

    try {
      const result = await checkEligibility({
        flightInfo: flightData,
        customerInfo: {
          email: data.email,
          region: data.region,
        },
      });

      setEligibilityResult(result);
      setSubmittedEmail(data.email);

      if (result.eligible) {
        toast.success('Great news! You are eligible for compensation.');
      } else {
        toast.error('Unfortunately, this flight is not eligible for compensation.');
      }
    } catch (error: any) {
      toast.error('Error checking eligibility. Please try again.');
      console.error('Eligibility check error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinue = () => {
    if (eligibilityResult?.eligible && submittedEmail) {
      onComplete(eligibilityResult, submittedEmail);
    } else {
      toast.error('You must be eligible to continue with the claim.');
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            Check Eligibility
          </CardTitle>
          <CardDescription>
            Let's verify if you're eligible for compensation
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="your@email.com"
                    className="pl-10"
                    {...register('email')}
                  />
                </div>
                {errors.email && (
                  <p className="text-sm text-destructive">{errors.email.message}</p>
                )}
              </div>

              {/* Region */}
              <div className="space-y-2">
                <Label htmlFor="region">Your Region</Label>
                <select
                  id="region"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  {...register('region')}
                >
                  <option value="EU">🇪🇺 European Union</option>
                  <option value="US">🇺🇸 United States</option>
                  <option value="CA">🇨🇦 Canada</option>
                </select>
                {errors.region && (
                  <p className="text-sm text-destructive">{errors.region.message}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Select the region where your flight originated or was destined
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onBack}>
                Back
              </Button>
              <Button type="submit" disabled={isLoading} className="flex-1">
                {isLoading ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Checking...
                  </>
                ) : (
                  'Check Eligibility'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Eligibility Result */}
      {eligibilityResult && (
        <Card className="fade-in">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {eligibilityResult.eligible ? (
                <>
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  Eligible for Compensation
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-red-600" />
                  Not Eligible
                </>
              )}
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            {eligibilityResult.eligible ? (
              <>
                {/* Compensation Amount */}
                {eligibilityResult.compensationAmount != null && (
                  <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-6 text-center">
                    <Euro className="w-12 h-12 mx-auto mb-2 text-green-600" />
                    <p className="text-sm text-muted-foreground mb-1">
                      Estimated Compensation
                    </p>
                    <p className="text-4xl font-bold text-green-600">
                      {formatCurrency(
                        eligibilityResult.compensationAmount,
                        eligibilityResult.currency
                      )}
                    </p>
                    {eligibilityResult.regulation && (
                      <p className="text-sm text-muted-foreground mt-2">
                        Under {eligibilityResult.regulation} regulation
                      </p>
                    )}
                  </div>
                )}

                {/* Reasons */}
                {eligibilityResult.reasons && eligibilityResult.reasons.length > 0 && (
                  <div>
                    <p className="font-semibold mb-2">Eligibility Reasons:</p>
                    <ul className="space-y-1">
                      {eligibilityResult.reasons.map((reason, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <CheckCircle className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Requirements */}
                {eligibilityResult.requirements &&
                  eligibilityResult.requirements.length > 0 && (
                    <div className="border-t pt-4">
                      <p className="font-semibold mb-2">Required Documents:</p>
                      <ul className="space-y-1">
                        {eligibilityResult.requirements.map((req, index) => (
                          <li key={index} className="flex items-start gap-2 text-sm">
                            <span className="text-muted-foreground">•</span>
                            <span>{req}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                <Button onClick={handleContinue} className="w-full">
                  Continue to Passenger Information
                </Button>
              </>
            ) : (
              <>
                {/* Not eligible reasons */}
                {eligibilityResult.reasons && eligibilityResult.reasons.length > 0 && (
                  <div>
                    <p className="font-semibold mb-2">Reasons:</p>
                    <ul className="space-y-1">
                      {eligibilityResult.reasons.map((reason, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <XCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="bg-muted rounded-lg p-4">
                  <p className="text-sm">
                    Unfortunately, this flight does not qualify for compensation under
                    current regulations. This could be due to extraordinary
                    circumstances, flight distance, or delay duration.
                  </p>
                </div>

                <Button variant="outline" onClick={onBack} className="w-full">
                  Try Another Flight
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
