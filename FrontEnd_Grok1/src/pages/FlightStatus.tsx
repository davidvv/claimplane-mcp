import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import { FlightStatus } from '../types/api'

const FlightStatusPage = () => {
  const [flightNumber, setFlightNumber] = useState('')
  const [date, setDate] = useState('')
  const [refresh, setRefresh] = useState(false)

  const { data: flightData, isLoading, error, refetch } = useQuery<FlightStatus>({
    queryKey: ['flightStatus', flightNumber, date, refresh],
    queryFn: () => apiClient.getFlightStatus(flightNumber, date, refresh),
    enabled: false, // Only run when manually triggered
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (flightNumber && date) {
      refetch()
    }
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled':
        return 'text-blue-600 bg-blue-100'
      case 'delayed':
        return 'text-yellow-600 bg-yellow-100'
      case 'cancelled':
        return 'text-red-600 bg-red-100'
      case 'departed':
      case 'arrived':
        return 'text-green-600 bg-green-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Check Flight Status</h1>
        <p className="text-gray-600">
          Enter your flight details to check the current status and information.
        </p>
      </div>

      <div className="card mb-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="flightNumber" className="block text-sm font-medium text-gray-700 mb-1">
              Flight Number *
            </label>
            <input
              type="text"
              id="flightNumber"
              value={flightNumber}
              onChange={(e) => setFlightNumber(e.target.value.toUpperCase())}
              placeholder="e.g., LH1234"
              className="input"
              required
            />
          </div>

          <div>
            <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-1">
              Flight Date *
            </label>
            <input
              type="date"
              id="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="input"
              required
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="refresh"
              checked={refresh}
              onChange={(e) => setRefresh(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="refresh" className="ml-2 block text-sm text-gray-700">
              Force refresh from external data source
            </label>
          </div>

          <button
            type="submit"
            disabled={!flightNumber || !date}
            className="btn w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Check Flight Status
          </button>
        </form>
      </div>

      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Checking flight status...</p>
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
                Error checking flight status
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {error instanceof Error ? error.message : 'An unexpected error occurred'}
              </div>
            </div>
          </div>
        </div>
      )}

      {flightData && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Flight Information</h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Flight Details</h3>
              <dl className="space-y-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Flight Number</dt>
                  <dd className="text-sm text-gray-900">{flightData.flightNumber}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Airline</dt>
                  <dd className="text-sm text-gray-900">{flightData.airline}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Route</dt>
                  <dd className="text-sm text-gray-900">{flightData.departureAirport} → {flightData.arrivalAirport}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Flight Date</dt>
                  <dd className="text-sm text-gray-900">{flightData.departureDate}</dd>
                </div>
              </dl>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">Status & Schedule</h3>
              <dl className="space-y-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd className="text-sm">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(flightData.status)}`}>
                      {flightData.status.charAt(0).toUpperCase() + flightData.status.slice(1)}
                    </span>
                  </dd>
                </div>
                {flightData.delayMinutes && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Delay</dt>
                    <dd className="text-sm text-gray-900">{flightData.delayMinutes} minutes</dd>
                  </div>
                )}
                {flightData.scheduledDeparture && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Scheduled Departure</dt>
                    <dd className="text-sm text-gray-900">{formatDateTime(flightData.scheduledDeparture)}</dd>
                  </div>
                )}
                {flightData.actualDeparture && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Actual Departure</dt>
                    <dd className="text-sm text-gray-900">{formatDateTime(flightData.actualDeparture)}</dd>
                  </div>
                )}
                {flightData.scheduledArrival && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Scheduled Arrival</dt>
                    <dd className="text-sm text-gray-900">{formatDateTime(flightData.scheduledArrival)}</dd>
                  </div>
                )}
                {flightData.actualArrival && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Actual Arrival</dt>
                    <dd className="text-sm text-gray-900">{formatDateTime(flightData.actualArrival)}</dd>
                  </div>
                )}
              </dl>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="text-sm text-gray-500">
              <p>Last updated: {formatDateTime(flightData.lastUpdated)}</p>
              <p>Data source: {flightData.dataSource}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default FlightStatusPage