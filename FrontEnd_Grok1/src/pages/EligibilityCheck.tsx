import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import { EligibilityRequest, EligibilityResponse } from '../types/api'

const EligibilityCheck = () => {
  const [formData, setFormData] = useState<EligibilityRequest>({
    flightInfo: {
      flightNumber: '',
      airline: '',
      departureDate: '',
      departureAirport: '',
      arrivalAirport: '',
    },
    customerInfo: {
      email: '',
      region: 'EU' as const,
    },
  })

  const { data: eligibilityData, isLoading, error, refetch } = useQuery<EligibilityResponse>({
    queryKey: ['eligibility', formData],
    queryFn: () => apiClient.checkEligibility(formData),
    enabled: false,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isFormValid()) {
      refetch()
    }
  }

  const handleFlightInfoChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      flightInfo: {
        ...prev.flightInfo,
        [field]: value,
      },
    }))
  }

  const handleCustomerInfoChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      customerInfo: {
        ...prev.customerInfo,
        [field]: value,
      },
    }))
  }

  const isFormValid = () => {
    return (
      formData.flightInfo.flightNumber &&
      formData.flightInfo.airline &&
      formData.flightInfo.departureDate &&
      formData.flightInfo.departureAirport &&
      formData.flightInfo.arrivalAirport &&
      formData.customerInfo.email &&
      formData.customerInfo.region
    )
  }

  const getEligibilityColor = (eligible: boolean) => {
    return eligible
      ? 'text-green-600 bg-green-100'
      : 'text-red-600 bg-red-100'
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Check Compensation Eligibility</h1>
        <p className="text-gray-600">
          Find out if your flight incident qualifies for compensation under EU261, DOT, or CTA regulations.
        </p>
      </div>

      <div className="card mb-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Flight Information */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Flight Information</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="flightNumber" className="block text-sm font-medium text-gray-700 mb-1">
                  Flight Number *
                </label>
                <input
                  type="text"
                  id="flightNumber"
                  value={formData.flightInfo.flightNumber}
                  onChange={(e) => handleFlightInfoChange('flightNumber', e.target.value.toUpperCase())}
                  placeholder="e.g., LH1234"
                  className="input"
                  required
                />
              </div>

              <div>
                <label htmlFor="airline" className="block text-sm font-medium text-gray-700 mb-1">
                  Airline *
                </label>
                <input
                  type="text"
                  id="airline"
                  value={formData.flightInfo.airline}
                  onChange={(e) => handleFlightInfoChange('airline', e.target.value)}
                  placeholder="e.g., Lufthansa"
                  className="input"
                  required
                />
              </div>

              <div>
                <label htmlFor="departureDate" className="block text-sm font-medium text-gray-700 mb-1">
                  Departure Date *
                </label>
                <input
                  type="date"
                  id="departureDate"
                  value={formData.flightInfo.departureDate}
                  onChange={(e) => handleFlightInfoChange('departureDate', e.target.value)}
                  className="input"
                  required
                />
              </div>

              <div>
                <label htmlFor="departureAirport" className="block text-sm font-medium text-gray-700 mb-1">
                  Departure Airport *
                </label>
                <input
                  type="text"
                  id="departureAirport"
                  value={formData.flightInfo.departureAirport}
                  onChange={(e) => handleFlightInfoChange('departureAirport', e.target.value.toUpperCase())}
                  placeholder="e.g., FRA"
                  className="input"
                  required
                />
              </div>

              <div className="md:col-span-2">
                <label htmlFor="arrivalAirport" className="block text-sm font-medium text-gray-700 mb-1">
                  Arrival Airport *
                </label>
                <input
                  type="text"
                  id="arrivalAirport"
                  value={formData.flightInfo.arrivalAirport}
                  onChange={(e) => handleFlightInfoChange('arrivalAirport', e.target.value.toUpperCase())}
                  placeholder="e.g., JFK"
                  className="input"
                  required
                />
              </div>
            </div>
          </div>

          {/* Customer Information */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Passenger Information</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  id="email"
                  value={formData.customerInfo.email}
                  onChange={(e) => handleCustomerInfoChange('email', e.target.value)}
                  placeholder="your.email@example.com"
                  className="input"
                  required
                />
              </div>

              <div>
                <label htmlFor="region" className="block text-sm font-medium text-gray-700 mb-1">
                  Region *
                </label>
                <select
                  id="region"
                  value={formData.customerInfo.region}
                  onChange={(e) => handleCustomerInfoChange('region', e.target.value)}
                  className="input"
                  required
                >
                  <option value="EU">European Union (EU261)</option>
                  <option value="US">United States (DOT)</option>
                  <option value="CA">Canada (CTA)</option>
                </select>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={!isFormValid()}
            className="btn w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Check Eligibility
          </button>
        </form>
      </div>

      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Checking eligibility...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error checking eligibility
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {error instanceof Error ? error.message : 'An unexpected error occurred'}
              </div>
            </div>
          </div>
        </div>
      )}

      {eligibilityData && (
        <div className="card">
          <div className="text-center mb-6">
            <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold ${getEligibilityColor(eligibilityData.eligible)}`}>
              {eligibilityData.eligible ? (
                <>
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Eligible for Compensation
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  Not Eligible for Compensation
                </>
              )}
            </div>
          </div>

          {eligibilityData.eligible && eligibilityData.compensationAmount && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.84L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.84l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">
                    Estimated Compensation: {formatCurrency(eligibilityData.compensationAmount, eligibilityData.currency || 'EUR')}
                  </h3>
                  <div className="mt-2 text-sm text-green-700">
                    <p>Regulation: {eligibilityData.regulation}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Eligibility Details</h3>
              <div className="text-sm text-gray-600">
                <p><strong>Regulation:</strong> {eligibilityData.regulation}</p>
                {eligibilityData.compensationAmount && (
                  <p><strong>Compensation Amount:</strong> {formatCurrency(eligibilityData.compensationAmount, eligibilityData.currency || 'EUR')}</p>
                )}
              </div>
            </div>

            {eligibilityData.reasons && eligibilityData.reasons.length > 0 && (
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Reasons</h3>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {eligibilityData.reasons.map((reason, index) => (
                    <li key={index}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}

            {eligibilityData.requirements && eligibilityData.requirements.length > 0 && (
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Required Documents</h3>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {eligibilityData.requirements.map((requirement, index) => (
                    <li key={index}>{requirement}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {eligibilityData.eligible && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-4">
                  Ready to submit your claim? Make sure you have all required documents ready.
                </p>
                <a href="/submit-claim" className="btn">
                  Submit Claim Now
                </a>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default EligibilityCheck