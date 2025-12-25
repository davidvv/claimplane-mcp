/**
 * Step 3: Passenger Information & Documents
 */

import { useState, useEffect } from 'react';
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
  const [countryCode, setCountryCode] = useState('+1');
  const [phoneNumber, setPhoneNumber] = useState('');

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

  // Initialize phone number from existing data
  useEffect(() => {
    const existingPhone = initialData?.phone || userProfile?.phone || '';
    if (existingPhone && existingPhone.startsWith('+')) {
      // Extract country code and number
      const match = existingPhone.match(/^(\+\d{1,4})(\d+)$/);
      if (match) {
        setCountryCode(match[1]);
        setPhoneNumber(match[2]);
      }
    }
  }, [initialData, userProfile]);

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
                autoComplete="given-name"
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
                autoComplete="family-name"
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
                  autoComplete="email"
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
              <div className="flex gap-2">
                <select
                  value={countryCode}
                  onChange={(e) => setCountryCode(e.target.value)}
                  className="w-[140px] flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="+1">🇺🇸 +1</option>
                  <option value="+44">🇬🇧 +44</option>
                  <option value="+49">🇩🇪 +49</option>
                  <option value="+33">🇫🇷 +33</option>
                  <option value="+39">🇮🇹 +39</option>
                  <option value="+34">🇪🇸 +34</option>
                  <option value="+31">🇳🇱 +31</option>
                  <option value="+32">🇧🇪 +32</option>
                  <option value="+41">🇨🇭 +41</option>
                  <option value="+43">🇦🇹 +43</option>
                  <option value="+45">🇩🇰 +45</option>
                  <option value="+46">🇸🇪 +46</option>
                  <option value="+47">🇳🇴 +47</option>
                  <option value="+48">🇵🇱 +48</option>
                  <option value="+351">🇵🇹 +351</option>
                  <option value="+353">🇮🇪 +353</option>
                  <option value="+420">🇨🇿 +420</option>
                  <option value="+30">🇬🇷 +30</option>
                  <option value="+90">🇹🇷 +90</option>
                  <option value="+971">🇦🇪 +971</option>
                  <option value="+81">🇯🇵 +81</option>
                  <option value="+86">🇨🇳 +86</option>
                  <option value="+82">🇰🇷 +82</option>
                  <option value="+91">🇮🇳 +91</option>
                  <option value="+61">🇦🇺 +61</option>
                  <option value="+64">🇳🇿 +64</option>
                  <option value="+55">🇧🇷 +55</option>
                  <option value="+52">🇲🇽 +52</option>
                  <option value="+27">🇿🇦 +27</option>
                  <option value="+20">🇪🇬 +20</option>
                  <option value="+7">🇷🇺 +7</option>
                  <option value="+65">🇸🇬 +65</option>
                  <option value="+60">🇲🇾 +60</option>
                  <option value="+66">🇹🇭 +66</option>
                  <option value="+84">🇻🇳 +84</option>
                  <option value="+62">🇮🇩 +62</option>
                  <option value="+63">🇵🇭 +63</option>
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
              <p className="text-xs text-muted-foreground">
                Select your country code and enter your phone number
              </p>
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
              autoComplete="street-address"
              {...register('street')}
            />
            {errors.street && (
              <p className="text-sm text-destructive">{errors.street.message}</p>
            )}
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="city">City *</Label>
              <Input id="city" autoComplete="address-level2" {...register('city')} />
              {errors.city && (
                <p className="text-sm text-destructive">{errors.city.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="postalCode">Postal Code *</Label>
              <Input
                id="postalCode"
                autoComplete="postal-code"
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
              <select
                id="country"
                autoComplete="country-name"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                {...register('country')}
              >
                <option value="">Select a country</option>
                <option value="United States">🇺🇸 United States</option>
                <option value="United Kingdom">🇬🇧 United Kingdom</option>
                <option value="Germany">🇩🇪 Germany</option>
                <option value="France">🇫🇷 France</option>
                <option value="Italy">🇮🇹 Italy</option>
                <option value="Spain">🇪🇸 Spain</option>
                <option value="Netherlands">🇳🇱 Netherlands</option>
                <option value="Belgium">🇧🇪 Belgium</option>
                <option value="Switzerland">🇨🇭 Switzerland</option>
                <option value="Austria">🇦🇹 Austria</option>
                <option value="Denmark">🇩🇰 Denmark</option>
                <option value="Sweden">🇸🇪 Sweden</option>
                <option value="Norway">🇳🇴 Norway</option>
                <option value="Finland">🇫🇮 Finland</option>
                <option value="Poland">🇵🇱 Poland</option>
                <option value="Portugal">🇵🇹 Portugal</option>
                <option value="Ireland">🇮🇪 Ireland</option>
                <option value="Czech Republic">🇨🇿 Czech Republic</option>
                <option value="Greece">🇬🇷 Greece</option>
                <option value="Hungary">🇭🇺 Hungary</option>
                <option value="Romania">🇷🇴 Romania</option>
                <option value="Bulgaria">🇧🇬 Bulgaria</option>
                <option value="Croatia">🇭🇷 Croatia</option>
                <option value="Slovakia">🇸🇰 Slovakia</option>
                <option value="Slovenia">🇸🇮 Slovenia</option>
                <option value="Luxembourg">🇱🇺 Luxembourg</option>
                <option value="Estonia">🇪🇪 Estonia</option>
                <option value="Latvia">🇱🇻 Latvia</option>
                <option value="Lithuania">🇱🇹 Lithuania</option>
                <option value="Canada">🇨🇦 Canada</option>
                <option value="Australia">🇦🇺 Australia</option>
                <option value="New Zealand">🇳🇿 New Zealand</option>
                <option value="Japan">🇯🇵 Japan</option>
                <option value="China">🇨🇳 China</option>
                <option value="South Korea">🇰🇷 South Korea</option>
                <option value="India">🇮🇳 India</option>
                <option value="Singapore">🇸🇬 Singapore</option>
                <option value="Malaysia">🇲🇾 Malaysia</option>
                <option value="Thailand">🇹🇭 Thailand</option>
                <option value="Vietnam">🇻🇳 Vietnam</option>
                <option value="Indonesia">🇮🇩 Indonesia</option>
                <option value="Philippines">🇵🇭 Philippines</option>
                <option value="Turkey">🇹🇷 Turkey</option>
                <option value="United Arab Emirates">🇦🇪 United Arab Emirates</option>
                <option value="Saudi Arabia">🇸🇦 Saudi Arabia</option>
                <option value="Israel">🇮🇱 Israel</option>
                <option value="South Africa">🇿🇦 South Africa</option>
                <option value="Egypt">🇪🇬 Egypt</option>
                <option value="Brazil">🇧🇷 Brazil</option>
                <option value="Mexico">🇲🇽 Mexico</option>
                <option value="Argentina">🇦🇷 Argentina</option>
                <option value="Chile">🇨🇱 Chile</option>
                <option value="Colombia">🇨🇴 Colombia</option>
                <option value="Russia">🇷🇺 Russia</option>
                <option value="Ukraine">🇺🇦 Ukraine</option>
              </select>
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
