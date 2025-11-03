/**
 * Step 4: Review & Submit
 */

import { useState } from 'react';
import { CheckCircle, User, Plane, Euro, FileText, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

import { submitClaim } from '@/services/claims';
import { uploadDocument } from '@/services/documents';
import type { FlightStatus, EligibilityResponse, ClaimRequest } from '@/types/api';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LoadingOverlay } from '@/components/LoadingSpinner';
import { formatCurrency, formatDateTime, getIncidentLabel } from '@/lib/utils';

interface Step4Props {
  flightData: FlightStatus;
  eligibilityData: EligibilityResponse;
  passengerData: any;
  documents: any[];
  onComplete: (claimId: string) => void;
  onBack: () => void;
}

export function Step4_Review({
  flightData,
  eligibilityData,
  passengerData,
  documents,
  onComplete,
  onBack,
}: Step4Props) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setUploadProgress(0);

    try {
      // Step 1: Submit the claim
      const claimRequest: ClaimRequest = {
        customerInfo: {
          email: passengerData.email,
          firstName: passengerData.firstName,
          lastName: passengerData.lastName,
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
      };

      const claim = await submitClaim(claimRequest);
      toast.success('Claim submitted successfully!');

      // Step 2: Upload documents
      if (documents.length > 0 && claim.id) {
        for (let i = 0; i < documents.length; i++) {
          const doc = documents[i];
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
          } catch (error) {
            console.error('Document upload error:', error);
            toast.error(`Failed to upload ${doc.file.name}`);
          }
        }
      }

      toast.success('All documents uploaded!');

      // Analytics tracking stub
      if (typeof window !== 'undefined' && (window as any).analytics) {
        (window as any).analytics.track('claim_submitted', {
          claimId: claim.id,
          compensationAmount: eligibilityData.compensationAmount,
          regulation: eligibilityData.regulation,
          incidentType: passengerData.incidentType,
        });
      }

      // Complete the wizard
      onComplete(claim.id!);
    } catch (error: any) {
      console.error('Claim submission error:', error);
      toast.error(
        error.response?.data?.error?.message ||
          'Failed to submit claim. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {isSubmitting && (
        <LoadingOverlay
          message={
            uploadProgress > 0
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
              Your Information
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-3">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Name</p>
                <p className="font-semibold">
                  {passengerData.firstName} {passengerData.lastName}
                </p>
              </div>
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

        {/* Terms & Conditions */}
        <Card>
          <CardContent className="pt-6">
            <div className="bg-muted rounded-lg p-4 text-sm">
              <p className="font-semibold mb-2">Terms & Conditions</p>
              <p className="text-muted-foreground mb-2">
                By submitting this claim, you agree to our terms of service and
                authorize EasyAirClaim to act on your behalf in pursuing compensation
                from the airline.
              </p>
              <p className="text-muted-foreground">
                We operate on a "no win, no fee" basis. Our commission is 25% (+ VAT)
                of the compensation amount, deducted only upon successful claim.
              </p>
            </div>
          </CardContent>
        </Card>

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
