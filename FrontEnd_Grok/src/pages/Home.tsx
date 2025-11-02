import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Plane, Shield, Clock, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <>
      <section className="bg-gradient-to-b from-primary/10 to-white dark:to-gray-900 py-20">
        <div className="container-custom text-center">
          <h1 className="text-5xl font-bold mb-6">Get Compensated for Flight Delays</h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
            Up to €600 per passenger under EU261, DOT, and CTA regulations. No win, no fee.
          </p>
          <div className="flex gap-4 justify-center">
            <Button asChild size="lg">
              <Link to="/claim">File a Claim</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link to="/status">Check Status</Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="container-custom">
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="p-6 text-center">
              <Clock className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="font-semibold mb-2">3+ Hour Delay</h3>
              <p className="text-sm text-gray-600">Eligible for compensation</p>
            </Card>
            <Card className="p-6 text-center">
              <Plane className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="font-semibold mb-2">Cancelled Flight</h3>
              <p className="text-sm text-gray-600">Get up to €600 back</p>
            </Card>
            <Card className="p-6 text-center">
              <Shield className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="font-semibold mb-2">No Win, No Fee</h3>
              <p className="text-sm text-gray-600">Risk-free process</p>
            </Card>
          </div>
        </div>
      </section>
    </>
  );
}