import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Plane, Calendar, Search, Clock, AlertCircle } from 'lucide-react';
import { flightLookupSchema } from '../../schemas';
import { getFlightStatus, getMockFlightStatus } from '../../services/flights';
import { FlightInfo } from '../../types/openapi';
import { toast } from 'sonner';

interface Step1FlightProps {
  initialData?: FlightInfo;
  onComplete: (data: FlightInfo) => void;
}

export default function Step1_Flight({ initialData, onComplete }: Step1FlightProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [flightData, setFlightData] = useState<FlightInfo | null>(initialData || null);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm({
    resolver: zodResolver(flightLookupSchema),
    defaultValues: {
      flightNumber: initialData?.flightNumber || '',
      date: initialData?.departureDate || '',
    },
  });

  const watchedFlightNumber = watch('flightNumber');
  const watchedDate = watch('date');

  const onSubmit = async (data: any) => {
    setIsLoading(true);
    
    try {
      // Try to get flight data from API first
      let flightInfo: FlightInfo;
      
      try {
        flightInfo = await getFlightStatus({
          flightNumber: data.flightNumber.toUpperCase(),
          date: data.date,
        });
      } catch (error) {
        // If API fails, use mock data for demo
        console.log('Using mock flight data for demo');
        flightInfo = getMockFlightStatus({
          flightNumber: data.flightNumber.toUpperCase(),
          date: data.date,
        });
      }
      
      setFlightData(flightInfo);
      toast.success('Flight found successfully!');
    } catch (error) {
      toast.error('Flight not found. Please check your flight number and date.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmFlight = () => {
    if (flightData) {
      onComplete(flightData);
    }
  };

  const formatFlightNumber = (value: string) => {
    return value.toUpperCase().replace(/[^A-Z0-9]/g, '');
  };

  const getMinDate = () => {
    const date = new Date();
    date.setFullYear(date.getFullYear() - 1);
    return date.toISOString().split('T')[0];
  };

  const getMaxDate = () => {
    const date = new Date();
    date.setFullYear(date.getFullYear() + 1);
    return date.toISOString().split('T')[0];
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Flight Information
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Enter your flight details to check if you're eligible for compensation.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Flight Number */}
          <div>
            <label htmlFor="flightNumber" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Flight Number
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Plane className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="flightNumber"
                type="text"
                {...register('flightNumber')}
                onChange={(e) => {
                  const formatted = formatFlightNumber(e.target.value);
                  setValue('flightNumber', formatted);
                }}
                placeholder="e.g., LH1234"
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            {errors.flightNumber && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {errors.flightNumber.message}
              </p>
            )}
          </div>

          {/* Flight Date */}
          <div>
            <label htmlFor="date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Flight Date
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Calendar className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="date"
                type="date"
                {...register('date')}
                min={getMinDate()}
                max={getMaxDate()}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            {errors.date && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {errors.date.message}
              </p>
            )}
          </div>
        </div>

        {/* Search Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading || !watchedFlightNumber || !watchedDate}
            className="inline-flex items-center px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Searching...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Search Flight
              </>
            )}
          </button>
        </div>
      </form>

      {/* Flight Results */}
      {flightData && (
        <div className="mt-8 border-t border-gray-200 dark:border-gray-700 pt-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Flight Found
          </h3>
          
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Flight Details
                </h4>
                <p className="text-gray-900 dark:text-white">
                  {flightData.flightNumber} - {flightData.airline}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {flightData.departureAirport} → {flightData.arrivalAirport}
                </p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Status
                </h4>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    flightData.status === 'delayed' ? 'bg-red-500' :
                    flightData.status === 'cancelled' ? 'bg-red-600' :
                    flightData.status === 'diverted' ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}></div>
                  <span className="text-gray-900 dark:text-white capitalize">
                    {flightData.status.replace('_', ' ')}
                  </span>
                </div>
                
                {flightData.delayMinutes && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center mt-1">
                    <Clock className="h-3 w-3 mr-1" />
                    Delayed by {flightData.delayMinutes} minutes
                  </p>
                )}
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Scheduled Time
                </h4>
                <p className="text-gray-900 dark:text-white">
                  {new Date(flightData.scheduledDeparture).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Departure
                </p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Actual Time
                </h4>
                <p className="text-gray-900 dark:text-white">
                  {flightData.actualDeparture 
                    ? new Date(flightData.actualDeparture).toLocaleString()
                    : 'Not available'}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {flightData.actualDeparture ? 'Actual departure' : 'Awaiting update'}
                </p>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={handleConfirmFlight}
                className="inline-flex items-center px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors duration-200"
              >
                Confirm Flight
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium mb-1">Need help finding your flight?</p>
            <p>
              Check your booking confirmation email or airline app. Flight numbers typically start with 
              two letters (airline code) followed by 1-4 digits, like LH1234 or BA2156.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}