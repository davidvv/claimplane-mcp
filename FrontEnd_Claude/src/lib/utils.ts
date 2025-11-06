import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function validateFile(file: File): { valid: boolean; error?: string } {
  // TODO: Implement actual file validation logic
  return { valid: true };
}

/**
 * Format a number as currency in EUR
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: 'EUR',
  }).format(amount);
}

/**
 * Format a date string or Date object
 */
export function formatDate(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(dateObj);
}

/**
 * Format delay in minutes to a human-readable string
 */
export function formatDelay(minutes: number): string {
  if (minutes < 60) {
    return `${minutes} minutes`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  if (remainingMinutes === 0) {
    return `${hours} ${hours === 1 ? 'hour' : 'hours'}`;
  }
  return `${hours} ${hours === 1 ? 'hour' : 'hours'} ${remainingMinutes} minutes`;
}

/**
 * Format status label to human-readable format
 */
export function formatStatusLabel(status: string): string {
  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Get color variant for status badge
 */
export function getStatusColor(status: string): 'default' | 'success' | 'warning' | 'error' {
  const statusLower = status.toLowerCase();

  if (statusLower === 'approved' || statusLower === 'paid') {
    return 'success';
  }
  if (statusLower === 'rejected' || statusLower === 'cancelled') {
    return 'error';
  }
  if (statusLower === 'pending' || statusLower === 'under_review' || statusLower === 'awaiting_documents') {
    return 'warning';
  }
  return 'default';
}
