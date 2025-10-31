import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import { Claim, Document } from '../types/api'

const ClaimStatus = () => {
  const [searchParams] = useSearchParams()
  const [claimId, setClaimId] = useState(searchParams.get('claimId') || '')
  const [inputClaimId, setInputClaimId] = useState('')

  const { data: claimData, isLoading, error, refetch } = useQuery<Claim>({
    queryKey: ['claim', claimId],
    queryFn: () => apiClient.getClaim(claimId),
    enabled: !!claimId,
  })

  useEffect(() => {
    const urlClaimId = searchParams.get('claimId')
    if (urlClaimId) {
      setClaimId(urlClaimId)
      setInputClaimId(urlClaimId)
    }
  }, [searchParams])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputClaimId.trim()) {
      setClaimId(inputClaimId.trim())
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'text-gray-600 bg-gray-100'
      case 'submitted':
        return 'text-blue-600 bg-blue-100'
      case 'under_review':
        return 'text-yellow-600 bg-yellow-100'
      case 'approved':
        return 'text-green-600 bg-green-100'
      case 'rejected':
        return 'text-red-600 bg-red-100'
      case 'paid':
        return 'text-purple-600 bg-purple-100'
      case 'closed':
        return 'text-gray-600 bg-gray-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusText = (status: string) => {
    return status.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  }

  const downloadDocument = async (documentId: string, filename: string) => {
    try {
      const blob = await apiClient.downloadDocument(documentId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading document:', error)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Claim Status</h1>
        <p className="text-gray-600">
          Check the status of your compensation claim using your claim ID.
        </p>
      </div>

      {/* Search Form */}
      <div className="card mb-8">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="flex-1">
            <label htmlFor="claimId" className="block text-sm font-medium text-gray-700 mb-1">
              Claim ID
            </label>
            <input
              type="text"
              id="claimId"
              value={inputClaimId}
              onChange={(e) => setInputClaimId(e.target.value)}
              placeholder="Enter your claim ID (e.g., 123e4567-e89b-12d3-a456-426614174000)"
              className="input"
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={!inputClaimId.trim()}
              className="btn disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Search
            </button>
          </div>
        </form>
      </div>

      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading claim details...</p>
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
                Error loading claim
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {error instanceof Error ? error.message : 'Claim not found or access denied'}
              </div>
            </div>
          </div>
        </div>
      )}

      {claimData && (
        <div className="space-y-6">
          {/* Claim Overview */}
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Claim Overview</h2>
              <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(claimData.status!)}`}>
                {getStatusText(claimData.status!)}
              </span>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Claim Details</h3>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Claim ID</dt>
                    <dd className="text-sm text-gray-900 font-mono">{claimData.id}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Incident Type</dt>
                    <dd className="text-sm text-gray-900 capitalize">{claimData.incidentType.replace('_', ' ')}</dd>
                  </div>
                  {claimData.compensationAmount && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Compensation Amount</dt>
                      <dd className="text-sm text-gray-900 font-semibold">
                        {formatCurrency(claimData.compensationAmount, claimData.currency || 'EUR')}
                      </dd>
                    </div>
                  )}
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Submitted</dt>
                    <dd className="text-sm text-gray-900">{formatDateTime(claimData.submittedAt!)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                    <dd className="text-sm text-gray-900">{formatDateTime(claimData.updatedAt!)}</dd>
                  </div>
                </dl>
              </div>

              <div>
                <h3 className="font-medium text-gray-900 mb-2">Flight Information</h3>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Flight</dt>
                    <dd className="text-sm text-gray-900">{claimData.flightInfo.flightNumber} - {claimData.flightInfo.airline}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Route</dt>
                    <dd className="text-sm text-gray-900">{claimData.flightInfo.departureAirport} → {claimData.flightInfo.arrivalAirport}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Date</dt>
                    <dd className="text-sm text-gray-900">{claimData.flightInfo.departureDate}</dd>
                  </div>
                  {claimData.flightInfo.delayMinutes && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Delay</dt>
                      <dd className="text-sm text-gray-900">{claimData.flightInfo.delayMinutes} minutes</dd>
                    </div>
                  )}
                </dl>
              </div>
            </div>

            {claimData.notes && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="font-medium text-gray-900 mb-2">Additional Notes</h3>
                <p className="text-sm text-gray-600">{claimData.notes}</p>
              </div>
            )}
          </div>

          {/* Documents */}
          {claimData.documents && claimData.documents.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Supporting Documents</h2>
              <div className="space-y-3">
                {claimData.documents.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <svg className="h-8 w-8 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                        <p className="text-xs text-gray-500">
                          {doc.documentType.replace('_', ' ').toUpperCase()} • {(doc.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => downloadDocument(doc.id!, doc.filename)}
                      className="btn-secondary text-sm"
                    >
                      Download
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Status Timeline */}
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Claim Timeline</h2>
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">Claim Submitted</p>
                  <p className="text-sm text-gray-500">{formatDateTime(claimData.submittedAt!)}</p>
                </div>
              </div>

              {claimData.status !== 'submitted' && claimData.status !== 'draft' && (
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      ['approved', 'paid', 'closed'].includes(claimData.status!)
                        ? 'bg-green-100'
                        : claimData.status === 'rejected'
                        ? 'bg-red-100'
                        : 'bg-yellow-100'
                    }`}>
                      <svg className={`w-4 h-4 ${
                        ['approved', 'paid', 'closed'].includes(claimData.status!)
                          ? 'text-green-600'
                          : claimData.status === 'rejected'
                          ? 'text-red-600'
                          : 'text-yellow-600'
                      }`} fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-900">
                      {getStatusText(claimData.status!)}
                    </p>
                    <p className="text-sm text-gray-500">{formatDateTime(claimData.updatedAt!)}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ClaimStatus