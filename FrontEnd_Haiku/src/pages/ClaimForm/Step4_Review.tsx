import React from 'react';
import { ArrowLeft, CheckCircle, Plane, User, Mail, Clock, Upload } from 'lucide-react';
import { FormProgress } from '../../types/openapi';
import { formatFileSize } from '../../services/documents';

interface Step4ReviewProps {
  formData: FormProgress['data'];
  onSubmit: () => void;
  onBack: () => void;
}

export default function Step4_Review({ formData, onSubmit, onBack }: Step4ReviewProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Review Your Claim
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Please review all the information before submitting your claim.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Flight Information Summary */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <Plane className="h-5 w-5 text-primary-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">Flight Information</h3>
          </div>
          
          {formData.flightInfo && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600 dark:text-gray-400">Flight Number</p>
                <p className="font-medium text-gray-900 dark:text-white">{formData.flightInfo.flightNumber}</p>
              </div>
              <div>
                <p className="text-gray-600 dark:text-gray-400">Airline</p>
                <p className="font-medium text-gray-900 dark:text-white">{formData.flightInfo.airline}</p>
              </div>
              <div>
                <p className="text-gray-600 dark:text-gray-400">Date</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {new Date(formData.flightInfo.departureDate).toLocaleDateString()}
                </p>
              </div>
              <div>
                <p className="text-gray-600 dark:text-gray-400">Route</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {formData.flightInfo.departureAirport} → {formData.flightInfo.arrivalAirport}
                </p>
              </div>
              <div>
                <p className="text-gray-600 dark:text-gray-400">Status</p>
                <p className="font-medium text-gray-900 dark:text-white capitalize">{formData.flightInfo.status}</p>
              </div>
              {formData.flightInfo.delayMinutes && (
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Delay</p>
                  <p className="font-medium text-gray-900 dark:text-white">{formData.flightInfo.delayMinutes} minutes</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Eligibility Summary */}
        {formData.eligibility && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center mb-3">
              <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">Eligibility</h3>
            </div>
            
            <div className="space-y-3">
              <div>
                <p className="text-gray-600 dark:text-gray-400">Status</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {formData.eligibility.eligible ? '✅ Eligible for compensation' : '❌ Not eligible'}
                </p>
              </div>
              
              {formData.eligibility.compensationAmount && (
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Estimated Compensation</p>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {formData.eligibility.compensationAmount} {formData.eligibility.currency}
                  </p>
                </div>
              )}
              
              {formData.eligibility.regulation && (
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Regulation</p>
                  <p className="font-medium text-gray-900 dark:text-white">{formData.eligibility.regulation}</p>
                </div>
              )}
              
              {formData.eligibility.reasons && formData.eligibility.reasons.length > 0 && (
                <div>
                  <p className="text-gray-600 dark:text-gray-400 mb-2">Reasons:</p>
                  <ul className="space-y-1">
                    {formData.eligibility.reasons.map((reason, index) => (
                      <li key={index} className="text-sm text-gray-700 dark:text-gray-300 flex items-start">
                        <span className="mr-2">•</span>
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Passenger Information Summary */}
        {formData.customerInfo && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center mb-3">
              <User className="h-5 w-5 text-primary-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">Passenger Information</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600 dark:text-gray-400">Name</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {formData.customerInfo.firstName} {formData.customerInfo.lastName}
                </p>
              </div>
              <div>
                <p className="text-gray-600 dark:text-gray-400">Email</p>
                <p className="font-medium text-gray-900 dark:text-white">{formData.customerInfo.email}</p>
              </div>
              {formData.customerInfo.phone && (
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Phone</p>
                  <p className="font-medium text-gray-900 dark:text-white">{formData.customerInfo.phone}</p>
                </div>
              )}
              {formData.customerInfo.address && formData.customerInfo.address.country && (
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Country</p>
                  <p className="font-medium text-gray-900 dark:text-white">{formData.customerInfo.address.country}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Documents Summary */}
        {formData.documents && formData.documents.length > 0 && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center mb-3">
              <Upload className="h-5 w-5 text-primary-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">Uploaded Documents</h3>
            </div>
            
            <div className="space-y-2">
              {formData.documents.map((doc, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-gray-200 dark:bg-gray-600 rounded flex items-center justify-center mr-3">
                      <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                        {doc.filename.split('.').pop()?.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{doc.filename}</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">{formatFileSize(doc.size)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Terms and Conditions */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-start">
            <input
              id="terms"
              type="checkbox"
              required
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded mt-1"
            />
            <label htmlFor="terms" className="ml-3 text-sm text-gray-700 dark:text-gray-300">
              I agree to the{' '}
              <a href="#" className="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300">
                Terms of Service
              </a>{' '}
              and{' '}
              <a href="#" className="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300">
                Privacy Policy
              </a>
              . I confirm that the information provided is accurate and complete.
            </label>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex justify-between pt-6">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </button>
          
          <button
            type="submit"
            className="inline-flex items-center px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
          >
            Submit Claim
          </button>
        </div>
      </form>
    </div>
  );
}