/**
 * Main claim form page with 4-step wizard
 *
 * Workflow v2: Draft claim is created at Step 2 after eligibility check.
 * This enables progressive file uploads and abandoned cart recovery.
 */

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Stepper } from '@/components/Stepper';
import { useClaimFormPersistence } from '@/hooks/useLocalStorageForm';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { isAuthenticated, getCurrentUser, type UserProfile, setAuthToken } from '@/services/auth';
import { getClaim } from '@/services/claims';
import { toast } from 'sonner';
import { Step1_Flight, type OCRData } from './Step1_Flight';
import { Step2_Eligibility } from './Step2_Eligibility';
import { Step3_Passenger } from './Step3_Passenger';
import { Step4_Review } from './Step4_Review';
import type { FlightStatus, EligibilityResponse } from '@/types/api';

const STEPS = [
  { number: 1, title: 'Flight', description: 'Flight details' },
  { number: 2, title: 'Eligibility', description: 'Check eligibility' },
  { number: 3, title: 'Information', description: 'Your details' },
  { number: 4, title: 'Review', description: 'Review & submit' },
];

// Draft claim data returned from /claims/draft endpoint
interface DraftClaimData {
  claimId: string;
  customerId: string;
  accessToken: string;
  compensationAmount?: number;
  currency?: string;
}

