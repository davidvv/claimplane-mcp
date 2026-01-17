/**
 * Step 3: Passenger Information & Documents
 *
 * Workflow v2: If draftClaimId is provided, files are uploaded
 * progressively to the draft claim as the user selects them.
 * 
 * Supports Multi-Passenger Claims (Phase 5).
 */

import { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { User, Mail, Phone, FileText, Sparkles, Plus, Trash2, Users } from 'lucide-react';

import { passengerInfoSchema, type PassengerInfoForm } from '@/schemas/validation';
import type { FlightStatus, EligibilityResponse } from '@/types/api';
import type { UserProfile } from '@/services/auth';
import type { OCRData } from './Step1_Flight';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/Badge';
import { FileUploadZone } from '@/components/FileUploadZone';

interface Step3Props {
  flightData: FlightStatus;
  eligibilityData: EligibilityResponse;
  initialData: any;
  initialDocuments: any[];
  customerEmail?: string | null;
  userProfile?: UserProfile | null;
  draftClaimId?: string | null;  // Workflow v2: Draft claim ID for progressive upload
  ocrData?: OCRData | null;  // OCR-extracted data from boarding pass
  onComplete: (data: PassengerInfoForm, documents: any[]) => void;
  onBack: () => void;
}

export function Step3_Passenger({
  flightData,
  initialData,
  initialDocuments,
  customerEmail,
  userProfile,
  draftClaimId,
  ocrData,
  onComplete,
  onBack,
}: Step3Props) {
  const [documents, setDocuments] = useState<any[]>(initialDocuments || []);
  const [countryCode, setCountryCode] = useState('');  // No default - user must select
  const [phoneNumber, setPhoneNumber] = useState('');

  // Mapping from phone prefix to country name
  const phoneToCountryMap: Record<string, string> = {
    '+49': 'Germany', '+43': 'Austria', '+41': 'Switzerland', '+44': 'United Kingdom',
    '+33': 'France', '+39': 'Italy', '+34': 'Spain', '+31': 'Netherlands',
    '+32': 'Belgium', '+45': 'Denmark', '+46': 'Sweden', '+47': 'Norway',
    '+48': 'Poland', '+351': 'Portugal', '+353': 'Ireland', '+420': 'Czech Republic',
    '+30': 'Greece', '+1': 'United States', '+90': 'Turkey', '+971': 'United Arab Emirates',
    '+81': 'Japan', '+86': 'China', '+82': 'South Korea', '+91': 'India',
    '+61': 'Australia', '+55': 'Brazil', '+52': 'Mexico',
  };

  // Helper to determine initial passengers list
  const getInitialPassengers = () => {
    // 1. If we have saved form data with passengers list, use it
    if (initialData?.passengers?.length > 0) {
      return initialData.passengers;
    }
    
    // 2. If we have legacy saved form data (flat fields), migrate it
    if (initialData?.firstName) {
      return [{
        firstName: initialData.firstName,
        lastName: initialData.lastName,
        ticketNumber: initialData.ticketNumber || '',
        bookingReference: initialData.bookingReference || ''
      }];
    }

    // 3. If we have OCR data with multiple passengers, use it
    if (ocrData?.passengers?.length) {
      return ocrData.passengers.map((p: any) => ({
        firstName: p.firstName || '',
        lastName: p.lastName || '',
        ticketNumber: p.ticketNumber || '',
        bookingReference: p.bookingReference || ''
      }));
    }

    // 4. Default: Single passenger from profile/OCR/email
    return [{
      firstName: ocrData?.firstName || userProfile?.first_name || '',
      lastName: ocrData?.lastName || userProfile?.last_name || '',
      ticketNumber: '',
      bookingReference: ocrData?.bookingReference || ''
    }];
  };

  // Merge default values
  const defaultFormValues = {
    // Contact Info (Account Holder)
    email: initialData?.email || customerEmail || userProfile?.email || '',
    phone: initialData?.phone || userProfile?.phone || '',
    street: initialData?.street || userProfile?.address?.street || '',
    city: initialData?.city || userProfile?.address?.city || '',
    postalCode: initialData?.postalCode || userProfile?.address?.postalCode || '',
    country: initialData?.country || userProfile?.address?.country || '',
    
    // Booking & Incident
    bookingReference: initialData?.bookingReference || ocrData?.bookingReference || '',
    incidentType: initialData?.incidentType || (flightData.status === 'cancelled' ? 'cancellation' : 'delay'),
    notes: initialData?.notes || '',

    // Passengers List
    passengers: getInitialPassengers(),
  };

  const {
    register,
    control,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<PassengerInfoForm>({
    resolver: zodResolver(passengerInfoSchema),
    defaultValues: defaultFormValues,
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "passengers"
  });

  // Initialize phone number
  useEffect(() => {
    const existingPhone = defaultFormValues.phone;
    if (existingPhone && existingPhone.startsWith('+')) {
      const match = existingPhone.match(/^(\+\d{1,4})(\d+)$/);
      if (match) {
        setCountryCode(match[1]);
        setPhoneNumber(match[2]);
      }
    }
  }, []);

  const onSubmit = (data: PassengerInfoForm) => {
    if (documents.length === 0) {
      alert('Please upload at least one document (boarding pass or ID).');
      return;
    }
    onComplete(data, documents);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      
      {/* Contact Information (Account Holder) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5" />
            Contact Information
          </CardTitle>
          <CardDescription>
            Where should we send updates about your claim?
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address *</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  className="pl-10"
                  autoComplete="email"
                  {...register('email')}
                />
              </div>
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number (Optional)</Label>
              <div className="flex gap-2">
                <select
                  value={countryCode}
                  onChange={(e) => {
                    const newCode = e.target.value;
                    setCountryCode(newCode);
                    const mappedCountry = phoneToCountryMap[newCode];
                    if (mappedCountry) {
                      setValue('country', mappedCountry, { shouldValidate: true });
                    }
                  }}
                  className="w-[140px] flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">Select...</option>
                  <option value="+49">🇩🇪 +49</option>
                  <option value="+44">🇬🇧 +44</option>
                  <option value="+1">🇺🇸 +1</option>
                  {/* Add more as needed, keeping it brief for render */}
                  <option value="+33">🇫🇷 +33</option>
                  <option value="+34">🇪🇸 +34</option>
                </select>
                <div className="relative flex-1">
                  <Phone className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="123456789"
                    className="pl-10"
                    value={phoneNumber}
                    onChange={(e) => {
                      const num = e.target.value.replace(/\D/g, '');
                      setPhoneNumber(num);
                    }}
                  />
                  <input
                    type="hidden"
                    {...register('phone')}
                    value={phoneNumber ? `${countryCode}${phoneNumber}` : ''}
                  />
                </div>
              </div>
              {errors.phone && (
                <p className="text-sm text-destructive">{errors.phone.message}</p>
              )}
            </div>
          </div>

          {/* Address Fields */}
          <div className="space-y-2">
            <Label htmlFor="street">Street Address *</Label>
            <Input id="street" autoComplete="street-address" {...register('street')} />
            {errors.street && <p className="text-sm text-destructive">{errors.street.message}</p>}
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="city">City *</Label>
              <Input id="city" autoComplete="address-level2" {...register('city')} />
              {errors.city && <p className="text-sm text-destructive">{errors.city.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="postalCode">Postal Code *</Label>
              <Input id="postalCode" autoComplete="postal-code" {...register('postalCode')} />
              {errors.postalCode && <p className="text-sm text-destructive">{errors.postalCode.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="country">Country *</Label>
              <Input id="country" autoComplete="country-name" {...register('country')} />
              {errors.country && <p className="text-sm text-destructive">{errors.country.message}</p>}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Passengers List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Passengers
          </CardTitle>
          <CardDescription>
            Enter details for all passengers claiming compensation
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {fields.map((field, index) => (
            <div key={field.id} className="relative">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <User className="w-4 h-4" />
                  Passenger {index + 1}
                </h4>
                {fields.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:text-destructive/90 hover:bg-destructive/10"
                    onClick={() => remove(index)}
                  >
                    <Trash2 className="w-4 h-4 mr-1" />
                    Remove
                  </Button>
                )}
              </div>

              <div className="grid md:grid-cols-2 gap-4 p-4 border rounded-lg bg-gray-50/50 dark:bg-gray-900/50">
                {/* First Name */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Label htmlFor={`passengers.${index}.firstName`}>First Name *</Label>
                    {ocrData?.passengers?.[index]?.firstName && (
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800 text-[10px] px-1 py-0 h-5">
                        <Sparkles className="w-3 h-3 mr-1" />
                        OCR
                      </Badge>
                    )}
                  </div>
                  <Input
                    {...register(`passengers.${index}.firstName`)}
                    placeholder="e.g. John"
                  />
                  {errors.passengers?.[index]?.firstName && (
                    <p className="text-sm text-destructive">
                      {errors.passengers[index]?.firstName?.message}
                    </p>
                  )}
                </div>

                {/* Last Name */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Label htmlFor={`passengers.${index}.lastName`}>Last Name *</Label>
                  </div>
                  <Input
                    {...register(`passengers.${index}.lastName`)}
                    placeholder="e.g. Doe"
                  />
                  {errors.passengers?.[index]?.lastName && (
                    <p className="text-sm text-destructive">
                      {errors.passengers[index]?.lastName?.message}
                    </p>
                  )}
                </div>

                {/* Ticket Number */}
                <div className="space-y-2">
                  <Label htmlFor={`passengers.${index}.ticketNumber`}>Ticket Number (Optional)</Label>
                  <Input
                    {...register(`passengers.${index}.ticketNumber`)}
                    placeholder="13-digit number"
                  />
                </div>
              </div>
            </div>
          ))}

          <Button
            type="button"
            variant="outline"
            className="w-full border-dashed"
            onClick={() => append({ firstName: '', lastName: '', ticketNumber: '' })}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Another Passenger
          </Button>
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
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="incidentType">Incident Type *</Label>
              <select
                id="incidentType"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                {...register('incidentType')}
              >
                <option value="delay">Flight Delay</option>
                <option value="cancellation">Flight Cancellation</option>
                <option value="denied_boarding">Denied Boarding</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="bookingReference">Booking Reference (Group)</Label>
              <Input
                {...register('bookingReference')}
                placeholder="e.g. ABC123"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Additional Notes (Optional)</Label>
            <textarea
              id="notes"
              rows={3}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              {...register('notes')}
            />
          </div>
        </CardContent>
      </Card>

      {/* Documents */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Upload documents for ALL passengers
          </CardDescription>
        </CardHeader>

        <CardContent>
          <FileUploadZone
            onFilesChange={setDocuments}
            maxFiles={10} // Increased for families
            maxSizeMB={10}
            claimId={draftClaimId || undefined}
          />
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
