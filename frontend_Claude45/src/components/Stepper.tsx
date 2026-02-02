/**
 * Multi-step progress indicator for claim form wizard
 */

import { memo } from 'react';
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

export const Stepper = memo(function Stepper({ steps, currentStep }: StepperProps) {
  return (
    <nav aria-label="Progress" className="mb-8 overflow-hidden">
      <ol className="flex items-center justify-between w-full">
        {steps.map((step, index) => {
          const isCompleted = currentStep > step.number;
          const isCurrent = currentStep === step.number;
          const isUpcoming = currentStep < step.number;

          return (
            <li
              key={step.number}
              className={cn(
                'relative flex flex-col items-center flex-1 min-w-0'
              )}
            >
              {/* Connector line */}
              {index !== steps.length - 1 && (
                <div
                  className={cn(
                    'absolute top-4 sm:top-5 left-1/2 h-0.5 w-full transition-colors z-0',
                    isCompleted ? 'bg-primary' : 'bg-border'
                  )}
                />
              )}

              {/* Step circle */}
              <div
                className={cn(
                  'relative flex items-center justify-center w-8 h-8 xs:w-10 xs:h-10 rounded-full border-2 transition-all z-10 bg-background shrink-0',
                  isCompleted &&
                    'bg-primary border-primary text-white',
                  isCurrent &&
                    'border-primary text-primary',
                  isUpcoming &&
                    'border-border text-muted-foreground'
                )}
              >
                {isCompleted ? (
                  <Check className="w-4 h-4 xs:w-5 xs:h-5" />
                ) : (
                  <span className="text-xs xs:text-sm font-semibold">{step.number}</span>
                )}
              </div>

              {/* Step label */}
              <div className="mt-2 sm:mt-3 text-center px-1 w-full overflow-hidden">
                <p
                  className={cn(
                    'text-[10px] xs:text-xs sm:text-sm font-medium transition-colors truncate',
                    (isCurrent || isCompleted) ? 'text-foreground' : 'text-muted-foreground'
                  )}
                >
                  {/* Show full title on larger mobile, but just number/icon on tiny screens if needed */}
                  <span className="hidden xs:inline">{step.title}</span>
                  <span className="xs:hidden">{isCurrent ? step.title : ''}</span>
                </p>
                <p className="text-[10px] sm:text-xs text-muted-foreground hidden md:block truncate">
                  {step.description}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
});
