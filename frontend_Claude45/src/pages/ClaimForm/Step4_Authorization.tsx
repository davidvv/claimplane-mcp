/**
 * Step 4: Authorization (POA Signature)
 *
 * Collects digital signature for Power of Attorney.
 * Supports both drawn signature and typed name options.
 */

import { useState, useRef, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Check, PenTool, Type, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

import apiClient from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Label } from '@/components/ui/Label';
import { Input } from '@/components/ui/Input';
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
  consentPrivacy: z.boolean().refine(val => val === true, "You must accept the Privacy Policy"),
  consentElectronicSignature: z.boolean().refine(val => val === true, "You must consent to use an electronic signature"),
  consentRepresentAll: z.boolean().optional(),
  typedSignature: z.string().optional(),
});

type AuthorizationForm = z.infer<typeof authorizationSchema>;
type SignatureType = 'draw' | 'type';

interface Step4Props {
  flightData: any;
  passengerData: any;
  claimId?: string | null;
  onComplete: () => void;
  onBack: () => void;
}

// Generate signature image from typed text
function generateSignatureImage(typedName: string): string {
  const canvas = document.createElement('canvas');
  canvas.width = 600;
  canvas.height = 150;
  const ctx = canvas.getContext('2d');
  
  if (!ctx) return '';
  
  // White background
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  // Draw signature text in cursive style
  ctx.font = 'italic 48px "Brush Script MT", "Lucida Handwriting", cursive';
  ctx.fillStyle = '#1a1a1a';
  ctx.textBaseline = 'middle';
  
  // Center the text
  const textMetrics = ctx.measureText(typedName);
  const x = (canvas.width - textMetrics.width) / 2;
  const y = canvas.height / 2;
  
  ctx.fillText(typedName, x, y);
  
  // Add underline
  ctx.beginPath();
  ctx.moveTo(x, y + 25);
  ctx.lineTo(x + textMetrics.width, y + 25);
  ctx.strokeStyle = '#1a1a1a';
  ctx.lineWidth = 2;
  ctx.stroke();
  
  return canvas.toDataURL('image/png');
}

