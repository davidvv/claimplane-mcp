/**
 * Step 2: Eligibility Check
 *
 * Workflow v2: When user clicks "Continue", we create a draft claim
 * to enable progressive file uploads and abandoned cart recovery.
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { CheckCircle, XCircle, Mail, Euro } from 'lucide-react';
import { toast } from 'sonner';

import { eligibilityFormSchema, type EligibilityForm } from '@/schemas/validation';
import { checkEligibility } from '@/services/eligibility';
import { deleteClaim } from '@/services/claims';
import apiClient from '@/services/api';
import type { FlightStatus, EligibilityResponse } from '@/types/api';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { formatCurrency } from '@/lib/utils';

// Draft claim data returned from /claims/draft endpoint
interface DraftClaimData {
  claimId: string;
  customerId: string;
  accessToken: string;
  compensationAmount?: number;
  currency?: string;
}

interface Step2Props {
  flightData: FlightStatus;
  initialData: EligibilityResponse | null;
  draftClaimId: string | null;
  boardingPassFile?: File | null;
  ocrFileId?: string | null;
  onComplete: (data: EligibilityResponse, email: string, draftData?: DraftClaimData) => void;
  onBack: () => void;
  onDraftCancelled: () => void;
}

export function Step2_Eligibility({
  flightData,
  initialData,
  draftClaimId,
  boardingPassFile: _boardingPassFile,
  ocrFileId,
  onComplete,
  onBack,
  onDraftCancelled,
}: Step2Props) {
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingDraft, setIsCreatingDraft] = useState(false);
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
  });

  const onSubmit = async (data: EligibilityForm) => {
    setIsLoading(true);

    try {
      const result = await checkEligibility({
        flightInfo: flightData,
        customerInfo: {
          email: data.email,
          region: 'EU',  // Default to EU for EU261 regulation
        },
      });

      setEligibilityResult(result);
      setSubmittedEmail(data.email);

      // If user is NOT eligible and has a draft claim, delete it to prevent "abandoned claim" reminders
      if (!result.eligible && draftClaimId) {
        try {
          console.log(`Deleting ineligible draft claim: ${draftClaimId}`);
          await deleteClaim(draftClaimId);
          onDraftCancelled();
        } catch (error) {
          console.error('Failed to delete ineligible draft claim:', error);
          // Non-blocking error
        }
      }

      // Determine if we're using fallback data
      const isFallback = flightData.dataSource === 'mock';

      if (result.eligible) {
        if (isFallback || result.requirements?.includes('Manual review required')) {
          // Fallback scenario - manual review
          toast.success('Claim accepted! Our experts will review your case.');
        } else if (result.compensationAmount && result.compensationAmount > 0) {
          // API success with compensation
          toast.success('Great news! You are eligible for compensation.');
        } else {
          // Edge case: eligible but no amount
          toast.success('Your claim has been accepted for review.');
        }
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

  const handleContinue = async () => {
    if (!eligibilityResult?.eligible || !submittedEmail) {
      toast.error('You must be eligible to continue with the claim.');
      return;
    }

    setIsCreatingDraft(true);

    try {
      // Create draft claim (Workflow v2)
      // Ensure date is YYYY-MM-DD
      const depDate = flightData.departureDate || flightData.scheduledDeparture?.split('T')[0];
      const formattedDate = depDate?.includes('T') ? depDate.split('T')[0] : depDate;

      const response = await apiClient.post('/claims/draft', {
        email: submittedEmail,
        flightInfo: {
          flightNumber: flightData.flightNumber,
          airline: flightData.airline,
          departureDate: formattedDate,
          departureAirport: flightData.departureAirport,
          arrivalAirport: flightData.arrivalAirport,
        },
        incidentType: flightData.status === 'cancelled' ? 'cancellation' : 'delay',
        compensationAmount: eligibilityResult.compensationAmount,
        currency: eligibilityResult.currency || 'EUR',
        boardingPassFileId: ocrFileId,
      });

      const draftData: DraftClaimData = {
        claimId: response.data.claimId,
        customerId: response.data.customerId,
        accessToken: response.data.accessToken,
        compensationAmount: response.data.compensationAmount,
        currency: response.data.currency,
      };

      console.log('Draft claim created:', draftData.claimId);

      // Note: Boarding pass is now linked by the backend automatically 
      // if boardingPassFileId was provided in the draft creation request.
      
      onComplete(eligibilityResult, submittedEmail, draftData);

    } catch (error: any) {
      console.error('Failed to create draft claim:', error);
      const errorDetail = error.response?.data?.detail;
      const errorMsg = typeof errorDetail === 'string' ? errorDetail : 'Failed to save draft. Please try again.';
      toast.error(errorMsg);
      // WP-306: Block user if backend save fails (prevents XSS etc.)
    } finally {
      setIsCreatingDraft(false);
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
              <p className="text-xs text-muted-foreground">
                We'll use this to send you updates about your claim
              </p>
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
      {eligibilityResult && (() => {
        const isFallback = flightData.dataSource === 'mock';
        const requiresManualReview = eligibilityResult.requirements?.includes('Manual review required');
        const hasCompensation = eligibilityResult.compensationAmount && eligibilityResult.compensationAmount > 0;

        return (
          <Card className="fade-in">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {eligibilityResult.eligible ? (
                  <>
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    {hasCompensation && !isFallback && !requiresManualReview
                      ? 'Eligible for Compensation'
                      : 'Claim Accepted for Review'}
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
                  {/* Scenario 1: API Success with Compensation > 0 */}
                  {hasCompensation && !isFallback && !requiresManualReview && (
                    <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-6 text-center">
                      <Euro className="w-12 h-12 mx-auto mb-2 text-green-600" />
                      <p className="text-sm text-muted-foreground mb-1">
                        Expected Compensation
                      </p>
                      <p className="text-4xl font-bold text-green-600">
                        {formatCurrency(
                          eligibilityResult.compensationAmount ?? 0,
                          eligibilityResult.currency
                        )}
                      </p>
                      {eligibilityResult.regulation && (
                        <p className="text-sm text-muted-foreground mt-2">
                          Under {eligibilityResult.regulation} regulation
                        </p>
                      )}
                      <p className="text-sm text-muted-foreground mt-3">
                        This is the amount you can expect to receive based on your flight's distance and delay.
                      </p>
                    </div>
                  )}

                  {/* Scenario 2: Compensation = 0 (not eligible but still accepted) */}
                  {!hasCompensation && eligibilityResult.compensationAmount === 0 && (
                    <div className="bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
                      <p className="text-sm font-semibold mb-2">No Compensation Available</p>
                      <p className="text-sm text-muted-foreground">
                        Based on your flight details, this claim does not qualify for compensation.
                        This is typically due to the delay being less than 3 hours, or the incident
                        type not being covered under EU261/2004 regulations.
                      </p>
                    </div>
                  )}

                  {/* Scenario 3: Fallback / Manual Review Required */}
                  {(isFallback || requiresManualReview) && (
                    <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
                      <p className="text-sm font-semibold mb-2">Expert Review Required</p>
                      <p className="text-sm text-muted-foreground mb-3">
                        We couldn't automatically calculate your compensation amount. Our expert team
                        will review your flight details and assess your eligibility based on EU261/2004
                        regulations.
                      </p>
                      <p className="text-sm text-muted-foreground">
                        You'll receive a notification within 2-4 business days with the final assessment
                        and expected compensation amount.
                      </p>
                    </div>
                  )}

                  {/* Reasons */}
                  {eligibilityResult.reasons && eligibilityResult.reasons.length > 0 && (
                    <div>
                      <p className="font-semibold mb-2">Details:</p>
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

                  {/* Continue Button */}
                  <Button 
                    onClick={handleContinue} 
                    className="w-full"
                    disabled={isCreatingDraft}
                  >
                    {isCreatingDraft ? (
                      <>
                        <LoadingSpinner size="sm" className="mr-2" />
                        Saving...
                      </>
                    ) : (
                      'Continue to Passenger Information'
                    )}
                  </Button>
                </>
              ) : (
                <>
                  {/* Not Eligible - Show Thank You Message */}
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
                    <p className="text-sm font-semibold mb-2">
                      Thank you for considering ClaimPlane
                    </p>
                    <p className="text-sm">
                      Unfortunately, this flight does not qualify for compensation under
                      EU261/2004 regulations. We appreciate your interest and hope we can
                      assist you with future claims.
                    </p>
                  </div>

                  <Button variant="outline" onClick={onBack} className="w-full">
                    Try Another Flight
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        );
      })()}
    </div>
  );
}
