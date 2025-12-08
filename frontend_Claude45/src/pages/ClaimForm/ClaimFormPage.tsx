/**
 * Main claim form page with 4-step wizard
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Stepper } from '@/components/Stepper';
import { useClaimFormPersistence } from '@/hooks/useLocalStorageForm';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { isAuthenticated, getCurrentUser, type UserProfile } from '@/services/auth';
import { Step1_Flight } from './Step1_Flight';
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

export function ClaimFormPage() {
  useDocumentTitle('File Claim');
  const navigate = useNavigate();
  const {
    formData,
    updateStep,
    updateFlightData,
    updateEligibilityData,
    updatePassengerData,
    updateDocuments,
    clearFormData,
  } = useClaimFormPersistence();

  const [currentStep, setCurrentStep] = useState(formData.currentStep || 1);
  const [flightData, setFlightData] = useState<FlightStatus | null>(
    formData.flightData || null
  );
  const [eligibilityData, setEligibilityData] = useState<EligibilityResponse | null>(
    formData.eligibilityData || null
  );
  const [customerEmail, setCustomerEmail] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [passengerData, setPassengerData] = useState<any>(
    formData.passengerData || null
  );
  const [documents, setDocuments] = useState<any[]>(formData.documents || []);

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

  const handleFlightComplete = (data: FlightStatus) => {
    setFlightData(data);
    updateFlightData(data);
    setCurrentStep(2);
  };

  const handleEligibilityComplete = (data: EligibilityResponse, email: string) => {
    setEligibilityData(data);
    updateEligibilityData(data);
    setCustomerEmail(email);
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
    // Clear form data
    clearFormData();
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
      setCurrentStep(1);
      setFlightData(null);
      setEligibilityData(null);
      setPassengerData(null);
      setDocuments([]);
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
              onComplete={handleSubmitComplete}
              onBack={handleBack}
            />
          )}
        </div>
      </div>
    </div>
  );
}
