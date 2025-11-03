/**
 * Step 4: Review and Submit
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { CheckCircle, User, Plane, MapPin, FileText } from 'lucide-react';
import { claimService } from '@/services/claims';
import { documentService } from '@/services/documents';
import { useClaimStore } from '@/store/claimStore';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { FileUpload } from '@/components/ui/FileUpload';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { DocumentType } from '@/types/openapi';

export function Step4Review() {
  const navigate = useNavigate();
  const { formData, previousStep, updateFormData, resetForm, setLoading, loading } =
    useClaimStore();
  const [submitting, setSubmitting] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState<string[]>([]);

  const handleDocumentUpload = async (file: File, documentType: DocumentType) => {
    if (!formData.claimId) {
      toast.error('Please submit your claim first');
      return;
    }

    try {
      await documentService.uploadDocument(formData.claimId, file, documentType);
      setUploadedDocs((prev) => [...prev, file.name]);
      toast.success('Document uploaded successfully!');
    } catch (error) {
      console.error('Document upload error:', error);
      throw error;
    }
  };

  const handleSubmit = async () => {
    if (
      !formData.flightStatus ||
      !formData.eligibility ||
      !formData.email ||
      !formData.firstName ||
      !formData.lastName ||
      !formData.address ||
      !formData.incidentType
    ) {
      toast.error('Please complete all required fields');
      return;
    }

    setSubmitting(true);
    setLoading(true);

    try {
      const claim = await claimService.createClaim({
        customerInfo: {
          email: formData.email,
          firstName: formData.firstName,
          lastName: formData.lastName,
          phone: formData.phone || null,
          address: formData.address,
        },
        flightInfo: formData.flightStatus,
        incidentType: formData.incidentType,
        notes: formData.notes || null,
      });

      updateFormData({ claimId: claim.id });
      toast.success('Claim submitted successfully!');

      // Redirect to success page
      setTimeout(() => {
        navigate(`/success?claimId=${claim.id}`);
        resetForm();
      }, 1500);
    } catch (error) {
      console.error('Claim submission error:', error);
      toast.error('Failed to submit claim. Please try again.');
    } finally {
      setSubmitting(false);
      setLoading(false);
    }
  };

  if (!formData.flightStatus || !formData.eligibility) {
    return (
      <Card className="mx-auto max-w-2xl p-8 text-center">
        <p className="text-gray-600 dark:text-gray-400">
          Missing flight or eligibility information. Please start over.
        </p>
        <Button className="mt-4" onClick={() => navigate('/claim')}>
          Start New Claim
        </Button>
      </Card>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Compensation Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Compensation Summary</CardTitle>
        </CardHeader>

        <div className="rounded-lg bg-primary-50 p-6 dark:bg-primary-900/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Estimated Compensation
              </p>
              <p className="text-3xl font-bold text-primary-700 dark:text-primary-400">
                {formatCurrency(
                  formData.eligibility.compensationAmount,
                  formData.eligibility.currency
                )}
              </p>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                Under {formData.eligibility.regulation} regulations
              </p>
            </div>
            <CheckCircle className="h-16 w-16 text-primary-600" />
          </div>
        </div>
      </Card>

      {/* Flight Details */}
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Plane className="h-5 w-5 text-gray-500" />
            <CardTitle>Flight Details</CardTitle>
          </div>
        </CardHeader>

        <dl className="space-y-3">
          <div className="flex justify-between">
            <dt className="text-sm text-gray-600 dark:text-gray-400">Flight Number:</dt>
            <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formData.flightStatus.airline} {formData.flightStatus.flightNumber}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-sm text-gray-600 dark:text-gray-400">Date:</dt>
            <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formatDate(formData.flightStatus.departureDate)}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-sm text-gray-600 dark:text-gray-400">Route:</dt>
            <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formData.flightStatus.departureAirport} →{' '}
              {formData.flightStatus.arrivalAirport}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-sm text-gray-600 dark:text-gray-400">Incident Type:</dt>
            <dd className="text-sm font-medium capitalize text-gray-900 dark:text-gray-100">
              {formData.incidentType?.replace('_', ' ')}
            </dd>
          </div>
        </dl>
      </Card>

      {/* Passenger Details */}
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <User className="h-5 w-5 text-gray-500" />
            <CardTitle>Passenger Information</CardTitle>
          </div>
        </CardHeader>

        <dl className="space-y-3">
          <div className="flex justify-between">
            <dt className="text-sm text-gray-600 dark:text-gray-400">Name:</dt>
            <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formData.firstName} {formData.lastName}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-sm text-gray-600 dark:text-gray-400">Email:</dt>
            <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formData.email}
            </dd>
          </div>
          {formData.phone && (
            <div className="flex justify-between">
              <dt className="text-sm text-gray-600 dark:text-gray-400">Phone:</dt>
              <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {formData.phone}
              </dd>
            </div>
          )}
          <div className="flex justify-between">
            <dt className="text-sm text-gray-600 dark:text-gray-400">Address:</dt>
            <dd className="text-right text-sm font-medium text-gray-900 dark:text-gray-100">
              {formData.address?.street}
              <br />
              {formData.address?.city}, {formData.address?.postalCode}
              <br />
              {formData.address?.country}
            </dd>
          </div>
        </dl>
      </Card>

      {/* Document Upload (Optional - shown after submission) */}
      {formData.claimId && (
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-gray-500" />
              <CardTitle>Upload Documents (Optional)</CardTitle>
            </div>
          </CardHeader>

          <div className="space-y-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Upload supporting documents such as boarding pass, ID, or receipts to strengthen
              your claim.
            </p>

            <FileUpload
              onFileSelect={(file) => console.log('Selected:', file.name)}
              onUpload={(file) => handleDocumentUpload(file, 'boarding_pass')}
            />

            {uploadedDocs.length > 0 && (
              <div className="rounded-lg bg-green-50 p-4 dark:bg-green-900/20">
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  Uploaded: {uploadedDocs.join(', ')}
                </p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Terms & Submit */}
      <Card>
        <div className="space-y-4">
          <div className="rounded-lg bg-gray-50 p-4 text-sm text-gray-700 dark:bg-gray-800 dark:text-gray-300">
            <p className="font-medium">Please note:</p>
            <ul className="ml-4 mt-2 list-disc space-y-1">
              <li>
                By submitting this claim, you agree to our Terms of Service and Privacy Policy
              </li>
              <li>You authorize us to represent you in pursuing this compensation</li>
              <li>
                We'll keep you updated via email throughout the claim process
              </li>
            </ul>
          </div>

          <div className="flex justify-between border-t border-gray-200 pt-6 dark:border-gray-700">
            <Button variant="outline" onClick={previousStep} disabled={submitting}>
              Back
            </Button>
            <Button
              onClick={handleSubmit}
              loading={submitting}
              disabled={submitting || loading}
            >
              {formData.claimId ? 'Claim Submitted' : 'Submit Claim'}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
