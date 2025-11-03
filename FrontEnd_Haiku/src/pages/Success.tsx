import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { CheckCircle, Copy, Mail, Clock, FileText, ArrowRight, Plane } from 'lucide-react';
import { toast } from 'sonner';

export default function Success() {
  const location = useLocation();
  const [copied, setCopied] = useState(false);
  
  // Get claim data from location state or use mock data
  const claimData = location.state?.claim || {
    id: '123e4567-e89b-12d3-a456-426614174002',
    flightInfo: {
      flightNumber: 'LH1234',
      airline: 'Lufthansa',
      departureDate: '2025-06-15',
    },
    compensationAmount: 600,
    currency: 'EUR',
    submittedAt: new Date().toISOString(),
  };

  const handleCopyClaimId = async () => {
    try {
      await navigator.clipboard.writeText(claimData.id);
      setCopied(true);
      toast.success('Claim ID copied to clipboard!');
      
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy claim ID');
    }
  };

  const handleEmailConfirmation = () => {
    toast.success('Confirmation email sent!');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Success Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full mb-4">
            <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
          </div>
          
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Claim Submitted Successfully!
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Your compensation claim has been received and is being processed.
          </p>
        </div>

        {/* Success Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 mb-8">
          <div className="space-y-6">
            {/* Claim ID Section */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Your Claim Details
              </h2>
              
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      Claim ID
                    </p>
                    <p className="font-mono text-sm text-gray-900 dark:text-white font-semibold">
                      {claimData.id}
                    </p>
                  </div>
                  
                  <button
                    onClick={handleCopyClaimId}
                    className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-md transition-colors duration-200"
                  >
                    {copied ? (
                      <>
                        <CheckCircle className="h-4 w-4" />
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Flight Information */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Flight Information
              </h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Flight Number</p>
                  <p className="font-medium text-gray-900 dark:text-white">{claimData.flightInfo.flightNumber}</p>
                </div>
                
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Airline</p>
                  <p className="font-medium text-gray-900 dark:text-white">{claimData.flightInfo.airline}</p>
                </div>
                
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Flight Date</p>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {new Date(claimData.flightInfo.departureDate).toLocaleDateString()}
                  </p>
                </div>
                
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Submitted</p>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {new Date(claimData.submittedAt).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>

            {/* Compensation */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Expected Compensation
              </h3>
              
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-green-800 dark:text-green-200">
                      Estimated Amount
                    </p>
                    <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                      {claimData.compensationAmount} {claimData.currency}
                    </p>
                  </div>
                  
                  <div className="text-green-600 dark:text-green-400">
                    <Plane className="h-8 w-8" />
                  </div>
                </div>
              </div>
            </div>

            {/* Next Steps */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                What Happens Next?
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-start space-x-3">
                  <Mail className="h-5 w-5 text-primary-600 dark:text-primary-400 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Email Confirmation
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      You'll receive a confirmation email with your claim details within minutes.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <Clock className="h-5 w-5 text-primary-600 dark:text-primary-400 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Processing Time
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      We'll review your claim and respond within 2-4 weeks.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <FileText className="h-5 w-5 text-primary-600 dark:text-primary-400 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Updates
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      We'll keep you informed about the progress of your claim.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/status"
            className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
          >
            Track Your Claim
            <ArrowRight className="ml-2 h-5 w-5" />
          </Link>
          
          <button
            onClick={handleEmailConfirmation}
            className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 dark:border-gray-600 text-base font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
          >
            <Mail className="mr-2 h-5 w-5" />
            Resend Confirmation
          </button>
        </div>

        {/* Additional Information */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Need help?{' '}
            <a
              href="mailto:support@easyairclaim.com"
              className="font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
            >
              Contact our support team
            </a>
            {' '}or call us at{' '}
            <a
              href="tel:+441234567890"
              className="font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
            >
              +44 123 456 7890
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}