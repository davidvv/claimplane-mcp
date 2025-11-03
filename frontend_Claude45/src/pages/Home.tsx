/**
 * Landing page / Home
 */

import { Link } from 'react-router-dom';
import {
  Plane,
  FileText,
  Search,
  CheckCircle,
  Clock,
  Shield,
  Euro,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';

export function Home() {
  return (
    <div className="w-full">
      {/* Hero Section */}
      <section className="py-20 md:py-32 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Get Your Flight
              <br />
              <span className="text-primary">Compensation Fast</span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Delayed, cancelled, or denied boarding? You may be entitled to up to
              €600 compensation under EU261 regulation. File your claim in minutes.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/claim/new">
                <Button size="lg" className="w-full sm:w-auto">
                  <FileText className="w-5 h-5 mr-2" />
                  File a Claim
                </Button>
              </Link>
              <Link to="/status">
                <Button size="lg" variant="outline" className="w-full sm:w-auto">
                  <Search className="w-5 h-5 mr-2" />
                  Check Status
                </Button>
              </Link>
            </div>

            {/* Trust indicators */}
            <div className="mt-12 flex flex-wrap justify-center gap-8 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span>No Win, No Fee</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-600" />
                <span>5 Min Application</span>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-purple-600" />
                <span>GDPR Secure</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 md:py-32">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              How It Works
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Get compensated in three simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Step 1 */}
            <Card>
              <CardContent className="pt-6">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <FileText className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">1. Submit Your Claim</h3>
                <p className="text-muted-foreground">
                  Enter your flight details and upload required documents. Takes
                  less than 5 minutes.
                </p>
              </CardContent>
            </Card>

            {/* Step 2 */}
            <Card>
              <CardContent className="pt-6">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <Search className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">2. We Review</h3>
                <p className="text-muted-foreground">
                  Our experts check your eligibility and handle all communication
                  with the airline.
                </p>
              </CardContent>
            </Card>

            {/* Step 3 */}
            <Card>
              <CardContent className="pt-6">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <Euro className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">3. Get Paid</h3>
                <p className="text-muted-foreground">
                  Receive your compensation directly to your bank account. Usually
                  within 8-12 weeks.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Compensation Amounts */}
      <section className="py-20 md:py-32 bg-muted/50">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Compensation Amounts
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Under EU261 regulation, you're entitled to compensation based on flight
              distance
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-4xl font-bold text-primary mb-2">€250</div>
                <div className="text-sm text-muted-foreground mb-4">
                  Flights up to 1,500 km
                </div>
                <p className="text-sm">
                  Short-haul flights within the EU
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-4xl font-bold text-primary mb-2">€400</div>
                <div className="text-sm text-muted-foreground mb-4">
                  Flights 1,500 - 3,500 km
                </div>
                <p className="text-sm">
                  Medium-haul flights
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-4xl font-bold text-primary mb-2">€600</div>
                <div className="text-sm text-muted-foreground mb-4">
                  Flights over 3,500 km
                </div>
                <p className="text-sm">
                  Long-haul international flights
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="mt-12 text-center">
            <Link to="/claim/new">
              <Button size="lg">Check Your Eligibility</Button>
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ Preview */}
      <section className="py-20 md:py-32">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="max-w-3xl mx-auto space-y-6">
            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-2">
                  How long does the claim process take?
                </h3>
                <p className="text-muted-foreground">
                  Most claims are processed within 8-12 weeks. We handle all
                  communication with the airline on your behalf.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-2">Do I pay anything upfront?</h3>
                <p className="text-muted-foreground">
                  No! We operate on a "no win, no fee" basis. You only pay our
                  commission if your claim is successful.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-2">
                  What documents do I need?
                </h3>
                <p className="text-muted-foreground">
                  Typically just your boarding pass and ID. In some cases, we may
                  ask for additional documentation like receipts for expenses.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 md:py-32 bg-primary text-white">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center">
            <Plane className="w-16 h-16 mx-auto mb-6 opacity-90" />
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to Claim Your Compensation?
            </h2>
            <p className="text-xl mb-8 opacity-90">
              Join thousands of passengers who've successfully claimed with
              EasyAirClaim
            </p>
            <Link to="/claim/new">
              <Button
                size="lg"
                variant="secondary"
                className="bg-white text-primary hover:bg-white/90"
              >
                Start Your Claim Now
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
