import React from 'react';

export interface ProgressBarProps {
  currentStep: number;
  totalSteps: number;
  stepLabels?: string[];
}

declare const ProgressBar: React.FC<ProgressBarProps>;

export default ProgressBar;