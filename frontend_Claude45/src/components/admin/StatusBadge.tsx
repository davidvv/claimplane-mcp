/**
 * Status Badge Component
 * Displays claim status with appropriate color coding
 */

import { Badge } from '../ui/Badge';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

const STATUS_CONFIG: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'success' | 'outline' }> = {
  // Initial states
  submitted: { label: 'Submitted', variant: 'secondary' },
  pending_review: { label: 'Pending Review', variant: 'secondary' },

  // Under review
  under_review: { label: 'Under Review', variant: 'default' },
  additional_info_required: { label: 'Info Required', variant: 'outline' },

  // Decision states
  approved: { label: 'Approved', variant: 'success' },
  rejected: { label: 'Rejected', variant: 'destructive' },

  // Processing states
  payment_processing: { label: 'Payment Processing', variant: 'default' },
  payment_sent: { label: 'Payment Sent', variant: 'success' },
  paid: { label: 'Paid', variant: 'success' },
  completed: { label: 'Completed', variant: 'success' },

  // Cancellation
  cancelled: { label: 'Cancelled', variant: 'destructive' },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || {
    label: status.replace(/_/g, ' '),
    variant: 'outline' as const,
  };

  return (
    <Badge variant={config.variant} className={className}>
      {config.label}
    </Badge>
  );
}
