import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../lib/api'
import { ClaimRequest, Document } from '../types/api'

const ClaimSubmission = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState<ClaimRequest>({
    customerInfo: {
      email: '',
      firstName: '',
      lastName: '',
      phone: '',
      address: {
        street: '',
        city: '',
        postalCode: '',
        country: '',
      },
    },
    flightInfo: {
      flightNumber: '',
      airline: '',
      departureDate: '',
      departureAirport: '',
      arrivalAirport: '',
    },
    incidentType: 'delay' as const,
    notes: '',
  })

  const [documents, setDocuments] = useState<File[]>([])
  const [uploadedDocuments, setUploadedDocuments] = useState<Document[]>([])

  const submitClaimMutation = useMutation({
    mutationFn: apiClient.submitClaim,
    onSuccess: (data) => {
      navigate(`/claim-status?claimId=${data.id}`)
    },
  })

  const uploadDocumentMutation = useMutation({
    mutationFn: ({ claimId, file, documentType }: { claimId: string; file: File; documentType: string }) =>
      apiClient.uploadDocument(claimId, file, documentType),
    onSuccess: (uploadedDoc) => {
      setUploadedDocuments(prev => [...prev, uploadedDoc])
    },
  })

  const handleCustomerChange = (field: string, value: string) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.')
      setFormData(prev => ({
        ...prev,
        customerInfo: {
          ...prev.customerInfo,
          [parent]: {
            ...(prev.customerInfo as any)[parent],
            [child]: value,
          },
        },
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        customerInfo: {
          ...prev.customerInfo,
          [field]: value,
        },
      }))
    }
  }

  const handleFlightChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      flightInfo: {
        ...prev.flightInfo,
        [field]: value,
      },
    }))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setDocuments(prev => [...prev, ...files])
  }

  const removeDocument = (index: number) => {
    setDocuments(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      // Submit the claim first
      const claimResponse = await submitClaimMutation.mutateAsync(formData)

      // Upload documents if any
      if (documents.length > 0 && claimResponse.id) {
        for (const file of documents) {
          const documentType = getDocumentType(file.name)
          await uploadDocumentMutation.mutateAsync({
            claimId: claimResponse.id,
            file,
            documentType,
          })
        }
      }

      // Navigate to success page
      navigate(`/claim-status?claimId=${claimResponse.id}`)
    } catch (error) {
      console.error('Error submitting claim:', error)
    }
  }

  const getDocumentType = (filename: string): string => {
    const extension = filename.toLowerCase().split('.').pop()
    switch (extension) {
      case 'pdf':
        return 'boarding_pass'
      case 'jpg':
      case 'jpeg':
      case 'png':
        return 'id_document'
      default:
        return 'other'
    }
  }

  const isFormValid = () => {
    return (
      formData.customerInfo.email &&
      formData.customerInfo.firstName &&
      formData.customerInfo.lastName &&
      formData.flightInfo.flightNumber &&
      formData.flightInfo.airline &&
      formData.flightInfo.departureDate &&
      formData.flightInfo.departureAirport &&
      formData.flightInfo.arrivalAirport &&
      formData.incidentType
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Submit Compensation Claim</h1>
        <p className="text-gray-600">
          Fill out the form below to submit your flight compensation claim. Make sure all information is accurate.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Customer Information */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Passenger Information</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
                First Name *
              </label>
              <input
                type="text"
                id="firstName"
                value={formData.customerInfo.firstName}
                onChange={(e) => handleCustomerChange('firstName', e.target.value)}
                className="input"
                required
              />
            </div>

            <div>
              <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
                Last Name *
              </label>
              <input
                type="text"
                id="lastName"
                value={formData.customerInfo.lastName}
                onChange={(e) => handleCustomerChange('lastName', e.target.value)}
                className="input"
                required
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Address *
              </label>
              <input
                type="email"
                id="email"
                value={formData.customerInfo.email}
                onChange={(e) => handleCustomerChange('email', e.target.value)}
                className="input"
                required
              />
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                Phone Number
              </label>
              <input
                type="tel"
                id="phone"
                value={formData.customerInfo.phone || ''}
                onChange={(e) => handleCustomerChange('phone', e.target.value)}
                className="input"
              />
            </div>

            <div className="md:col-span-2">
              <label htmlFor="street" className="block text-sm font-medium text-gray-700 mb-1">
                Street Address
              </label>
              <input
                type="text"
                id="street"
                value={formData.customerInfo.address?.street || ''}
                onChange={(e) => handleCustomerChange('address.street', e.target.value)}
                className="input"
              />
            </div>

            <div>
              <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
                City
              </label>
              <input
                type="text"
                id="city"
                value={formData.customerInfo.address?.city || ''}
                onChange={(e) => handleCustomerChange('address.city', e.target.value)}
                className="input"
              />
            </div>

            <div>
              <label htmlFor="postalCode" className="block text-sm font-medium text-gray-700 mb-1">
                Postal Code
              </label>
              <input
                type="text"
                id="postalCode"
                value={formData.customerInfo.address?.postalCode || ''}
                onChange={(e) => handleCustomerChange('address.postalCode', e.target.value)}
                className="input"
              />
            </div>

            <div>
              <label htmlFor="country" className="block text-sm font-medium text-gray-700 mb-1">
                Country
              </label>
              <input
                type="text"
                id="country"
                value={formData.customerInfo.address?.country || ''}
                onChange={(e) => handleCustomerChange('address.country', e.target.value)}
                className="input"
              />
            </div>
          </div>
        </div>

        {/* Flight Information */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Flight Information</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="flightNumber" className="block text-sm font-medium text-gray-700 mb-1">
                Flight Number *
              </label>
              <input
                type="text"
                id="flightNumber"
                value={formData.flightInfo.flightNumber}
                onChange={(e) => handleFlightChange('flightNumber', e.target.value.toUpperCase())}
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
                onChange={(e) => handleFlightChange('airline', e.target.value)}
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
                onChange={(e) => handleFlightChange('departureDate', e.target.value)}
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
                onChange={(e) => handleFlightChange('departureAirport', e.target.value.toUpperCase())}
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
                onChange={(e) => handleFlightChange('arrivalAirport', e.target.value.toUpperCase())}
                placeholder="e.g., JFK"
                className="input"
                required
              />
            </div>
          </div>
        </div>

        {/* Incident Details */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Incident Details</h2>
          <div className="space-y-6">
            <div>
              <label htmlFor="incidentType" className="block text-sm font-medium text-gray-700 mb-1">
                Type of Incident *
              </label>
              <select
                id="incidentType"
                value={formData.incidentType}
                onChange={(e) => setFormData(prev => ({ ...prev, incidentType: e.target.value as any }))}
                className="input"
                required
              >
                <option value="delay">Flight Delay</option>
                <option value="cancellation">Flight Cancellation</option>
                <option value="denied_boarding">Denied Boarding</option>
                <option value="baggage_delay">Baggage Delay</option>
              </select>
            </div>

            <div>
              <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
                Additional Notes
              </label>
              <textarea
                id="notes"
                value={formData.notes || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                rows={4}
                className="input"
                placeholder="Please provide any additional details about your flight incident..."
              />
            </div>
          </div>
        </div>

        {/* Document Upload */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Supporting Documents</h2>
          <div className="space-y-4">
            <div>
              <label htmlFor="documents" className="block text-sm font-medium text-gray-700 mb-1">
                Upload Documents
              </label>
              <input
                type="file"
                id="documents"
                multiple
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              <p className="mt-1 text-sm text-gray-500">
                Upload boarding passes, ID documents, receipts, or other relevant files (PDF, JPG, PNG)
              </p>
            </div>

            {documents.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Selected Files:</h3>
                <ul className="space-y-2">
                  {documents.map((file, index) => (
                    <li key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                      <span className="text-sm text-gray-700">{file.name}</span>
                      <button
                        type="button"
                        onClick={() => removeDocument(index)}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-center">
          <button
            type="submit"
            disabled={!isFormValid() || submitClaimMutation.isPending}
            className="btn px-8 py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitClaimMutation.isPending ? 'Submitting Claim...' : 'Submit Claim'}
          </button>
        </div>
      </form>

      {submitClaimMutation.isError && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error submitting claim
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {submitClaimMutation.error instanceof Error ? submitClaimMutation.error.message : 'An unexpected error occurred'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ClaimSubmission