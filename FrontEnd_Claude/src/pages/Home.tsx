/**
 * Landing/Home page
 */
import { Link } from 'react-router-dom';
import { Plane, CheckCircle, Shield, Clock, ArrowRight, Euro } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';

export function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-aviation-cloud to-white dark:from-gray-900 dark:to-gray-800">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="mx-auto max-w-4xl">
          <div className="mb-8 inline-block rounded-full bg-primary-100 p-4 dark:bg-primary-900">
            <Plane className="h-16 w-16 text-primary-600 dark:text-primary-400" />
          </div>

          <h1 className="mb-6 text-5xl font-bold text-gray-900 dark:text-gray-100 sm:text-6xl">
            Get the Flight Compensation
            <br />
            <span className="text-primary-600 dark:text-primary-400">You Deserve</span>
          </h1>

          <p className="mb-8 text-xl text-gray-600 dark:text-gray-300">
            Delayed, cancelled, or disrupted flight? Claim up to €600 compensation under EU261
            regulations. Fast, easy, and no win - no fee.
          </p>

          <div className="flex flex-col justify-center gap-4 sm:flex-row">
            <Link to="/claim">
              <Button size="lg" className="px-8">
                File a Claim
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/status">
              <Button size="lg" variant="outline" className="px-8">
                Check Claim Status
              </Button>
            </Link>
          </div>

          {/* Trust Signals */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-8 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-green-600" />
              <span>GDPR Compliant</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span>No Win - No Fee</span>
            </div>
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-green-600" />
              <span>24/7 Support</span>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-white py-20 dark:bg-gray-800">
        <div className="container mx-auto px-4">
          <h2 className="mb-12 text-center text-4xl font-bold text-gray-900 dark:text-gray-100">
            How It Works
          </h2>

          <div className="grid gap-8 md:grid-cols-3">
            <Card hoverable>
              <div className="text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-100 text-2xl font-bold text-primary-600 dark:bg-primary-900 dark:text-primary-400">
                  1
                </div>
                <CardTitle className="mb-2">Enter Flight Details</CardTitle>
                <CardDescription>
                  Provide your flight number and date. We'll automatically check your eligibility
                  for compensation.
                </CardDescription>
              </div>
            </Card>

            <Card hoverable>
              <div className="text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-100 text-2xl font-bold text-primary-600 dark:bg-primary-900 dark:text-primary-400">
                  2
                </div>
                <CardTitle className="mb-2">Submit Your Claim</CardTitle>
                <CardDescription>
                  Fill in your passenger details and upload supporting documents. The process
                  takes less than 5 minutes.
                </CardDescription>
              </div>
            </Card>

            <Card hoverable>
              <div className="text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-100 text-2xl font-bold text-primary-600 dark:bg-primary-900 dark:text-primary-400">
                  3
                </div>
                <CardTitle className="mb-2">Get Compensated</CardTitle>
                <CardDescription>
                  We handle everything with the airline. Track your claim status and receive your
                  compensation directly.
                </CardDescription>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Compensation Amounts */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="mb-12 text-center text-4xl font-bold text-gray-900 dark:text-gray-100">
            Compensation You Can Claim
          </h2>

          <div className="mx-auto max-w-4xl">
            <Card>
              <CardHeader>
                <CardTitle>EU261 Regulation Amounts</CardTitle>
                <CardDescription>
                  Based on flight distance and delay duration
                </CardDescription>
              </CardHeader>

              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-lg bg-primary-50 p-4 dark:bg-primary-900/20">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      Short Distance
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Flights up to 1,500 km
                    </p>
                  </div>
                  <div className="flex items-center text-2xl font-bold text-primary-700 dark:text-primary-400">
                    <Euro className="mr-1 h-6 w-6" />
                    250
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-lg bg-primary-50 p-4 dark:bg-primary-900/20">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      Medium Distance
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Flights 1,500 - 3,500 km
                    </p>
                  </div>
                  <div className="flex items-center text-2xl font-bold text-primary-700 dark:text-primary-400">
                    <Euro className="mr-1 h-6 w-6" />
                    400
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-lg bg-primary-50 p-4 dark:bg-primary-900/20">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      Long Distance
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Flights over 3,500 km
                    </p>
                  </div>
                  <div className="flex items-center text-2xl font-bold text-primary-700 dark:text-primary-400">
                    <Euro className="mr-1 h-6 w-6" />
                    600
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-600 py-20 dark:bg-primary-800">
        <div className="container mx-auto px-4 text-center">
          <h2 className="mb-6 text-4xl font-bold text-white">
            Ready to Claim Your Compensation?
          </h2>
          <p className="mb-8 text-xl text-primary-100">
            Join thousands of passengers who've successfully claimed their rights
          </p>
          <Link to="/claim">
            <Button size="lg" variant="secondary" className="px-8">
              Start Your Claim Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* FAQ Preview */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="mb-12 text-center text-4xl font-bold text-gray-900 dark:text-gray-100">
            Frequently Asked Questions
          </h2>

          <div className="mx-auto max-w-3xl space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>How long does the process take?</CardTitle>
              </CardHeader>
              <p className="text-gray-700 dark:text-gray-300">
                Most claims are processed within 4-8 weeks, though it can vary depending on the
                airline's response time. We'll keep you updated throughout the process.
              </p>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>What if my claim is rejected?</CardTitle>
              </CardHeader>
              <p className="text-gray-700 dark:text-gray-300">
                We operate on a no win - no fee basis. If your claim is unsuccessful, you don't
                pay anything. We only charge a commission on successful claims.
              </p>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Which flights are covered?</CardTitle>
              </CardHeader>
              <p className="text-gray-700 dark:text-gray-300">
                We cover flights under EU261 (departing from EU or arriving in EU with EU
                carrier), US DOT regulations, and Canadian CTA regulations.
              </p>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}
