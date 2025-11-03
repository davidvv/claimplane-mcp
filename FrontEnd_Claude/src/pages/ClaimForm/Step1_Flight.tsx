/**
 * Step 1: Flight Lookup
 */
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Plane } from 'lucide-react';
import { Step1FlightLookupSchema, type Step1FormData } from '@/schemas/validation';
import { flightService } from '@/services/flights';
import { useClaimStore } from '@/store/claimStore';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';

export function Step1Flight() {
  const { formData, updateFormData, nextStep, setLoading, loading } = useClaimStore();
  const [flightNotFound, setFlightNotFound] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Step1FormData>({
    resolver: zodResolver(Step1FlightLookupSchema),
    defaultValues: {
      flightNumber: formData.flightNumber || '',
      departureDate: formData.departureDate || '',
    },
  });

  const onSubmit = async (data: Step1FormData) => {
    setLoading(true);
    setFlightNotFound(false);

    try {
      const flightStatus = await flightService.getFlightStatus(data.flightNumber, {
        date: data.departureDate,
        refresh: false,
      });

      updateFormData({
        flightNumber: data.flightNumber,
        departureDate: data.departureDate,
        flightStatus,
      });

      toast.success('Flight found!');
      nextStep();
    } catch (error) {
      console.error('Flight lookup error:', error);
      setFlightNotFound(true);
      toast.error('Flight not found. Please check your flight number and date.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mx-auto max-w-2xl">
      <CardHeader>
        <div className="flex items-center space-x-3">
          <div className="rounded-full bg-primary-100 p-3 dark:bg-primary-900">
            <Plane className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <CardTitle>Find Your Flight</CardTitle>
            <CardDescription>
              Enter your flight details to check eligibility for compensation
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Input
          label="Flight Number"
          placeholder="e.g., LH1234"
          error={errors.flightNumber?.message}
          helperText="Include the airline code (e.g., LH for Lufthansa)"
          required
          {...register('flightNumber')}
        />

        <Input
          type="date"
          label="Departure Date"
          error={errors.departureDate?.message}
          required
          {...register('departureDate')}
        />

        {flightNotFound && (
          <div className="rounded-lg bg-yellow-50 p-4 dark:bg-yellow-900/20">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              We couldn't find your flight. This doesn't mean you're not eligible! You can
              still continue with your claim, and we'll manually verify your flight details.
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => {
                // Allow manual continuation
                updateFormData({
                  flightNumber: '',
                  departureDate: '',
                });
                nextStep();
              }}
            >
              Continue Without Auto-Fill
            </Button>
          </div>
        )}

        <div className="flex justify-end">
          <Button type="submit" loading={loading} disabled={loading}>
            Search Flight
          </Button>
        </div>
      </form>
    </Card>
  );
}
