/**
 * Multi-step claim form container
 */
import { useEffect } from 'react';
import { useClaimStore } from '@/store/claimStore';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { Step1Flight } from './Step1_Flight';
import { Step2Eligibility } from './Step2_Eligibility';
import { Step3Passenger } from './Step3_Passenger';
import { Step4Review } from './Step4_Review';

const FORM_STEPS = [
  { id: 1, label: 'Flight', description: 'Find your flight' },
  { id: 2, label: 'Eligibility', description: 'Check compensation' },
  { id: 3, label: 'Details', description: 'Your information' },
  { id: 4, label: 'Review', description: 'Submit claim' },
];

export function ClaimFormPage() {
  const { currentStep } = useClaimStore();

  // Scroll to top on step change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [currentStep]);

  return (
    <div className="min-h-screen bg-gray-50 py-8 dark:bg-gray-900">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            File Your Claim
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Complete the form below to submit your compensation claim
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-12">
          <ProgressBar steps={FORM_STEPS} currentStep={currentStep} />
        </div>

        {/* Form Steps */}
        <div className="animate-fade-in">
          {currentStep === 0 && <Step1Flight />}
          {currentStep === 1 && <Step2Eligibility />}
          {currentStep === 2 && <Step3Passenger />}
          {currentStep === 3 && <Step4Review />}
        </div>
      </div>
    </div>
  );
}
