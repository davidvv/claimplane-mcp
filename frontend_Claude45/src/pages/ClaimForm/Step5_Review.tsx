/**
 * Step 5: Review & Submit
 *
 * Workflow v2: If draftClaimId is provided, we finalize the existing
 * draft claim instead of creating a new one. Files are already uploaded.
 */

import { useState } from 'react';
import { CheckCircle, User, Plane, Euro, FileText, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

import { submitClaim } from '@/services/claims';
import { uploadDocument } from '@/services/documents';
import type { FlightStatus, EligibilityResponse, ClaimRequest } from '@/types/api';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LoadingOverlay } from '@/components/LoadingSpinner';
import { formatCurrency, getIncidentLabel } from '@/lib/utils';

interface Step5Props {
  flightData: FlightStatus;
  eligibilityData: EligibilityResponse;
  passengerData: any;
  documents: any[];
  draftClaimId?: string | null;  // Workflow v2: Draft claim ID to finalize
  onComplete: (claimId: string) => void;
  onBack: () => void;
}

export function Step5_Review({
  flightData,
  eligibilityData,
  passengerData,
  documents,
  draftClaimId,
  onComplete,
  onBack,
}: Step5Props) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentUploadFile, setCurrentUploadFile] = useState<string>('');
  // const [termsAccepted, setTermsAccepted] = useState(false); // Terms accepted in Step 4

  // Extract primary passenger for display (support both multi-passenger and legacy formats)
  const primaryPassenger = passengerData.passengers?.[0] || {
    firstName: passengerData.firstName || '',
    lastName: passengerData.lastName || '',
  };
  const allPassengers = passengerData.passengers || [primaryPassenger];

  const handleSubmit = async () => {
    // Validate terms acceptance (Moved to Step 4)
    // if (!termsAccepted) {
    //   toast.error('Please accept the terms and conditions to continue');
    //   return;
    // }

    setIsSubmitting(true);
    setUploadProgress(0);

    let claimId: string | null = null;

    try {
      // Extract primary passenger from passengers array (multi-passenger support)
      // Fall back to flat fields for backward compatibility
      const primaryPassenger = passengerData.passengers?.[0] || {
        firstName: passengerData.firstName,
        lastName: passengerData.lastName,
        ticketNumber: passengerData.ticketNumber,
      };

      // Step 1: Submit the claim
      const claimRequest: ClaimRequest = {
        customerInfo: {
          email: passengerData.email,
          firstName: primaryPassenger.firstName,
          lastName: primaryPassenger.lastName,
          phone: passengerData.phone || null,
          address: {
            street: passengerData.street,
            city: passengerData.city,
            postalCode: passengerData.postalCode,
            country: passengerData.country,
          },
        },
        flightInfo: {
          flightNumber: flightData.flightNumber,
          airline: flightData.airline,
          departureDate: flightData.departureDate,
          departureAirport: flightData.departureAirport,
          arrivalAirport: flightData.arrivalAirport,
          scheduledDeparture: flightData.scheduledDeparture,
          scheduledArrival: flightData.scheduledArrival,
          actualDeparture: flightData.actualDeparture,
          actualArrival: flightData.actualArrival,
          status: flightData.status,
          delayMinutes: flightData.delayMinutes,
        },
        incidentType: passengerData.incidentType,
        notes: passengerData.notes || null,
        bookingReference: passengerData.bookingReference || null,
        ticketNumber: primaryPassenger.ticketNumber || null,
        termsAccepted: true,
        // Workflow v2: Pass draft claim ID to finalize existing draft
        claimId: draftClaimId || undefined,
      };

      const claim = await submitClaim(claimRequest);
      claimId = claim.id!;
      toast.success('Claim submitted successfully!');

      // Step 2: Upload documents (only if we don't have a draft claim)
      // If draftClaimId exists, documents were already uploaded progressively
      let uploadErrors = 0;
      const failedFiles: string[] = [];

      if (!draftClaimId && documents.length > 0 && claim.id) {
        for (let i = 0; i < documents.length; i++) {
          const doc = documents[i];
          setCurrentUploadFile(doc.file.name);

          try {
            await uploadDocument(
              claim.id,
              doc.file,
              doc.documentType,
              (progressEvent: any) => {
                const percentCompleted = Math.round(
                  ((i + progressEvent.loaded / progressEvent.total) / documents.length) * 100
                );
                setUploadProgress(percentCompleted);
              }
            );
            console.log(`Successfully uploaded: ${doc.file.name}`);
          } catch (error: any) {
            console.error('Document upload error:', error);
            uploadErrors++;
            failedFiles.push(doc.file.name);

            // Check if it's a timeout error
            if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
              toast.error(`Upload timeout for ${doc.file.name}. File may be too large or connection too slow.`);
            } else {
              toast.error(`Failed to upload ${doc.file.name}: ${error.response?.data?.detail || error.message || 'Unknown error'}`);
            }
          }
        }
      }

      // Clear upload status
      setCurrentUploadFile('');
      setUploadProgress(0);

      // Show appropriate success/warning message
      if (documents.length > 0) {
        if (uploadErrors === 0) {
          toast.success('All documents uploaded successfully!');
        } else if (uploadErrors < documents.length) {
          toast.warning(
            `${documents.length - uploadErrors} of ${documents.length} documents uploaded. ` +
            `Failed: ${failedFiles.join(', ')}. You can upload them later from your claim details.`,
            { duration: 8000 }
          );
        } else {
          // All uploads failed
          toast.error(
            'All document uploads failed. Your claim was created, but you need to upload documents later from your claim details.',
            { duration: 10000 }
          );
        }
      }

      // Analytics tracking stub
      if (typeof window !== 'undefined' && (window as any).analytics) {
        (window as any).analytics.track('claim_submitted', {
          claimId: claim.id,
          compensationAmount: eligibilityData.compensationAmount,
          regulation: eligibilityData.regulation,
          incidentType: passengerData.incidentType,
          documentsUploaded: documents.length - uploadErrors,
          documentsFailed: uploadErrors,
        });
      }

      // Complete the wizard - navigate to success page
      // We navigate even if some uploads failed, but the user has been warned
      onComplete(claim.id!);
    } catch (error: any) {
      console.error('Claim submission error:', error);

      // Check if it's a timeout error
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        toast.error('Request timeout. Please try again or contact support if the issue persists.');
      } else {
        toast.error(
          error.response?.data?.error?.message ||
          error.response?.data?.detail ||
            'Failed to submit claim. Please try again.'
        );
      }

      // If claim was created but uploads failed, still allow navigation
      if (claimId) {
        const shouldNavigate = window.confirm(
          'Your claim was submitted but there were issues with document uploads. ' +
          'Would you like to view your claim now? You can upload documents later.'
        );
        if (shouldNavigate) {
          onComplete(claimId);
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {isSubmitting && (
        <LoadingOverlay
          message={
            currentUploadFile
              ? `Uploading ${currentUploadFile}... ${uploadProgress}%`
              : uploadProgress > 0
              ? `Uploading documents... ${uploadProgress}%`
              : 'Submitting your claim...'
          }
        />
      )}

      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Review Your Claim</h2>
          <p className="text-muted-foreground">
            Please review all information before submitting
          </p>
        </div>

        {/* Flight Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plane className="w-5 h-5" />
              Flight Information
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-3">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Flight Number</p>
                <p className="font-semibold">{flightData.flightNumber}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Airline</p>
                <p className="font-semibold">{flightData.airline}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Route</p>
                <p className="font-semibold">
                  {flightData.departureAirport} → {flightData.arrivalAirport}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Departure Date</p>
                <p className="font-semibold">{flightData.departureDate}</p>
              </div>
            </div>

            {flightData.delayMinutes && flightData.delayMinutes > 0 && (
              <div className="pt-3 border-t">
                <p className="text-sm text-muted-foreground">Delay Duration</p>
                <Badge variant="destructive" className="mt-1">
                  {flightData.delayMinutes} minutes
                </Badge>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Compensation */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Euro className="w-5 h-5" />
              Compensation Details
            </CardTitle>
          </CardHeader>

          <CardContent>
            <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-6 text-center">
              <p className="text-sm text-muted-foreground mb-1">
                Eligible Compensation Amount
              </p>
              <p className="text-4xl font-bold text-green-600">
                {formatCurrency(
                  eligibilityData.compensationAmount || 0,
                  eligibilityData.currency
                )}
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Under {eligibilityData.regulation} regulation
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Passenger Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              {allPassengers.length > 1 ? 'Passengers' : 'Your Information'}
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-3">
            {/* Show all passengers */}
            {allPassengers.length > 1 ? (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Passengers ({allPassengers.length})</p>
                <ul className="space-y-1">
                  {allPassengers.map((p: any, i: number) => (
                    <li key={i} className="font-semibold">
                      {i + 1}. {p.firstName} {p.lastName}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Name</p>
                  <p className="font-semibold">
                    {primaryPassenger.firstName} {primaryPassenger.lastName}
                  </p>
                </div>
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Email</p>
                <p className="font-semibold">{passengerData.email}</p>
              </div>
              {passengerData.phone && (
                <div>
                  <p className="text-sm text-muted-foreground">Phone</p>
                  <p className="font-semibold">{passengerData.phone}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-muted-foreground">Incident Type</p>
                <p className="font-semibold">
                  {getIncidentLabel(passengerData.incidentType)}
                </p>
              </div>
            </div>

            <div className="pt-3 border-t">
              <p className="text-sm text-muted-foreground">Address</p>
              <p className="font-semibold">
                {passengerData.street}, {passengerData.city},{' '}
                {passengerData.postalCode}, {passengerData.country}
              </p>
            </div>

            {passengerData.notes && (
              <div className="pt-3 border-t">
                <p className="text-sm text-muted-foreground">Additional Notes</p>
                <p className="text-sm">{passengerData.notes}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Documents */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Uploaded Documents
            </CardTitle>
          </CardHeader>

          <CardContent>
            {documents.length > 0 ? (
              <ul className="space-y-2">
                {documents.map((doc, index) => (
                  <li
                    key={index}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium text-sm">{doc.file.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {doc.documentType.replace('_', ' ')}
                        </p>
                      </div>
                    </div>
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <AlertCircle className="w-12 h-12 mx-auto mb-2" />
                <p>No documents uploaded</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Terms & Conditions (Already accepted in Step 4) */}
        {/* <Card>
          <CardContent className="pt-6">
            <div className="bg-muted rounded-lg p-4 text-sm">
              <p className="font-semibold mb-2">Terms & Conditions</p>
              ...
            </div>
          </CardContent>
        </Card> */}

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onBack}
            disabled={isSubmitting}
          >
            Back
          </Button>
          <Button
            onClick={handleSubmit}
            // disabled={isSubmitting || !termsAccepted} // Terms check removed
            disabled={isSubmitting}
            className="flex-1"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Claim'}
          </Button>
        </div>
      </div>
    </>
  );
}
