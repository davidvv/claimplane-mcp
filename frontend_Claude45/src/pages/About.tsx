/**
 * About Us page
 */

import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export function About() {
  const location = useLocation();

  useEffect(() => {
    // Handle scrolling to anchor when hash is present in URL
    if (location.hash) {
      const id = location.hash.replace('#', '');
      const element = document.getElementById(id);
      if (element) {
        // Small delay to ensure page has rendered
        setTimeout(() => {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
    }
  }, [location]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">About EasyAirClaim</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Making flight compensation claims easy, secure, and transparent
          </p>
        </div>

        {/* Why Choose Us Section */}
        <section className="mb-20">
          <h2 className="text-3xl font-bold text-center mb-12">Why Choose EasyAirClaim?</h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Easy */}
            <div className="bg-card p-6 rounded-lg border shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Easy</h3>
              <p className="text-muted-foreground">
                Simple online process. No complicated paperwork. Just answer a few questions and we handle the rest.
              </p>
            </div>

            {/* Secure */}
            <div className="bg-card p-6 rounded-lg border shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Secure</h3>
              <p className="text-muted-foreground">
                Your data is encrypted and protected. GDPR compliant with 256-bit SSL encryption for all transfers.
              </p>
            </div>

            {/* Cost Effective */}
            <div className="bg-card p-6 rounded-lg border shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Cost Effective</h3>
              <p className="text-muted-foreground">
                Only 20% commission (includes Taxes & VAT). No upfront costs. No hidden fees. You only pay if we win your claim.
              </p>
            </div>

            {/* Transparent */}
            <div className="bg-card p-6 rounded-lg border shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Transparent</h3>
              <p className="text-muted-foreground">
                Track your claim status in real-time. Know exactly what's happening every step of the way.
              </p>
            </div>
          </div>
        </section>

        {/* Who We Are Section */}
        <section className="mb-20">
          <div className="bg-card p-12 rounded-lg border shadow-sm max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold mb-6 text-center">Who We Are</h2>
            <div className="prose prose-slate dark:prose-invert max-w-none">
              <p className="text-lg text-muted-foreground text-center mb-6">
                EasyAirClaim is dedicated to helping air passengers claim the compensation they deserve under EU Regulation 261/2004.
              </p>
              <p className="text-muted-foreground text-center mb-6">
                Our team of aviation experts and customer advocates work tirelessly to ensure airlines honor their obligations to passengers.
                We believe that claiming compensation should be simple, transparent, and accessible to everyone.
              </p>
              <p className="text-muted-foreground text-center">
                Founded with the mission to level the playing field between airlines and passengers, we've helped thousands of travelers
                recover millions in compensation for flight delays, cancellations, and denied boarding.
              </p>
            </div>
          </div>
        </section>

        {/* Our Fees Section */}
        <section id="fees" className="mb-20">
          <h2 className="text-3xl font-bold text-center mb-4">Our Fees</h2>
          <p className="text-xl text-muted-foreground text-center mb-12 max-w-2xl mx-auto">
            Simple, transparent pricing. Just 20% commission (includes Taxes & VAT) on successful claims.
          </p>

          <div className="grid md:grid-cols-2 gap-12 max-w-5xl mx-auto items-center">
            {/* Pie Chart */}
            <div className="flex flex-col items-center">
              <div className="relative w-64 h-64">
                <svg viewBox="0 0 100 100" className="transform -rotate-90">
                  {/* Background circle */}
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="20"
                  />
                  {/* You get 80% - Blue segment (starts at top, goes 80% clockwise) */}
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke="hsl(var(--primary))"
                    strokeWidth="20"
                    strokeDasharray="201.06 251.33"
                    strokeDashoffset="0"
                    className="transition-all"
                  />
                  {/* Our commission 20% - Orange segment (remaining 20%) */}
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="20"
                    strokeDasharray="50.27 251.33"
                    strokeDashoffset="-201.06"
                    className="transition-all"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-3xl font-bold">€600</div>
                    <div className="text-sm text-muted-foreground">Total Claim</div>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-sm bg-primary"></div>
                  <span className="text-sm">You receive: <strong>€480 (80%)</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-sm" style={{ backgroundColor: '#f97316' }}></div>
                  <span className="text-sm">Our commission: <strong>€120 (20%, includes Taxes & VAT)</strong></span>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="mt-6 bg-muted/30 border border-muted-foreground/20 rounded-lg p-4 max-w-xs">
                <p className="text-xs text-muted-foreground text-center">
                  <strong>Example calculation</strong> for an eligible claim with a delay of more than 3 hours
                  and a flight distance of more than 3,500 km (€600 compensation under EU261).
                </p>
              </div>
            </div>

            {/* Fee Breakdown */}
            <div className="space-y-6">
              <div className="bg-primary/5 border-l-4 border-primary p-6 rounded">
                <h3 className="text-2xl font-bold mb-2">No Win, No Fee</h3>
                <p className="text-muted-foreground">
                  You only pay if we successfully recover your compensation. If we don't win, you don't pay anything.
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="text-muted-foreground">EU261 Compensation:</span>
                  <span className="font-semibold">€600.00</span>
                </div>
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="text-muted-foreground">Our Commission (20%):</span>
                  <span className="font-semibold text-muted-foreground">- €120.00</span>
                </div>
                <div className="flex justify-between items-center pb-2 border-b border-primary">
                  <span className="font-bold">You Receive:</span>
                  <span className="text-2xl font-bold text-primary">€480.00</span>
                </div>
              </div>

              <div className="bg-muted/50 p-4 rounded">
                <p className="text-sm text-muted-foreground text-center">
                  <strong>No hidden costs.</strong> No setup fees. No processing fees.
                  Just straightforward 20% commission on successful claims.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="text-center">
          <div className="bg-primary/10 border border-primary/20 rounded-lg p-8 max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold mb-4">Ready to Claim Your Compensation?</h2>
            <p className="text-muted-foreground mb-6">
              Check your eligibility in just 2 minutes. No commitment required.
            </p>
            <a
              href="/claim/new"
              className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-11 px-8 py-2"
            >
              Start Your Claim
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
