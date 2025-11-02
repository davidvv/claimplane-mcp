/**
 * Step 3: Passenger Information and Documents
 */
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { User } from 'lucide-react';
import { Step3PassengerInfoSchema, type Step3FormData } from '@/schemas/validation';
import { useClaimStore } from '@/store/claimStore';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';

export function Step3Passenger() {
  const { formData, updateFormData, nextStep, previousStep, loading } = useClaimStore();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Step3FormData>({
    resolver: zodResolver(Step3PassengerInfoSchema),
    defaultValues: {
      email: formData.email || '',
      firstName: formData.firstName || '',
      lastName: formData.lastName || '',
      phone: formData.phone || '',
      region: formData.region || 'EU',
      address: formData.address || {
        street: '',
        city: '',
        postalCode: '',
        country: '',
      },
      incidentType: formData.incidentType || 'delay',
      notes: formData.notes || '',
    },
  });

  const onSubmit = (data: Step3FormData) => {
    updateFormData(data);
    nextStep();
  };

  return (
    <Card className="mx-auto max-w-2xl">
      <CardHeader>
        <div className="flex items-center space-x-3">
          <div className="rounded-full bg-primary-100 p-3 dark:bg-primary-900">
            <User className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <CardTitle>Passenger Information</CardTitle>
            <CardDescription>
              Please provide your contact details and address
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Contact Information */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
            Contact Details
          </h3>

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="First Name"
              placeholder="John"
              error={errors.firstName?.message}
              required
              {...register('firstName')}
            />

            <Input
              label="Last Name"
              placeholder="Doe"
              error={errors.lastName?.message}
              required
              {...register('lastName')}
            />
          </div>

          <Input
            type="email"
            label="Email Address"
            placeholder="john.doe@example.com"
            error={errors.email?.message}
            helperText="We'll send your claim confirmation here"
            required
            {...register('email')}
          />

          <Input
            type="tel"
            label="Phone Number"
            placeholder="+491234567890"
            error={errors.phone?.message}
            helperText="Include country code (e.g., +49 for Germany)"
            {...register('phone')}
          />

          <Select
            label="Region"
            error={errors.region?.message}
            required
            options={[
              { value: 'EU', label: 'European Union' },
              { value: 'US', label: 'United States' },
              { value: 'CA', label: 'Canada' },
            ]}
            {...register('region')}
          />
        </div>

        {/* Address */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
            Mailing Address
          </h3>

          <Input
            label="Street Address"
            placeholder="123 Main St"
            error={errors.address?.street?.message}
            required
            {...register('address.street')}
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="City"
              placeholder="Berlin"
              error={errors.address?.city?.message}
              required
              {...register('address.city')}
            />

            <Input
              label="Postal Code"
              placeholder="10115"
              error={errors.address?.postalCode?.message}
              required
              {...register('address.postalCode')}
            />
          </div>

          <Input
            label="Country"
            placeholder="Germany"
            error={errors.address?.country?.message}
            required
            {...register('address.country')}
          />
        </div>

        {/* Incident Details */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
            Incident Details
          </h3>

          <Select
            label="Type of Incident"
            error={errors.incidentType?.message}
            required
            options={[
              { value: 'delay', label: 'Flight Delay' },
              { value: 'cancellation', label: 'Flight Cancellation' },
              { value: 'denied_boarding', label: 'Denied Boarding' },
              { value: 'baggage_delay', label: 'Baggage Delay' },
            ]}
            {...register('incidentType')}
          />

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Additional Notes (Optional)
            </label>
            <textarea
              className="flex min-h-[120px] w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-base
                placeholder:text-gray-400
                focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500
                disabled:cursor-not-allowed disabled:opacity-50
                dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              placeholder="Any additional details about your flight disruption..."
              {...register('notes')}
            />
            {errors.notes && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {errors.notes.message}
              </p>
            )}
          </div>
        </div>

        {/* Navigation */}
        <div className="flex justify-between border-t border-gray-200 pt-6 dark:border-gray-700">
          <Button type="button" variant="outline" onClick={previousStep}>
            Back
          </Button>
          <Button type="submit" disabled={loading}>
            Review & Submit
          </Button>
        </div>
      </form>
    </Card>
  );
}
