import React from 'react';
import { clsx } from 'clsx';

interface ProgressBarProps {
  currentStep: number;
  totalSteps: number;
  completedSteps: number[];
}

export default function ProgressBar({ currentStep, totalSteps, completedSteps }: ProgressBarProps) {
  const steps = Array.from({ length: totalSteps }, (_, i) => i + 1);
  
  const getStepStatus = (step: number) => {
    if (completedSteps.includes(step)) return 'completed';
    if (step === currentStep) return 'current';
    return 'upcoming';
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const status = getStepStatus(step);
          const isLast = index === steps.length - 1;
          
          return (
            <React.Fragment key={step}>
              <div className="flex items-center">
                {/* Step Circle */}
                <div
                  className={clsx(
                    'flex items-center justify-center w-10 h-10 rounded-full text-sm font-medium transition-all duration-200',
                    {
                      'bg-primary-600 text-white': status === 'current',
                      'bg-green-600 text-white': status === 'completed',
                      'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400': status === 'upcoming',
                    }
                  )}
                >
                  {status === 'completed' ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    step
                  )}
                </div>
                
                {/* Step Label */}
                <div className="ml-3 hidden sm:block">
                  <p
                    className={clsx(
                      'text-sm font-medium',
                      {
                        'text-primary-600 dark:text-primary-400': status === 'current',
                        'text-green-600 dark:text-green-400': status === 'completed',
                        'text-gray-500 dark:text-gray-400': status === 'upcoming',
                      }
                    )}
                  >
                    {getStepLabel(step)}
                  </p>
                </div>
              </div>
              
              {/* Connector Line */}
              {!isLast && (
                <div className="flex-1 mx-4">
                  <div
                    className={clsx(
                      'h-0.5 transition-colors duration-200',
                      {
                        'bg-green-600': completedSteps.includes(step + 1) || step < currentStep,
                        'bg-gray-200 dark:bg-gray-700': !completedSteps.includes(step + 1) && step >= currentStep,
                      }
                    )}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
      
      {/* Mobile Step Labels */}
      <div className="sm:hidden mt-4">
        <p className="text-sm font-medium text-center text-gray-900 dark:text-white">
          Step {currentStep} of {totalSteps}: {getStepLabel(currentStep)}
        </p>
      </div>
    </div>
  );
}

function getStepLabel(step: number): string {
  const labels = {
    1: 'Flight Details',
    2: 'Eligibility Check',
    3: 'Passenger Info',
    4: 'Review & Submit',
  };
  
  return labels[step as keyof typeof labels] || `Step ${step}`;
}