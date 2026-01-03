/**
 * Step 1: Flight Lookup
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Plane, Calendar } from 'lucide-react';
import { toast } from 'sonner';

import { flightLookupSchema, type FlightLookupForm } from '@/schemas/validation';
import { getFlightStatus } from '@/services/flights';
import type { FlightStatus } from '@/types/api';

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

export function Step1_Flight({ initialData, onComplete }: Step1Props) {
  const [isLoading, setIsLoading] = useState(false);
  const [flightResult, setFlightResult] = useState<FlightStatus | null>(initialData);

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

  const onSubmit = async (data: FlightLookupForm) => {
    setIsLoading(true);

    try {
      const result = await getFlightStatus({
        flightNumber: data.flightNumber.toUpperCase(),
        date: data.departureDate,
      });

      setFlightResult(result);
      toast.success('Flight found!');
    } catch (error: any) {
      toast.error(error.response?.data?.error?.message || 'Flight not found. Please check your details.');
      console.error('Flight lookup error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinue = () => {
    if (flightResult) {
      onComplete(flightResult);
    }
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
            Enter your flight number and departure date to get started
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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
        </CardContent>
      </Card>

      {/* Flight Result */}
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
