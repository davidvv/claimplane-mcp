/**
 * Step 3: Passenger Information & Documents
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { User, Mail, Phone, MapPin, FileText } from 'lucide-react';

import { passengerInfoSchema, type PassengerInfoForm } from '@/schemas/validation';
import type { FlightStatus, EligibilityResponse } from '@/types/api';
import type { UserProfile } from '@/services/auth';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { FileUploadZone } from '@/components/FileUploadZone';

interface Step3Props {
  flightData: FlightStatus;
  eligibilityData: EligibilityResponse;
  initialData: any;
  initialDocuments: any[];
  customerEmail?: string | null;
  userProfile?: UserProfile | null;
  onComplete: (data: PassengerInfoForm, documents: any[]) => void;
  onBack: () => void;
}

export function Step3_Passenger({
  flightData,
  eligibilityData,
  initialData,
  initialDocuments,
  customerEmail,
  userProfile,
  onComplete,
  onBack,
}: Step3Props) {
  const [documents, setDocuments] = useState<any[]>(initialDocuments || []);

  // Merge default values with priority: initialData > customerEmail > userProfile
  const defaultFormValues = {
    incidentType: flightData.status === 'cancelled' ? 'cancellation' : 'delay',
    email: customerEmail || userProfile?.email || '',
    firstName: userProfile?.first_name || '',
    lastName: userProfile?.last_name || '',
    phone: userProfile?.phone || '',
    street: userProfile?.address?.street || '',
    city: userProfile?.address?.city || '',
    postalCode: userProfile?.address?.postalCode || '',
    country: userProfile?.address?.country || '',
    notes: '',
  };

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PassengerInfoForm>({
    resolver: zodResolver(passengerInfoSchema),
    defaultValues: initialData || defaultFormValues,
  });

  const onSubmit = (data: PassengerInfoForm) => {
    if (documents.length === 0) {
      alert('Please upload at least one document (boarding pass or ID).');
      return;
    }

    onComplete(data, documents);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Personal Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-5 h-5" />
            Personal Information
          </CardTitle>
          <CardDescription>
            Please provide your contact details
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            {/* First Name */}
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name *</Label>
              <Input
                id="firstName"
                {...register('firstName')}
              />
              {errors.firstName && (
                <p className="text-sm text-destructive">
                  {errors.firstName.message}
                </p>
              )}
            </div>

            {/* Last Name */}
            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name *</Label>
              <Input
                id="lastName"
                {...register('lastName')}
              />
              {errors.lastName && (
                <p className="text-sm text-destructive">
                  {errors.lastName.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="email">Email Address *</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  className="pl-10"
                  {...register('email')}
                />
              </div>
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email.message}</p>
              )}
            </div>

            {/* Phone */}
            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number (Optional)</Label>
              <div className="relative">
                <Phone className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                <Input
                  id="phone"
                  type="tel"
                  className="pl-10"
                  {...register('phone')}
                />
              </div>
              {errors.phone && (
                <p className="text-sm text-destructive">{errors.phone.message}</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Address */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Address
          </CardTitle>
          <CardDescription>
            Your mailing address for correspondence
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="street">Street Address *</Label>
            <Input
              id="street"
              {...register('street')}
            />
            {errors.street && (
              <p className="text-sm text-destructive">{errors.street.message}</p>
            )}
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="city">City *</Label>
              <Input id="city" {...register('city')} />
              {errors.city && (
                <p className="text-sm text-destructive">{errors.city.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="postalCode">Postal Code *</Label>
              <Input
                id="postalCode"
                {...register('postalCode')}
              />
              {errors.postalCode && (
                <p className="text-sm text-destructive">
                  {errors.postalCode.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="country">Country *</Label>
              <Input
                id="country"
                {...register('country')}
              />
              {errors.country && (
                <p className="text-sm text-destructive">{errors.country.message}</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Incident Details */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Incident Details
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="incidentType">Incident Type *</Label>
            <select
              id="incidentType"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              {...register('incidentType')}
            >
              <option value="delay">Flight Delay</option>
              <option value="cancellation">Flight Cancellation</option>
              <option value="denied_boarding">Denied Boarding</option>
              <option value="baggage_delay">Baggage Delay</option>
            </select>
            {errors.incidentType && (
              <p className="text-sm text-destructive">
                {errors.incidentType.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Additional Notes (Optional)</Label>
            <textarea
              id="notes"
              rows={4}
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Any additional details about your experience..."
              {...register('notes')}
            />
            {errors.notes && (
              <p className="text-sm text-destructive">{errors.notes.message}</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Documents */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Upload your boarding pass, ID, and any other relevant documents
          </CardDescription>
        </CardHeader>

        <CardContent>
          <FileUploadZone
            onFilesChange={setDocuments}
            maxFiles={5}
            maxSizeMB={10}
          />

          <div className="mt-4 bg-muted rounded-lg p-4">
            <p className="text-sm font-medium mb-2">Required Documents:</p>
            <ul className="text-sm text-muted-foreground space-y-1">
              {eligibilityData.requirements?.map((req, index) => (
                <li key={index}>• {req}</li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-2">
        <Button type="button" variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button type="submit" className="flex-1">
          Continue to Review
        </Button>
      </div>
    </form>
  );
}
