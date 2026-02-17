/**
 * Blog CTA Widget Component
 * Displays a call-to-action for flight compensation
 */

import { Link } from 'react-router-dom';
import { Plane, Clock, AlertTriangle, ArrowRight, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BlogCTAWidgetProps {
  className?: string;
  variant?: 'default' | 'inline' | 'banner';
}

export function BlogCTAWidget({ className, variant = 'default' }: BlogCTAWidgetProps) {
  if (variant === 'banner') {
    return (
      <div
        className={cn(
          'bg-gradient-to-r from-primary to-primary/80 text-primary-foreground rounded-lg p-6 my-8',
          className
        )}
      >
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <Plane className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Was Your Flight Delayed?</h3>
              <p className="text-sm opacity-90">
                You could be entitled to up to €600 in compensation
              </p>
            </div>
          </div>
          <Link
            to="/eligibility"
            className="inline-flex items-center gap-2 bg-white text-primary font-semibold px-6 py-3 rounded-md hover:bg-white/90 transition-colors"
          >
            Check Now
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  if (variant === 'inline') {
    return (
      <div
        className={cn(
          'bg-primary/5 border border-primary/20 rounded-lg p-4 my-6',
          className
        )}
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-primary" />
          </div>
          <div className="flex-1">
            <p className="font-medium text-sm">
              Flight delayed or cancelled? You may be entitled to compensation.
            </p>
            <Link
              to="/eligibility"
              className="inline-flex items-center gap-1 text-sm text-primary font-medium mt-1 hover:text-primary/80"
            >
              Check your eligibility
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Default variant - full widget
  return (
    <div
      className={cn(
        'bg-card border rounded-lg p-6 my-8',
        className
      )}
    >
      <div className="text-center mb-4">
        <div className="inline-flex items-center justify-center w-14 h-14 bg-primary/10 rounded-full mb-3">
          <Plane className="w-7 h-7 text-primary" />
        </div>
        <h3 className="text-xl font-bold mb-1">Was Your Flight Disrupted?</h3>
        <p className="text-muted-foreground text-sm">
          Check if you're eligible for compensation
        </p>
      </div>

      {/* Benefits list */}
      <ul className="space-y-2 mb-6">
        <li className="flex items-center gap-2 text-sm">
          <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
          <span>Up to <strong>€600</strong> per passenger</span>
        </li>
        <li className="flex items-center gap-2 text-sm">
          <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
          <span>No win, <strong>no fee</strong></span>
        </li>
        <li className="flex items-center gap-2 text-sm">
          <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
          <span>Claims for flights up to <strong>3 years ago</strong></span>
        </li>
        <li className="flex items-center gap-2 text-sm">
          <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
          <span>Covers <strong>delays, cancellations, denied boarding</strong></span>
        </li>
      </ul>

      {/* CTA Buttons */}
      <div className="space-y-3">
        <Link
          to="/eligibility"
          className="inline-flex items-center justify-center gap-2 w-full rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-11 px-4"
        >
          <Clock className="w-4 h-4" />
          Check Eligibility (2 min)
        </Link>
        <Link
          to="/claim/new"
          className="inline-flex items-center justify-center w-full rounded-md text-sm font-medium border border-input bg-background hover:bg-accent h-11 px-4"
        >
          Start Your Claim
        </Link>
      </div>

      {/* Trust badges */}
      <div className="mt-4 pt-4 border-t text-center">
        <p className="text-xs text-muted-foreground">
          Trusted by 10,000+ passengers • EU261 experts
        </p>
      </div>
    </div>
  );
}

export default BlogCTAWidget;