export function ClaimFormPage() {
  useDocumentTitle('File Claim');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const {
    formData,
    updateStep,
    updateFlightData,
    updateEligibilityData,
    updatePassengerData,
    updateDocuments,
    clearFormData,
  } = useClaimFormPersistence();

  const [currentStep, setCurrentStep] = useState(1);
  const [flightData, setFlightData] = useState<FlightStatus | null>(null);
  const [eligibilityData, setEligibilityData] = useState<EligibilityResponse | null>(null);
  const [customerEmail, setCustomerEmail] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [passengerData, setPassengerData] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  
  // OCR data from boarding pass upload
  const [ocrData, setOcrData] = useState<OCRData | null>(null);

  // Draft claim state (Workflow v2)
  const [draftClaimId, setDraftClaimId] = useState<string | null>(null);
  // Note: draftAccessToken is stored in localStorage via setAuthToken, not in state

  // Track if we're resuming from magic link (to skip localStorage prompt)
  const [isResumingFromMagicLink, setIsResumingFromMagicLink] = useState(false);

  // Check for resume parameter (coming from reminder email)
  useEffect(() => {
    const resumeClaimId = searchParams.get('resume');
    if (resumeClaimId) {
      // Set flag to skip localStorage prompt
      setIsResumingFromMagicLink(true);

      // Clear any conflicting localStorage data
      clearFormData();
      localStorage.removeItem('draftClaimId');
      localStorage.removeItem('draftAccessToken');

      setDraftClaimId(resumeClaimId);

      // Fetch draft data to hydrate form
      const loadDraft = async () => {
        try {
          const claim = await getClaim(resumeClaimId);

          // Restore Flight Data
          const restoredFlight: FlightStatus = {
            id: claim.id || resumeClaimId, // Use claim ID or resume ID
            flightNumber: claim.flightInfo.flightNumber,
            airline: claim.flightInfo.airline,
            departureAirport: claim.flightInfo.departureAirport,
            arrivalAirport: claim.flightInfo.arrivalAirport,
            departureDate: claim.flightInfo.departureDate,
            // Map optional fields
            scheduledDeparture: (claim.flightInfo as any).scheduledDeparture,
            scheduledArrival: (claim.flightInfo as any).scheduledArrival,
            actualDeparture: (claim.flightInfo as any).actualDeparture,
            actualArrival: (claim.flightInfo as any).actualArrival,
            status: (claim.flightInfo as any).status || 'unknown',
            delayMinutes: (claim.flightInfo as any).delayMinutes,
            lastUpdated: new Date().toISOString(),
            dataSource: 'db',
          };
          setFlightData(restoredFlight);
          updateFlightData(restoredFlight);

          // Restore Eligibility Data
          const restoredEligibility: EligibilityResponse = {
            eligible: true,
            compensationAmount: claim.compensationAmount || 0,
            currency: claim.currency,
            regulation: 'EU261',
            reasons: [],
          };
          setEligibilityData(restoredEligibility);
          updateEligibilityData(restoredEligibility);

          // Restore Step
          setCurrentStep(3);

          toast.success("Draft claim loaded successfully from your email link!");

        } catch (error) {
          console.error("Failed to load draft:", error);
          toast.error("Could not load draft claim details.");
          setIsResumingFromMagicLink(false); // Allow localStorage prompt on error
        }
      };

      loadDraft();
    }
  }, [searchParams, clearFormData, updateFlightData, updateEligibilityData]);

  // Check for saved form data on mount (runs only once)
  useEffect(() => {
    // Skip localStorage prompt if we're resuming from magic link
    if (isResumingFromMagicLink) {
      return;
    }

    // Check if there's saved form data from a previous session
    const hasSavedData = formData.currentStep && formData.currentStep > 1;

    if (hasSavedData) {
      const shouldResume = window.confirm(
        `You have a claim in progress at step ${formData.currentStep}. Would you like to resume where you left off?\n\nClick OK to resume, or Cancel to start a new claim.`
      );

      if (shouldResume) {
        // Restore saved data
        setCurrentStep(formData.currentStep || 1);
        setFlightData(formData.flightData || null);
        setEligibilityData(formData.eligibilityData || null);
        setPassengerData(formData.passengerData || null);
        setDocuments(formData.documents || []);
        // Restore draft claim ID if saved
        if (formData.draftClaimId) {
          setDraftClaimId(formData.draftClaimId);
        }
        if (formData.draftAccessToken) {
          setAuthToken(formData.draftAccessToken);
        }
      } else {
        // Clear saved data and start fresh
        clearFormData();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isResumingFromMagicLink]); // Now depends on magic link flag

  // Fetch user profile if authenticated
  useEffect(() => {
    const fetchUserProfile = async () => {
      if (isAuthenticated()) {
        try {
          const profile = await getCurrentUser();
          // Only use profile for customers, not admins
          if (profile.role === 'customer') {
            setUserProfile(profile);
          }
        } catch (error) {
          console.log('Could not fetch user profile:', error);
          // Silently fail - user can still fill in the form manually
        }
      }
    };

    fetchUserProfile();
  }, []);

  // Sync with localStorage
  useEffect(() => {
    updateStep(currentStep);
  }, [currentStep]);

  // Scroll to top when step changes
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [currentStep]);

  const handleFlightComplete = (data: FlightStatus, ocrExtractedData?: OCRData) => {
    setFlightData(data);
    updateFlightData(data);
    
    // Store OCR data if provided
    if (ocrExtractedData) {
      setOcrData(ocrExtractedData);
    }
    
    setCurrentStep(2);
  };

  const handleEligibilityComplete = (
    data: EligibilityResponse,
    email: string,
    draftData?: DraftClaimData
  ) => {
    setEligibilityData(data);
    updateEligibilityData(data);
    setCustomerEmail(email);

    // Store draft claim data if provided (Workflow v2)
    if (draftData) {
      setDraftClaimId(draftData.claimId);
      // Set auth token for subsequent API calls (file uploads)
      setAuthToken(draftData.accessToken);
      // Persist to localStorage for page refresh recovery
      localStorage.setItem('draftClaimId', draftData.claimId);
      localStorage.setItem('draftAccessToken', draftData.accessToken);
    }

    setCurrentStep(3);
  };

  const handlePassengerComplete = (data: any, docs: any[]) => {
    setPassengerData(data);
    setDocuments(docs);
    updatePassengerData(data);
    updateDocuments(docs);
    setCurrentStep(4);
  };

  const handleSubmitComplete = (claimId: string) => {
    // Clear form data and draft claim data
    clearFormData();
    localStorage.removeItem('draftClaimId');
    localStorage.removeItem('draftAccessToken');
    // Navigate to success page
    navigate(`/claim/success?claimId=${claimId}`);
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStartNewClaim = () => {
    if (confirm('Are you sure you want to start a new claim? This will clear all current form data.')) {
      clearFormData();
      localStorage.removeItem('draftClaimId');
      localStorage.removeItem('draftAccessToken');
      setCurrentStep(1);
      setFlightData(null);
      setEligibilityData(null);
      setPassengerData(null);
      setDocuments([]);
      setDraftClaimId(null);
      setOcrData(null); // Clear OCR data
    }
  };

  return (
    <div className="py-12 md:py-20">
      <div className="container max-w-4xl">
        <div className="mb-12 text-center">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl md:text-4xl font-bold flex-1">
              File Your Compensation Claim
            </h1>
            {(flightData || currentStep > 1) && (
              <button
                onClick={handleStartNewClaim}
                className="text-sm text-muted-foreground hover:text-foreground underline"
              >
                Start New Claim
              </button>
            )}
          </div>
          <p className="text-muted-foreground">
            Complete the form below to submit your claim. Takes about 5 minutes.
          </p>
        </div>

        {/* Progress stepper */}
        <Stepper steps={STEPS} currentStep={currentStep} />

        {/* Step content */}
        <div className="mt-8">
          {currentStep === 1 && (
            <Step1_Flight
              initialData={flightData}
              onComplete={handleFlightComplete}
            />
          )}

          {currentStep === 2 && flightData && (
            <Step2_Eligibility
              flightData={flightData}
              initialData={eligibilityData}
              onComplete={handleEligibilityComplete}
              onBack={handleBack}
            />
          )}

          {currentStep === 3 && flightData && eligibilityData && (
            <Step3_Passenger
              flightData={flightData}
              eligibilityData={eligibilityData}
              initialData={passengerData}
              initialDocuments={documents}
              customerEmail={customerEmail}
              userProfile={userProfile}
              draftClaimId={draftClaimId}
              ocrData={ocrData} // Pass OCR data for pre-filling
              onComplete={handlePassengerComplete}
              onBack={handleBack}
            />
          )}

          {currentStep === 4 && flightData && eligibilityData && passengerData && (
            <Step4_Review
              flightData={flightData}
              eligibilityData={eligibilityData}
              passengerData={passengerData}
              documents={documents}
              draftClaimId={draftClaimId}
              onComplete={handleSubmitComplete}
              onBack={handleBack}
            />
          )}
        </div>
      </div>
    </div>
  );
}
