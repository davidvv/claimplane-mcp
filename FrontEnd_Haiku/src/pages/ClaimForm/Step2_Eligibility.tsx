import React from 'react';
import { ArrowLeft, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { EligibilityResponse } from '../../types/openapi';
import { FlightInfo } from '../../types/openapi';

interface Step2EligibilityProps {
  flightInfo?: FlightInfo;
  initialData?: EligibilityResponse;
  onComplete: (data: EligibilityResponse) => void;
  onBack: () => void;
}

export default function Step2_Eligibility({ flightInfo, initialData, onComplete, onBack }: Step2EligibilityProps) {
  // Mock eligibility data for demo
  const mockEligibility: EligibilityResponse = initialData || {
    eligible: true,
    compensationAmount: 600,
    currency: 'EUR',
    regulation: 'EU261',
    reasons: [
      'Flight delayed by 105 minutes',
      'Departure within EU jurisdiction',
      'Delay within airline control'
    ],
    requirements: [
      'Boarding pass copy',
      'Valid ID or passport',
      'Proof of booking'
    ]
  };

  const handleContinue = () => {
    onComplete(mockEligibility);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Eligibility Check
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Based on your flight information, here's your eligibility for compensation.
        </p>
      </div>

      {/* Flight Summary */}
      {flightInfo && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Flight Summary</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600 dark:text-gray-400">Flight</p>
              <p className="font-medium text-gray-900 dark:text-white">{flightInfo.flightNumber}</p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Status</p>
              <p className="font-medium text-gray-900 dark:text-white capitalize">{flightInfo.status}</p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Delay</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {flightInfo.delayMinutes ? `${flightInfo.delayMinutes} minutes` : 'No delay'}
              </p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Date</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {new Date(flightInfo.departureDate).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Eligibility Result */}
      <div className={`mb-6 p-6 rounded-lg border-2 ${
        mockEligibility.eligible 
          ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
          : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
      }`}>
        <div className="flex items-center mb-4">
          {mockEligibility.eligible ? (
            <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400 mr-2" />
          ) : (
            <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400 mr-2" />
          )}
          <h3 className={`text-lg font-semibold ${
            mockEligibility.eligible ? 'text-green-900 dark:text-green-100' : 'text-red-900 dark:text-red-100'
          }`}>
            {mockEligibility.eligible ? '✅ You are eligible!' : '❌ Not eligible'}
          </h3>
        </div>

        {mockEligibility.compensationAmount && (
          <div className="mb-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Estimated Compensation</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {mockEligibility.compensationAmount} {mockEligibility.currency}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Under {mockEligibility.regulation} regulation
            </p>
          </div>
        )}

        {/* Reasons */}
        {mockEligibility.reasons && mockEligibility.reasons.length > 0 && (
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Why you're {mockEligibility.eligible ? 'eligible' : 'not eligible'}:</p>
            <ul className="space-y-1">
              {mockEligibility.reasons.map((reason, index) => (
                <li key={index} className="text-sm text-gray-600 dark:text-gray-400 flex items-start">
                  <span className="mr-2">•</span>
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Requirements */}
        {mockEligibility.requirements && mockEligibility.requirements.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Required documents:</p>
            <ul className="space-y-1">
              {mockEligibility.requirements.map((req, index) => (
                <li key={index} className="text-sm text-gray-600 dark:text-gray-400 flex items-start">
                  <Clock className="h-3 w-3 mr-2 mt-0.5 text-gray-400" />
                  {req}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </button>
        
        <button
          type="button"
          onClick={handleContinue}
          className="inline-flex items-center px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
        >
          Continue
        </button>
      </div>
    </div>
  );
}