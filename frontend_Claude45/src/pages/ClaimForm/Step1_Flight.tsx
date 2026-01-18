/**
 * Step 1: Flight Lookup with OCR-First Design
 *
 * Three input modes:
 * 1. Boarding Pass Upload (OCR) - PRIMARY
 * 2. Flight Number Search
 * 3. Route Search
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Plane, Calendar, Search, MapPin, ArrowUpDown, FileUp, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

import { flightLookupSchema, type FlightLookupForm } from '@/schemas/validation';
import { getFlightStatus, searchFlightsByRoute } from '@/services/flights';
import { ocrBoardingPass } from '@/services/claims';
import type { FlightStatus, FlightSearchResult, Airport, OCRResponse } from '@/types/api';
import { AirportAutocomplete } from '@/components/AirportAutocomplete';
import { BoardingPassUploadZone } from '@/components/BoardingPassUploadZone';
import { ExtractedDataPreview, type EditedBoardingPassData } from '@/components/ExtractedDataPreview';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Badge } from '@/components/ui/Badge';
import { formatDateTime, getStatusLabel } from '@/lib/utils';

interface Step1Props {
  initialData: FlightStatus | null;
  onComplete: (data: FlightStatus, ocrData?: OCRData) => void;
  savedOcrResult?: OCRResponse | null;
  setSavedOcrResult?: (result: OCRResponse | null) => void;
}

// OCR data to pass to next steps
export interface OCRData {
  firstName: string;
  lastName: string;
  bookingReference?: string;
  boardingPassFile?: File;
  passengers?: Array<{
    firstName: string;
    lastName: string;
    ticketNumber?: string;
    bookingReference?: string;
  }>;
}

type InputMode = 'boarding-pass' | 'flight-number' | 'route-search';

export function Step1_Flight({ initialData, onComplete, savedOcrResult, setSavedOcrResult }: Step1Props) {
  const [inputMode, setInputMode] = useState<InputMode>('boarding-pass');
  const [isLoading, setIsLoading] = useState(false);
  const [flightResult, setFlightResult] = useState<FlightStatus | null>(initialData);

  // OCR state
  const [boardingPassFile, setBoardingPassFile] = useState<File | null>(null);
  const [ocrResult, setOcrResult] = useState<OCRResponse | null>(savedOcrResult || null);
  // const [ocrError, setOcrError] = useState<string | null>(null); // Unused for now

  // Route search state
  const [departureAirport, setDepartureAirport] = useState<Airport | null>(null);
  const [arrivalAirport, setArrivalAirport] = useState<Airport | null>(null);
  const [flightDate, setFlightDate] = useState<string>('');
  const [timeFilter, setTimeFilter] = useState<string>('');
  const [searchResults, setSearchResults] = useState<FlightSearchResult[]>([]);
  const [swapKey, setSwapKey] = useState<number>(0);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FlightLookupForm>({
    resolver: zodResolver(flightLookupSchema),
    defaultValues: initialData
      ? {
          flightNumber: initialData.flightNumber,
          departureDate: initialData.departureDate,
        }
      : undefined,
  });

  // ==================== OCR Handlers ====================

  const handleFileSelect = async (file: File) => {
    setBoardingPassFile(file);
    // setOcrError(null);
    setIsLoading(true);

    try {
      const result = await ocrBoardingPass(file);

      if (!result.success) {
        const errorMessage = result.errors?.[0] || 'OCR processing failed';
        throw new Error(errorMessage);
      }

      setOcrResult(result);
      if (setSavedOcrResult) {
        setSavedOcrResult(result);
      }
      toast.success('Boarding pass data extracted successfully!');
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to extract data from boarding pass';
      // setOcrError(errorMsg);
      toast.error(errorMsg);
      console.error('OCR error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOCRConfirm = async (editedData: EditedBoardingPassData) => {
    setIsLoading(true);

    try {
      // Fetch full flight details using extracted data
      const result = await getFlightStatus({
        flightNumber: editedData.flightNumber,
        date: editedData.flightDate,
      });

      // Attach the full list of flights for multi-leg journeys
      if (editedData.flights && editedData.flights.length > 0) {
        result.flights = editedData.flights;
      }

      // Pass both flight data and OCR-extracted passenger info
      const ocrData: OCRData = {
        firstName: editedData.firstName,
        lastName: editedData.lastName,
        bookingReference: editedData.bookingReference,
        boardingPassFile: boardingPassFile || undefined,
        // Pass the raw passengers list if available (from email/multi-pax OCR)
        passengers: ocrResult?.data?.passengers?.map((p: any) => ({
          firstName: p.firstName,
          lastName: p.lastName,
          ticketNumber: p.ticketNumber,
          bookingReference: p.bookingReference
        }))
      };

      setFlightResult(result);
      // Don't clear OCR result to allow going back/changing selection
      // setOcrResult(null); 
      toast.success('Flight verified!');
      
      // Complete step with OCR data
      onComplete(result, ocrData);
    } catch (error: any) {
      toast.error(error.response?.data?.error?.message || 'Failed to verify flight. Please enter manually.');
      console.error('Flight verification error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOCRRetry = () => {
    setBoardingPassFile(null);
    setOcrResult(null);
    if (setSavedOcrResult) {
      setSavedOcrResult(null);
    }
    // setOcrError(null);
  };

  const handleChangeFlight = () => {
    setFlightResult(null);
    // If we have OCR data, ensure it's visible
    if (savedOcrResult) {
      setOcrResult(savedOcrResult);
    }
  };

  // ==================== Flight Number Handlers ====================

  const onSubmitFlightNumber = async (data: FlightLookupForm) => {
    setIsLoading(true);

    try {
      const result = await getFlightStatus({
        flightNumber: data.flightNumber.toUpperCase(),
        date: data.departureDate,
      });

      setFlightResult(result);
      setSearchResults([]);
      toast.success('Flight found!');
    } catch (error: any) {
      setFlightResult(null);
      setSearchResults([]);
      toast.error(error.response?.data?.error?.message || 'Flight not found. Please check your details.');
      console.error('Flight lookup error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // ==================== Route Search Handlers ====================

  const onSubmitRouteSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!departureAirport) {
      toast.error('Please select a departure airport');
      return;
    }
    if (!arrivalAirport) {
      toast.error('Please select an arrival airport');
      return;
    }
    if (!flightDate) {
      toast.error('Please select a flight date');
      return;
    }

    setIsLoading(true);

    try {
      const response = await searchFlightsByRoute({
        from: departureAirport.iata,
        to: arrivalAirport.iata,
        date: flightDate,
        time: timeFilter || undefined,
        force_refresh: true,
      });

      setSearchResults(response.flights || []);
      setFlightResult(null);

      if (!response.flights || response.flights.length === 0) {
        toast.error('No flights found for this route. Try adjusting your search criteria.');
      } else {
        toast.success(`Found ${response.flights.length} flight${response.flights.length > 1 ? 's' : ''}!`);
      }
    } catch (error: any) {
      setSearchResults([]);
      setFlightResult(null);
      toast.error(error.response?.data?.detail || 'Route search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectFlight = async (flight: FlightSearchResult) => {
    setIsLoading(true);

    try {
      const result = await getFlightStatus({
        flightNumber: flight.flightNumber,
        date: flightDate,
      });

      setFlightResult(result);
      setSearchResults([]);
      setInputMode('flight-number');
      toast.success('Flight selected!');
    } catch (error: any) {
      // Fallback: Convert flight search result to FlightStatus format
      const fallbackResult: FlightStatus = {
        id: `temp-${Date.now()}`,
        flightNumber: flight.flightNumber,
        airline: flight.airline || 'Unknown',
        departureAirport: flight.departureAirport,
        arrivalAirport: flight.arrivalAirport,
        departureDate: flightDate,
        scheduledDeparture: flight.scheduledDeparture,
        scheduledArrival: flight.scheduledArrival,
        actualDeparture: flight.actualDeparture,
        actualArrival: flight.actualArrival,
        status: flight.status as any,
        delay: flight.delayMinutes,
        delayMinutes: flight.delayMinutes,
        distanceKm: flight.distanceKm,
        lastUpdated: new Date().toISOString(),
        dataSource: 'route_search',
      };

      setFlightResult(fallbackResult);
      setSearchResults([]);
      setInputMode('flight-number');
      toast.success('Flight selected!');
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinue = () => {
    if (flightResult) {
      onComplete(flightResult);
    }
  };

  const handleModeSwitch = (mode: InputMode) => {
    setInputMode(mode);
    setFlightResult(null);
    setSearchResults([]);
    setOcrResult(null);
    setBoardingPassFile(null);
    // setOcrError(null);
  };

  const handleSwapAirports = () => {
    const temp = departureAirport;
    setDepartureAirport(arrivalAirport);
    setArrivalAirport(temp);
    setSwapKey(prev => prev + 1);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plane className="w-5 h-5" />
            Start Your Claim in Seconds
          </CardTitle>
          <CardDescription>
            Upload your boarding pass for instant data extraction, or enter your flight details manually
          </CardDescription>
        </CardHeader>

        <CardContent>
          {/* ==================== Boarding Pass Mode (Primary) ==================== */}
          {inputMode === 'boarding-pass' && !ocrResult && !flightResult && (
            <div className="space-y-6">
              <BoardingPassUploadZone
                onFileSelect={handleFileSelect}
                disabled={isLoading}
                isProcessing={isLoading}
              />

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white dark:bg-gray-900 text-muted-foreground">
                    or enter manually
                  </span>
                </div>
              </div>

              {/* Manual Entry Options */}
              <div className="grid grid-cols-1 xs:grid-cols-2 gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => handleModeSwitch('flight-number')}
                  className="w-full"
                >
                  <Plane className="w-4 h-4 mr-1 sm:mr-2" />
                  <span className="hidden xs:inline">Flight Number</span>
                  <span className="xs:hidden">Flight</span>
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => handleModeSwitch('route-search')}
                  className="w-full"
                >
                  <Search className="w-4 h-4 mr-1 sm:mr-2" />
                  <span className="hidden xs:inline">Route Search</span>
                  <span className="xs:hidden">Route</span>
                </Button>
              </div>
            </div>
          )}

          {/* ==================== OCR Result Preview ==================== */}
          {inputMode === 'boarding-pass' && ocrResult && !flightResult && (
            <ExtractedDataPreview
              data={ocrResult.data}
              fieldConfidence={ocrResult.fieldConfidence}
              confidenceScore={ocrResult.confidenceScore}
              onConfirm={handleOCRConfirm}
              onRetry={handleOCRRetry}
              isLoading={isLoading}
            />
          )}

          {/* ==================== Flight Number Mode ==================== */}
          {inputMode === 'flight-number' && (
            <>
              {/* Back to Upload Button */}
              <div className="mb-4">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => handleModeSwitch('boarding-pass')}
                >
                  <FileUp className="w-4 h-4 mr-2" />
                  Back to Upload
                </Button>
              </div>

              <form onSubmit={handleSubmit(onSubmitFlightNumber)} className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="flightNumber">Flight Number</Label>
                    <div className="relative">
                      <Plane className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                      <Input
                        id="flightNumber"
                        placeholder="e.g., LH1234"
                        className="pl-10"
                        {...register('flightNumber')}
                      />
                    </div>
                    {errors.flightNumber && (
                      <p className="text-sm text-destructive">{errors.flightNumber.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="departureDate">Departure Date *</Label>
                    <div className="relative">
                      <Calendar
                        className="absolute left-3 top-3 w-4 h-4 text-muted-foreground cursor-pointer z-10"
                        onClick={() => (document.getElementById('departureDate') as HTMLInputElement)?.showPicker?.()}
                      />
                      <Input
                        id="departureDate"
                        type="date"
                        className="pl-10"
                        max={new Date().toISOString().split('T')[0]}
                        required
                        {...register('departureDate', { required: 'Departure date is required' })}
                      />
                    </div>
                    {errors.departureDate && (
                      <p className="text-sm text-destructive">{errors.departureDate.message}</p>
                    )}
                  </div>
                </div>

                <Button type="submit" disabled={isLoading} className="w-full">
                  {isLoading ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Searching...
                    </>
                  ) : (
                    'Search Flight'
                  )}
                </Button>
              </form>
            </>
          )}

          {/* ==================== Route Search Mode ==================== */}
          {inputMode === 'route-search' && (
            <>
              {/* Back to Upload Button */}
              <div className="mb-4">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => handleModeSwitch('boarding-pass')}
                >
                  <FileUp className="w-4 h-4 mr-2" />
                  Back to Upload
                </Button>
              </div>

              <form onSubmit={onSubmitRouteSearch} className="space-y-4">
                <AirportAutocomplete
                  key={`departure-${swapKey}`}
                  value={departureAirport}
                  onChange={setDepartureAirport}
                  label="Departure Airport *"
                  placeholder="Search by city or airport code (e.g., Munich, MUC)"
                />

                <div className="flex justify-center -my-2 z-10">
                  <button
                    type="button"
                    onClick={handleSwapAirports}
                    className="rounded-full w-10 h-10 flex items-center justify-center border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-blue-500 transition-all shadow-sm"
                    title="Swap departure and arrival airports"
                  >
                    <ArrowUpDown className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                  </button>
                </div>

                <AirportAutocomplete
                  key={`arrival-${swapKey}`}
                  value={arrivalAirport}
                  onChange={setArrivalAirport}
                  label="Arrival Airport *"
                  placeholder="Search by city or airport code (e.g., New York, JFK)"
                />

                <div className="space-y-2">
                  <Label htmlFor="routeFlightDate">Flight Date *</Label>
                  <div className="relative">
                    <Calendar
                      className="absolute left-3 top-3 w-4 h-4 text-muted-foreground cursor-pointer z-10"
                      onClick={() => (document.getElementById('routeFlightDate') as HTMLInputElement)?.showPicker?.()}
                    />
                    <Input
                      id="routeFlightDate"
                      type="date"
                      className="pl-10"
                      max={new Date().toISOString().split('T')[0]}
                      value={flightDate}
                      onChange={(e) => setFlightDate(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="timeFilter">Approximate Time (Optional)</Label>
                  <select
                    id="timeFilter"
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                    value={timeFilter}
                    onChange={(e) => setTimeFilter(e.target.value)}
                  >
                    <option value="">Any time</option>
                    <option value="morning">Morning (6:00 - 12:00)</option>
                    <option value="afternoon">Afternoon (12:00 - 18:00)</option>
                    <option value="evening">Evening (18:00 - 23:59)</option>
                  </select>
                </div>

                <Button type="submit" disabled={isLoading} className="w-full">
                  {isLoading ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Search Flights
                    </>
                  )}
                </Button>
              </form>
            </>
          )}
        </CardContent>
      </Card>

      {/* Route Search Results */}
      {searchResults.length > 0 && (
        <Card className="fade-in">
          <CardHeader>
            <CardTitle>Search Results</CardTitle>
            <CardDescription>
              {searchResults.length} flight{searchResults.length > 1 ? 's' : ''} found • Click to select
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-3">
            {searchResults.map((flight, index) => (
              <div
                key={`${flight.flightNumber}-${index}`}
                onClick={() => handleSelectFlight(flight)}
                className="p-4 border rounded-lg cursor-pointer transition-all hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-gray-800 hover:shadow-md"
              >
                <div className="flex flex-wrap items-start justify-between gap-2 sm:gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <p className="font-semibold text-lg">{flight.flightNumber}</p>
                      {flight.airline && (
                        <span className="text-sm text-muted-foreground">• {flight.airline}</span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                      <MapPin className="w-4 h-4" />
                      <span>{flight.departureAirport} → {flight.arrivalAirport}</span>
                    </div>

                    {flight.scheduledDeparture && (
                      <p className="text-sm">Departure: {formatDateTime(flight.scheduledDeparture)}</p>
                    )}

                    <div className="mt-2 flex items-center gap-2">
                      <Badge variant={
                        flight.status === 'cancelled' || flight.delayMinutes && flight.delayMinutes >= 180
                          ? 'destructive'
                          : flight.delayMinutes && flight.delayMinutes > 0
                          ? 'default'
                          : 'outline'
                      }>
                        {flight.status === 'cancelled'
                          ? 'Cancelled'
                          : flight.delayMinutes && flight.delayMinutes > 0
                          ? `Delayed ${flight.delayMinutes} min`
                          : 'On Time'
                        }
                      </Badge>

                      {flight.estimatedCompensation && flight.estimatedCompensation > 0 && (
                        <Badge variant="destructive">
                          €{flight.estimatedCompensation} compensation
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="text-muted-foreground">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Flight Result */}
      {flightResult && (
        <Card className="fade-in">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Flight Found</CardTitle>
                <CardDescription>Review the flight details below</CardDescription>
              </div>
              {/* Change Flight Button */}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleChangeFlight}
                className="gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Change Flight
              </Button>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Flight Number</p>
                <p className="font-semibold">{flightResult.flightNumber}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Airline</p>
                <p className="font-semibold">{flightResult.airline}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">From</p>
                <p className="font-semibold">{flightResult.departureAirport}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">To</p>
                <p className="font-semibold">{flightResult.arrivalAirport}</p>
              </div>
            </div>

            <div>
              <p className="text-sm text-muted-foreground mb-2">Status</p>
              <Badge variant={flightResult.status === 'delayed' || flightResult.status === 'cancelled' ? 'destructive' : 'default'}>
                {getStatusLabel(flightResult.status || 'unknown')}
              </Badge>
            </div>

            {flightResult.delay !== null &&
             flightResult.delay !== undefined &&
             flightResult.status?.toLowerCase() !== 'canceled' &&
             flightResult.status?.toLowerCase() !== 'cancelled' && (
              <div className={`rounded-lg p-4 ${
                flightResult.delay > 180
                  ? 'bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800'
                  : flightResult.delay > 0
                  ? 'bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800'
                  : 'bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800'
              }`}>
                <p className={`font-semibold ${
                  flightResult.delay > 180
                    ? 'text-red-900 dark:text-red-200'
                    : flightResult.delay > 0
                    ? 'text-amber-900 dark:text-amber-200'
                    : 'text-green-900 dark:text-green-200'
                }`}>
                  {flightResult.delay > 0
                    ? `Delayed: ${flightResult.delay} minutes (${(flightResult.delay / 60).toFixed(1)} hours)`
                    : flightResult.delay < 0
                    ? `Arrived Early: ${Math.abs(flightResult.delay)} minutes`
                    : 'On Time'
                  }
                </p>
                {flightResult.delay >= 180 && (
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                    You may be eligible for EU261 compensation!
                  </p>
                )}
              </div>
            )}

            {(flightResult.status?.toLowerCase() === 'canceled' ||
              flightResult.status?.toLowerCase() === 'cancelled') && (
              <div className="rounded-lg p-4 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800">
                <p className="font-semibold text-red-900 dark:text-red-200">
                  Flight Cancelled
                </p>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  You may be eligible for EU261 compensation and/or refund!
                </p>
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-4 pt-4 border-t">
              {flightResult.scheduledDeparture && (
                <div>
                  <p className="text-sm text-muted-foreground">Scheduled Departure</p>
                  <p className="font-medium">{formatDateTime(flightResult.scheduledDeparture)}</p>
                  {flightResult.actualDeparture && (
                    <>
                      <p className="text-sm text-muted-foreground mt-2">Actual Departure</p>
                      <p className="font-medium">{formatDateTime(flightResult.actualDeparture)}</p>
                    </>
                  )}
                </div>
              )}

              {flightResult.scheduledArrival && (
                <div>
                  <p className="text-sm text-muted-foreground">Scheduled Arrival</p>
                  <p className="font-medium">{formatDateTime(flightResult.scheduledArrival)}</p>
                  {flightResult.actualArrival && (
                    <>
                      <p className="text-sm text-muted-foreground mt-2">Actual Arrival</p>
                      <p className="font-medium">{formatDateTime(flightResult.actualArrival)}</p>
                    </>
                  )}
                </div>
              )}
            </div>

            <Button onClick={handleContinue} className="w-full mt-4">
              Continue to Eligibility Check
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
