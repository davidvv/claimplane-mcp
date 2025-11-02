import React from 'react';

export interface SuccessProps {
  claimId: string;
  compensationAmount?: number;
  currency?: string;
}

declare const Success: React.FC<SuccessProps>;

export default Success;