/**
 * Step 1: Flight Lookup (Dual-Mode)
 *
 * Phase 6.5: Added route search functionality
 * - Users can now search by route (departure → arrival + date + optional time)
 * - Flight number search remains the default
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Plane, Calendar, Search, MapPin } from 'lucide-react';
import { toast } from 'sonner';

import { flightLookupSchema, type FlightLookupForm } from '@/schemas/validation';
import { getFlightStatus, searchFlightsByRoute } from '@/services/flights';
import type { FlightStatus, FlightSearchResult, Airport } from '@/types/api';
import { AirportAutocomplete } from '@/components/AirportAutocomplete';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Badge } from '@/components/ui/Badge';
import { formatDateTime, getStatusLabel } from '@/lib/utils';

interface Step1Props {
  initialData: FlightStatus | null;
  onComplete: (data: FlightStatus) => void;
}

type InputMode = 'flight-number' | 'route-search';

export function Step1_Flight({ initialData, onComplete }: Step1Props) {
  const [inputMode, setInputMode] = useState<InputMode>('flight-number');
  const [isLoading, setIsLoading] = useState(false);
  const [flightResult, setFlightResult] = useState<FlightStatus | null>(initialData);

  // Route search state
  const [departureAirport, setDepartureAirport] = useState<Airport | null>(null);
  const [arrivalAirport, setArrivalAirport] = useState<Airport | null>(null);
  const [flightDate, setFlightDate] = useState<string>('');
  const [timeFilter, setTimeFilter] = useState<string>('');
  const [searchResults, setSearchResults] = useState<FlightSearchResult[]>([]);

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

  // Flight number search handler (existing functionality)
  const onSubmitFlightNumber = async (data: FlightLookupForm) => {
    setIsLoading(true);

    try {
      const result = await getFlightStatus({
        flightNumber: data.flightNumber.toUpperCase(),
        date: data.departureDate,
      });

      setFlightResult(result);
      setSearchResults([]); // Clear route search results
      toast.success('Flight found!');
    } catch (error: any) {
      // Clear previous results when search fails
      setFlightResult(null);
      setSearchResults([]);
      toast.error(error.response?.data?.error?.message || 'Flight not found. Please check your details.');
      console.error('Flight lookup error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Route search handler (Phase 6.5)
  const onSubmitRouteSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
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
      });

      setSearchResults(response.flights);
      setFlightResult(null); // Clear selected flight

      if (response.flights.length === 0) {
        toast.error('No flights found for this route. Try adjusting your search criteria.');
      } else {
        toast.success(`Found ${response.flights.length} flight${response.flights.length > 1 ? 's' : ''}!`);
      }
    } catch (error: any) {
      // Clear previous results when search fails
      setSearchResults([]);
      setFlightResult(null);
      toast.error(error.response?.data?.detail || 'Route search failed. Please try again.');
      console.error('Route search error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle flight selection from route search results
  const handleSelectFlight = async (flight: FlightSearchResult) => {
    setIsLoading(true);

    try {
      // Fetch full flight details using flight number and date
      const result = await getFlightStatus({
        flightNumber: flight.flightNumber,
        date: flightDate,
      });

      setFlightResult(result);
      setSearchResults([]); // Clear search results
      setInputMode('flight-number'); // Switch back to flight number mode to show result
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

  // Switch mode handler
  const handleModeSwitch = (mode: InputMode) => {
    setInputMode(mode);
    setFlightResult(null);
    setSearchResults([]);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plane className="w-5 h-5" />
            Flight Details
          </CardTitle>
          <CardDescription>
            Find your flight by flight number or search by route
          </CardDescription>
        </CardHeader>

        <CardContent>
          {/* Mode Toggle */}
          <div className="flex gap-2 mb-6">
            <Button
              type="button"
              variant={inputMode === 'flight-number' ? 'default' : 'outline'}
              onClick={() => handleModeSwitch('flight-number')}
              className="flex-1"
            >
              <Plane className="w-4 h-4 mr-2" />
              Flight Number
            </Button>
            <Button
              type="button"
              variant={inputMode === 'route-search' ? 'default' : 'outline'}
              onClick={() => handleModeSwitch('route-search')}
              className="flex-1"
            >
              <Search className="w-4 h-4 mr-2" />
              Route Search
            </Button>
          </div>

          {/* Flight Number Mode */}
          {inputMode === 'flight-number' && (
            <form onSubmit={handleSubmit(onSubmitFlightNumber)} className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                {/* Flight Number */}
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
                    <p className="text-sm text-destructive">
                      {errors.flightNumber.message}
                    </p>
                  )}
                </div>

                {/* Departure Date */}
                <div className="space-y-2">
                  <Label htmlFor="departureDate">Departure Date *</Label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="departureDate"
                      type="date"
                      className="pl-10"
                      max={new Date().toISOString().split('T')[0]}
                      required
                      {...register('departureDate', {
                        required: 'Departure date is required',
                      })}
                    />
                  </div>
                  {errors.departureDate && (
                    <p className="text-sm text-destructive">
                      {errors.departureDate.message}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Enter the scheduled departure date in local time
                  </p>
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
          )}

          {/* Route Search Mode (Phase 6.5) */}
          {inputMode === 'route-search' && (
            <form onSubmit={onSubmitRouteSearch} className="space-y-4">
              {/* Departure Airport */}
              <AirportAutocomplete
                value={departureAirport}
                onChange={setDepartureAirport}
                label="Departure Airport *"
                placeholder="Search by city or airport code (e.g., Munich, MUC)"
              />

              {/* Arrival Airport */}
              <AirportAutocomplete
                value={arrivalAirport}
                onChange={setArrivalAirport}
                label="Arrival Airport *"
                placeholder="Search by city or airport code (e.g., New York, JFK)"
              />

              {/* Flight Date */}
              <div className="space-y-2">
                <Label htmlFor="routeFlightDate">Flight Date *</Label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
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
                <p className="text-xs text-muted-foreground">
                  Must be within the last 6 years (EU261 claim window)
                </p>
              </div>

              {/* Approximate Time (Optional) */}
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
                <p className="text-xs text-muted-foreground">
                  Narrow down your search by approximate departure time
                </p>
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
          )}
        </CardContent>
      </Card>

      {/* Route Search Results (Phase 6.5) */}
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
                className="
                  p-4 border rounded-lg cursor-pointer transition-all
                  hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-gray-800
                  hover:shadow-md
                "
              >
                <div className="flex items-start justify-between gap-4">
                  {/* Flight Info */}
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
                      <p className="text-sm">
                        Departure: {formatDateTime(flight.scheduledDeparture)}
                      </p>
                    )}

                    {/* Delay/Status Badge */}
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

                      {/* Estimated Compensation */}
                      {flight.estimatedCompensation && flight.estimatedCompensation > 0 && (
                        <Badge variant="destructive">
                          €{flight.estimatedCompensation} compensation
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Arrow Icon */}
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

      {/* Flight Result (Existing functionality) */}
      {flightResult && (
        <Card className="fade-in">
          <CardHeader>
            <CardTitle>Flight Found</CardTitle>
            <CardDescription>Review the flight details below</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Basic Info */}
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

            {/* Status */}
            <div>
              <p className="text-sm text-muted-foreground mb-2">Status</p>
              <Badge variant={flightResult.status === 'delayed' || flightResult.status === 'cancelled' ? 'destructive' : 'default'}>
                {getStatusLabel(flightResult.status || 'unknown')}
              </Badge>
            </div>

            {/* Delay Info - Don't show for cancelled flights */}
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

            {/* Cancellation Notice */}
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

            {/* Times */}
            <div className="grid md:grid-cols-2 gap-4 pt-4 border-t">
              {/* Departure Times */}
              {flightResult.scheduledDeparture && (
                <div>
                  <p className="text-sm text-muted-foreground">Scheduled Departure</p>
                  <p className="font-medium">
                    {formatDateTime(flightResult.scheduledDeparture)}
                  </p>
                  {flightResult.actualDeparture && (
                    <>
                      <p className="text-sm text-muted-foreground mt-2">Actual Departure</p>
                      <p className="font-medium">
                        {formatDateTime(flightResult.actualDeparture)}
                      </p>
                    </>
                  )}
                </div>
              )}

              {/* Arrival Times */}
              {flightResult.scheduledArrival && (
                <div>
                  <p className="text-sm text-muted-foreground">Scheduled Arrival</p>
                  <p className="font-medium">
                    {formatDateTime(flightResult.scheduledArrival)}
                  </p>
                  {flightResult.actualArrival && (
                    <>
                      <p className="text-sm text-muted-foreground mt-2">Actual Arrival</p>
                      <p className="font-medium">
                        {formatDateTime(flightResult.actualArrival)}
                      </p>
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
