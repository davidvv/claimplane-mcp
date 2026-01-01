/**
 * Contact page
 */

import { Mail, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';

export function Contact() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Contact Us</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Have questions? We're here to help. Reach out to our support team.
          </p>
        </div>

        {/* Contact Information */}
        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            {/* Email Support */}
            <div className="bg-card p-8 rounded-lg border shadow-sm">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <Mail className="w-6 h-6 text-primary" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Email Support</h2>
              <p className="text-muted-foreground mb-4">
                Send us an email and we'll respond within 24 hours
              </p>
              <a
                href="mailto:support@easyairclaim.com"
                className="text-primary font-semibold text-lg hover:underline"
              >
                support@easyairclaim.com
              </a>
            </div>

            {/* Business Address */}
            <div className="bg-card p-8 rounded-lg border shadow-sm">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <MapPin className="w-6 h-6 text-primary" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Business Address</h2>
              <p className="text-muted-foreground mb-4">
                EasyAirClaim LLC
              </p>
              <p className="text-foreground">
                3436 SW 8th Pl<br />
                Cape Coral, FL 33914<br />
                United States
              </p>
            </div>
          </div>

          {/* Additional Information */}
          <div className="bg-muted/30 border rounded-lg p-8 mb-12">
            <h2 className="text-2xl font-bold mb-4">What to Include in Your Message</h2>
            <ul className="space-y-3 text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="text-primary mt-1">•</span>
                <span><strong>For claim inquiries:</strong> Include your claim ID and booking reference</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-1">•</span>
                <span><strong>For technical support:</strong> Describe the issue and include screenshots if possible</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-1">•</span>
                <span><strong>For general questions:</strong> Be as specific as possible to help us assist you better</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-1">•</span>
                <span><strong>For termination requests:</strong> See our <Link to="/terms" className="text-primary hover:underline">Terms & Conditions</Link> for the required template</span>
              </li>
            </ul>
          </div>

          {/* Response Time */}
          <div className="bg-primary/5 border-l-4 border-primary p-6 rounded mb-12">
            <h3 className="text-xl font-bold mb-2">Response Time</h3>
            <p className="text-muted-foreground">
              Our support team typically responds within <strong>24 hours</strong> during business days.
              For urgent matters related to existing claims, we prioritize responses and aim to reply within <strong>12 hours</strong>.
            </p>
          </div>

          {/* FAQ Link */}
          <div className="text-center bg-card p-8 rounded-lg border shadow-sm">
            <h2 className="text-2xl font-bold mb-4">Before You Contact Us</h2>
            <p className="text-muted-foreground mb-6">
              Check out our About page for commonly asked questions about fees, the claim process, and timelines.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/about">
                <button className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-6 py-2">
                  Visit About Page
                </button>
              </Link>
              <Link to="/status">
                <button className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-6 py-2">
                  Check Claim Status
                </button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
