/**
 * Multi-step progress indicator for claim form wizard
 */

import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Step {
  number: number;
  title: string;
  description: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
}

export function Stepper({ steps, currentStep }: StepperProps) {
  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center justify-between w-full">
        {steps.map((step, index) => {
          const isCompleted = currentStep > step.number;
          const isCurrent = currentStep === step.number;
          const isUpcoming = currentStep < step.number;

          return (
            <li
              key={step.number}
              className={cn(
                'relative flex flex-col items-center flex-1',
                index !== steps.length - 1 && 'pr-4'
              )}
            >
              {/* Connector line */}
              {index !== steps.length - 1 && (
                <div
                  className={cn(
                    'absolute top-5 left-1/2 h-0.5 w-full transition-colors',
                    isCompleted ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'
                  )}
                />
              )}

              {/* Step circle */}
              <div
                className={cn(
                  'relative flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all z-10',
                  isCompleted &&
                    'bg-primary border-primary text-white',
                  isCurrent &&
                    'border-primary bg-white dark:bg-background text-primary',
                  isUpcoming &&
                    'border-gray-300 dark:border-gray-600 bg-white dark:bg-background text-gray-500'
                )}
              >
                {isCompleted ? (
                  <Check className="w-5 h-5" />
                ) : (
                  <span className="text-sm font-semibold">{step.number}</span>
                )}
              </div>

              {/* Step label */}
              <div className="mt-3 text-center">
                <p
                  className={cn(
                    'text-sm font-medium transition-colors',
                    (isCurrent || isCompleted) && 'text-foreground',
                    isUpcoming && 'text-muted-foreground'
                  )}
                >
                  {step.title}
                </p>
                <p className="text-xs text-muted-foreground hidden sm:block">
                  {step.description}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
