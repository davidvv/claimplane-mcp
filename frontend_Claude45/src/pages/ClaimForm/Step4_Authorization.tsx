/**
 * Step 4: Authorization (POA Signature)
 *
 * Collects digital signature for Power of Attorney.
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Check, PenTool } from 'lucide-react';
import { toast } from 'sonner';

import apiClient from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Label } from '@/components/ui/Label';
import { SignaturePad } from '@/components/SignaturePad';
import { LoadingOverlay } from '@/components/LoadingSpinner';

// Checkbox Component (inline fallback since UI lib is missing it)
function Checkbox({ id, checked, onCheckedChange, disabled }: { id: string, checked: boolean, onCheckedChange: (checked: boolean) => void, disabled?: boolean }) {
  return (
    <input
      type="checkbox"
      id={id}
      checked={checked}
      onChange={(e) => onCheckedChange(e.target.checked)}
      disabled={disabled}
      className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
    />
  );
}

// Schema for the authorization form
const authorizationSchema = z.object({
  consentTerms: z.boolean().refine(val => val === true, "You must accept the Terms and Conditions"),
  consentElectronicSignature: z.boolean().refine(val => val === true, "You must consent to use an electronic signature"),
  consentRepresentAll: z.boolean().optional(),
});

type AuthorizationForm = z.infer<typeof authorizationSchema>;

interface Step4Props {
  flightData: any;
  passengerData: any;
  claimId?: string | null;
  onComplete: () => void;
  onBack: () => void;
}

export function Step4_Authorization({
  flightData,
  passengerData,
  claimId,
  onComplete,
  onBack,
}: Step4Props) {
  const [signatureData, setSignatureData] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { handleSubmit, formState: { errors }, watch, setValue } = useForm<AuthorizationForm>({
    resolver: zodResolver(authorizationSchema),
    defaultValues: {
      consentTerms: false,
      consentElectronicSignature: false,
      consentRepresentAll: false
    }
  });

  // Determine if multi-passenger
  const passengers = passengerData.passengers || [];
  const isMultiPassenger = passengers.length > 1;
  const primaryPassengerName = passengers[0]?.firstName + ' ' + passengers[0]?.lastName;

  const onSubmit = async (data: AuthorizationForm) => {
    if (!signatureData) {
      toast.error("Please sign the Power of Attorney to continue");
      return;
    }

    if (!claimId) {
      toast.error("Error: No claim ID found. Please go back and try again.");
      return;
    }

    if (isMultiPassenger && !data.consentRepresentAll) {
      toast.error("Please confirm you are authorized to represent all passengers");
      return;
    }

    setIsSubmitting(true);

    try {
      console.log('Sending signature to backend, length:', finalSignature.length);
      // 1. Send signature to backend
      await apiClient.post(`/claims/${claimId}/sign-poa`, {
        signature_image: finalSignature,
        signer_name: primaryPassengerName,
        is_primary_passenger: true,
        consent_terms: data.consentTerms,
        consent_electronic_signature: data.consentElectronicSignature,
        consent_represent_all: data.consentRepresentAll
      });

      toast.success("Authorization signed successfully");
      onComplete();
    } catch (error) {
      console.error("Failed to sign POA:", error);
      toast.error("Failed to save signature. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PenTool className="w-5 h-5 text-primary" />
            Sign Power of Attorney
          </CardTitle>
          <CardDescription>
            To legally represent you against the airline, we need your signature on the Power of Attorney.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          
          {/* Summary Box */}
          <div className="bg-muted/30 p-4 rounded-lg text-sm border border-border">
            <p className="font-semibold mb-2">Claim Summary:</p>
            <ul className="space-y-1 text-muted-foreground">
              <li>Flight: <span className="text-foreground">{flightData.airline} {flightData.flightNumber}</span></li>
              <li>Date: <span className="text-foreground">{new Date(flightData.departureDate).toLocaleDateString()}</span></li>
              <li>Primary Passenger: <span className="text-foreground">{primaryPassengerName}</span></li>
              {isMultiPassenger && (
                <li>Additional Passengers: <span className="text-foreground">{passengers.length - 1}</span></li>
              )}
            </ul>
          </div>

          <div className="space-y-4">
            <div className="text-sm space-y-2">
              <p>
                By signing below, I authorize EasyAirClaim to act as my legal representative to claim compensation 
                for the flight irregularity described above. This includes the authority to negotiate with the airline, 
                submit claims, and receive payments on my behalf.
              </p>
              <p>
                <a href="#" className="text-primary underline hover:text-primary/80" onClick={(e) => e.preventDefault()}>
                  View full Power of Attorney document
                </a>
              </p>
            </div>

            {/* Signature Pad */}
            <div className="space-y-2">
              <Label>Your Signature</Label>
              <SignaturePad 
                onSignatureChange={setSignatureData} 
                className="w-full"
              />
              {signatureData && (
                <p className="text-xs text-green-600 flex items-center">
                  <Check className="w-3 h-3 mr-1" /> Signature captured
                </p>
              )}
            </div>

            {/* Checkboxes */}
            <div className="space-y-3 pt-2">
              <div className="flex items-start space-x-2">
                <Checkbox 
                  id="consentTerms" 
                  checked={!!watch('consentTerms')}
                  onCheckedChange={(checked) => setValue('consentTerms', checked as boolean)}
                />
                <div className="grid gap-1.5 leading-none">
                  <Label htmlFor="consentTerms" className="cursor-pointer">
                    I agree to the <a href="/terms" className="underline text-primary">Terms and Conditions</a> and <a href="/privacy" className="underline text-primary">Privacy Policy</a>.
                  </Label>
                  {errors.consentTerms && (
                    <p className="text-xs text-destructive">{errors.consentTerms.message}</p>
                  )}
                </div>
              </div>

              <div className="flex items-start space-x-2">
                <Checkbox 
                  id="consentElectronicSignature" 
                  checked={!!watch('consentElectronicSignature')}
                  onCheckedChange={(checked) => setValue('consentElectronicSignature', checked as boolean)}
                />
                <div className="grid gap-1.5 leading-none">
                  <Label htmlFor="consentElectronicSignature" className="cursor-pointer">
                    I agree to use an electronic signature for this Power of Attorney and understand it has the same legal validity as a handwritten signature.
                  </Label>
                  {errors.consentElectronicSignature && (
                    <p className="text-xs text-destructive">{errors.consentElectronicSignature.message}</p>
                  )}
                </div>
              </div>

              {isMultiPassenger && (
                <div className="flex items-start space-x-2">
                  <Checkbox 
                    id="consentRepresentAll" 
                    checked={!!watch('consentRepresentAll')}
                    onCheckedChange={(checked) => setValue('consentRepresentAll', checked as boolean)}
                  />
                  <div className="grid gap-1.5 leading-none">
                    <Label htmlFor="consentRepresentAll" className="cursor-pointer">
                      I confirm I am authorized to sign on behalf of all passengers listed in this claim.
                    </Label>
                    {errors.consentRepresentAll && (
                      <p className="text-xs text-destructive">{errors.consentRepresentAll.message}</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onBack}
              disabled={isSubmitting}
            >
              Back
            </Button>
            <Button
              onClick={handleSubmit(onSubmit)}
              disabled={isSubmitting}
              className="bg-primary text-white"
            >
              {isSubmitting ? 'Signing...' : 'Sign & Continue'}
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {isSubmitting && <LoadingOverlay message="Generating signed document..." />}
    </div>
  );
}
