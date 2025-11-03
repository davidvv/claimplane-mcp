import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFormProgress } from '../hooks/useLocalStorageForm';
import Step1_Flight from './ClaimForm/Step1_Flight';
import Step2_Eligibility from './ClaimForm/Step2_Eligibility';
import Step3_Passenger from './ClaimForm/Step3_Passenger';
import Step4_Review from './ClaimForm/Step4_Review';
import ProgressBar from '../components/ProgressBar';
import { FormProgress } from '../types/openapi';

export default function ClaimForm() {
  const navigate = useNavigate();
  const totalSteps = 4;
  
  // Use localStorage for form progress persistence
  const {
    currentStep,
    completedSteps,
    goToStep,
    nextStep,
    prevStep,
    completeStep,
  } = useFormProgress('claim_form', totalSteps);

  const [formData, setFormData] = useState<FormProgress['data']>({
    flightInfo: undefined,
    eligibility: undefined,
    customerInfo: undefined,
    documents: [],
  });

  const handleStepComplete = (step: number, data: any) => {
    setFormData(prev => ({ ...prev, ...data }));
    completeStep(step);
    
    if (step < totalSteps) {
      nextStep();
    }
  };

  const handleSubmit = async () => {
    try {
      // Submit claim logic would go here
      console.log('Submitting claim:', formData);
      
      // Navigate to success page with claim data
      navigate('/success', { 
        state: { 
          claim: {
            id: '123e4567-e89b-12d3-a456-426614174002',
            ...formData,
            submittedAt: new Date().toISOString(),
          }
        } 
      });
    } catch (error) {
      console.error('Failed to submit claim:', error);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <Step1_Flight
            initialData={formData.flightInfo}
            onComplete={(data) => handleStepComplete(1, { flightInfo: data })}
          />
        );
      case 2:
        return (
          <Step2_Eligibility
            flightInfo={formData.flightInfo}
            initialData={formData.eligibility}
            onComplete={(data) => handleStepComplete(2, { eligibility: data })}
            onBack={prevStep}
          />
        );
      case 3:
        return (
          <Step3_Passenger
            initialData={formData.customerInfo}
            onComplete={(data) => handleStepComplete(3, { customerInfo: data })}
            onBack={prevStep}
          />
        );
      case 4:
        return (
          <Step4_Review
            formData={formData}
            onSubmit={handleSubmit}
            onBack={prevStep}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            File a Compensation Claim
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Get up to €600 for your delayed, cancelled, or overbooked flight
          </p>
        </div>

        {/* Progress Bar */}
        <ProgressBar
          currentStep={currentStep}
          totalSteps={totalSteps}
          completedSteps={completedSteps}
        />

        {/* Step Content */}
        <div className="mt-8">
          {renderStep()}
        </div>

        {/* Navigation Help */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Step {currentStep} of {totalSteps} • Your progress is automatically saved
          </p>
        </div>
      </div>
    </div>
  );
}