export function Step4_Authorization({
  flightData,
  passengerData,
  claimId,
  onComplete,
  onBack,
}: Step4Props) {
  const [signatureType, setSignatureType] = useState<SignatureType>('draw');
  const [signatureData, setSignatureData] = useState<string | null>(null);
  const [typedSignature, setTypedSignature] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showTypedWarning, setShowTypedWarning] = useState(false);

  const { handleSubmit, formState: { errors }, watch, setValue } = useForm<AuthorizationForm>({
    resolver: zodResolver(authorizationSchema),
    defaultValues: {
      consentTerms: false,
      consentPrivacy: false,
      consentElectronicSignature: false,
      consentRepresentAll: false,
      typedSignature: ''
    }
  });

  // Determine if multi-passenger
  const passengers = passengerData.passengers || [];
  const isMultiPassenger = passengers.length > 1;
  const primaryPassengerName = passengers[0] 
    ? `${passengers[0].firstName || ''} ${passengers[0].lastName || ''}`.trim() || 'Primary Passenger'
    : 'Primary Passenger';

  // Update signature data when typed signature changes
  useEffect(() => {
    if (signatureType === 'type' && typedSignature.trim().length >= 2) {
      const generatedSignature = generateSignatureImage(typedSignature.trim());
      setSignatureData(generatedSignature);
    } else if (signatureType === 'type' && typedSignature.trim().length < 2) {
      setSignatureData(null);
    }
  }, [typedSignature, signatureType]);

  const onSubmit = async (data: AuthorizationForm) => {
    if (!signatureData) {
      toast.error(signatureType === 'draw' 
        ? "Please sign the Power of Attorney to continue" 
        : "Please type your full name to continue");
      return;
    }
    
    // Validate signature based on type
    if (signatureType === 'draw') {
      // Base64 PNG of a real signature should be at least ~1KB
      const MIN_SIGNATURE_SIZE = 1000;
      if (signatureData.length < MIN_SIGNATURE_SIZE) {
        toast.error("Please provide a more complete signature");
        return;
      }
    } else {
      // Typed signature validation
      if (typedSignature.trim().length < 2) {
        toast.error("Please type your full name");
        return;
      }
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
      await apiClient.post(`/claims/${claimId}/sign-poa`, {
        signature_image: signatureData,
        signer_name: signatureType === 'type' ? typedSignature.trim() : primaryPassengerName,
        is_primary_passenger: true,
        consent_terms: data.consentTerms,
        consent_privacy_policy: data.consentPrivacy,
        consent_electronic_signature: data.consentElectronicSignature,
        consent_represent_all: data.consentRepresentAll,
        region: 'US',
        document_type: 'claim_assignment',
        signature_type: signatureType // Add signature type for backend tracking
      });

      toast.success("Authorization signed successfully");
      setIsSubmitting(false);
      onComplete();
    } catch (error) {
      console.error("Failed to sign POA:", error);
      toast.error("Failed to save signature. Please try again.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PenTool className="w-5 h-5 text-primary" />
            Claim Assignment & Service Agreement
          </CardTitle>
          <CardDescription>
            To legally represent you against the airline, we need your signature on the Claim Assignment and Service Agreement.
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

          <div className="text-sm space-y-2">
            <p>
              By signing below, I authorize ClaimPlane to act as my representative to claim compensation 
              for the flight irregularity described above. I hereby assign to ClaimPlane the proceeds of any 
              settlement or judgment resulting from this claim.
            </p>
            <p>
              I understand that under the DOT 2024 Final Rule, airlines may issue refunds directly to my 
              original form of payment. In such cases, I agree to reimburse ClaimPlane for their agreed 
              success fee within 7 days of receipt of funds.
            </p>
            <p>
              <a href="#" className="text-primary underline hover:text-primary/80" onClick={(e) => e.preventDefault()}>
                View full Assignment Agreement
              </a>
            </p>
          </div>

          {/* Signature Type Toggle */}
          <div className="space-y-3">
            <Label className="text-base font-semibold">Choose Signature Method</Label>
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => {
                  setSignatureType('draw');
                  setSignatureData(null);
                  setTypedSignature('');
                  setShowTypedWarning(false);
                }}
                className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border-2 transition-all ${
                  signatureType === 'draw'
                    ? 'border-primary bg-primary/5 text-primary'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <PenTool className="w-5 h-5" />
                <span className="font-medium">Draw Signature</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setSignatureType('type');
                  setSignatureData(null);
                  setShowTypedWarning(true);
                }}
                className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border-2 transition-all ${
                  signatureType === 'type'
                    ? 'border-primary bg-primary/5 text-primary'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <Type className="w-5 h-5" />
                <span className="font-medium">Type Name</span>
              </button>
            </div>
          </div>

          {/* Typed Signature Warning */}
          {showTypedWarning && signatureType === 'type' && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800">
                <p className="font-semibold mb-1">Important Notice</p>
                <p>
                  While typing your name is legally valid, some airlines may request a handwritten signature 
                  for verification purposes. If this occurs, we will contact you to provide a drawn signature. 
                  For faster processing, we recommend using the "Draw Signature" option.
                </p>
              </div>
            </div>
          )}

          {/* Signature Input Area */}
          <div className="space-y-2">
            <Label>
              {signatureType === 'draw' ? 'Your Signature' : 'Type Your Full Name'}
            </Label>
            
            {signatureType === 'draw' ? (
              <SignaturePad 
                onSignatureChange={setSignatureData} 
                className="w-full"
              />
            ) : (
              <div className="space-y-3">
                <Input
                  type="text"
                  placeholder="Type your full name as it appears on your ID"
                  value={typedSignature}
                  onChange={(e) => setTypedSignature(e.target.value)}
                  className="text-lg"
                />
                {signatureData && typedSignature.trim().length >= 2 && (
                  <div className="border rounded-lg p-4 bg-white">
                    <p className="text-xs text-muted-foreground mb-2">Preview:</p>
                    <img 
                      src={signatureData} 
                      alt="Generated signature" 
                      className="max-h-24 w-auto"
                    />
                  </div>
                )}
              </div>
            )}
            
            {signatureData && (
              <p className="text-xs text-green-600 flex items-center">
                <Check className="w-3 h-3 mr-1" /> 
                {signatureType === 'draw' ? 'Signature captured' : 'Name captured'}
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
                  I agree to the <a href="/terms" className="underline text-primary" target="_blank" rel="noopener noreferrer">Terms and Conditions</a>.
                </Label>
                {errors.consentTerms && (
                  <p className="text-xs text-destructive">{errors.consentTerms.message}</p>
                )}
              </div>
            </div>

            <div className="flex items-start space-x-2">
              <Checkbox 
                id="consentPrivacy" 
                checked={!!watch('consentPrivacy')}
                onCheckedChange={(checked) => setValue('consentPrivacy', checked as boolean)}
              />
              <div className="grid gap-1.5 leading-none">
                <Label htmlFor="consentPrivacy" className="cursor-pointer">
                  I have read and agree to the <a href="/privacy" className="underline text-primary" target="_blank" rel="noopener noreferrer">Privacy Policy</a> and consent to the processing of my data.
                </Label>
                {errors.consentPrivacy && (
                  <p className="text-xs text-destructive">{errors.consentPrivacy.message}</p>
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
                  I agree to use an electronic signature for this Assignment Agreement and understand it has the same legal validity as a handwritten signature.
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
