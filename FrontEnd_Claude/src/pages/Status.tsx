/**
 * Claim status lookup and display page
 */
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import {
  Search,
  Plane,
  Calendar,
  DollarSign,
  FileText,
  Download,
  CheckCircle,
} from 'lucide-react';
import { ClaimStatusLookupSchema, type ClaimStatusFormData } from '@/schemas/validation';
import { claimService } from '@/services/claims';
import { documentService } from '@/services/documents';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Loading';
import {
  formatCurrency,
  formatDate,
  getStatusColor,
  formatStatusLabel,
} from '@/lib/utils';
import type { Claim } from '@/types/openapi';

export function StatusPage() {
  const [claim, setClaim] = useState<Claim | null>(null);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ClaimStatusFormData>({
    resolver: zodResolver(ClaimStatusLookupSchema),
  });

  const onSubmit = async (data: ClaimStatusFormData) => {
    setLoading(true);
    setClaim(null);

    try {
      const claimData = await claimService.getClaim(data.claimId);
      setClaim(claimData);
      toast.success('Claim found!');
    } catch (error) {
      console.error('Claim lookup error:', error);
      toast.error('Claim not found. Please check your Claim ID.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadDocument = async (documentId: string, filename: string) => {
    try {
      const blob = await documentService.downloadDocument(documentId);
      documentService.triggerDownload(blob, filename);
      toast.success('Document downloaded!');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download document.');
    }
  };

  const getStatusStep = (status: string): number => {
    const steps = ['submitted', 'under_review', 'approved', 'paid'];
    return steps.indexOf(status);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 dark:bg-gray-900">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Check Claim Status
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Enter your Claim ID to view the status of your compensation claim
          </p>
        </div>

        {/* Search Form */}
        <Card className="mx-auto mb-8 max-w-2xl">
          <CardHeader>
            <CardTitle>Enter Claim ID</CardTitle>
            <CardDescription>
              Your Claim ID was sent to your email after submission
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              placeholder="e.g., 123e4567-e89b-12d3-a456-426614174000"
              error={errors.claimId?.message}
              helperText="UUID format"
              {...register('claimId')}
            />

            <Button
              type="submit"
              fullWidth
              loading={loading}
              disabled={loading}
            >
              <Search className="mr-2 h-4 w-4" />
              Search Claim
            </Button>
          </form>
        </Card>

        {/* Loading State */}
        {loading && (
          <Card className="mx-auto max-w-4xl">
            <div className="flex flex-col items-center justify-center py-12">
              <Spinner />
              <p className="mt-4 text-gray-600 dark:text-gray-400">
                Looking up your claim...
              </p>
            </div>
          </Card>
        )}

        {/* Claim Details */}
        {claim && !loading && (
          <div className="mx-auto max-w-4xl space-y-6 animate-fade-in">
            {/* Status Overview */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Claim #{claim.id.slice(0, 8)}...</CardTitle>
                    <CardDescription>
                      Submitted on {formatDate(claim.submittedAt, 'long')}
                    </CardDescription>
                  </div>
                  <Badge className={getStatusColor(claim.status)}>
                    {formatStatusLabel(claim.status)}
                  </Badge>
                </div>
              </CardHeader>

              {/* Status Timeline */}
              <div className="mt-6">
                <div className="flex items-center justify-between">
                  {['submitted', 'under_review', 'approved', 'paid'].map((step, index) => {
                    const currentStepIndex = getStatusStep(claim.status);
                    const isCompleted = index <= currentStepIndex;
                    const isCurrent = index === currentStepIndex;

                    return (
                      <div key={step} className="flex flex-1 flex-col items-center">
                        {index > 0 && (
                          <div
                            className={`-ml-full h-1 w-full ${
                              isCompleted ? 'bg-green-500' : 'bg-gray-300'
                            }`}
                          />
                        )}
                        <div
                          className={`mt-2 flex h-10 w-10 items-center justify-center rounded-full ${
                            isCompleted
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-300 text-gray-600'
                          }`}
                        >
                          {isCompleted ? (
                            <CheckCircle className="h-5 w-5" />
                          ) : (
                            <span className="text-sm">{index + 1}</span>
                          )}
                        </div>
                        <p
                          className={`mt-2 text-xs font-medium ${
                            isCurrent ? 'text-primary-600' : 'text-gray-600'
                          }`}
                        >
                          {formatStatusLabel(step)}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </Card>

            {/* Compensation Details */}
            <Card>
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <DollarSign className="h-5 w-5 text-gray-500" />
                  <CardTitle>Compensation Details</CardTitle>
                </div>
              </CardHeader>

              <div className="rounded-lg bg-primary-50 p-6 dark:bg-primary-900/20">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Estimated Compensation
                </p>
                <p className="text-3xl font-bold text-primary-700 dark:text-primary-400">
                  {formatCurrency(claim.compensationAmount, claim.currency)}
                </p>
              </div>
            </Card>

            {/* Flight Details */}
            <Card>
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <Plane className="h-5 w-5 text-gray-500" />
                  <CardTitle>Flight Information</CardTitle>
                </div>
              </CardHeader>

              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600 dark:text-gray-400">Flight:</dt>
                  <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {claim.flightInfo.airline} {claim.flightInfo.flightNumber}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600 dark:text-gray-400">Date:</dt>
                  <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {formatDate(claim.flightInfo.departureDate)}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600 dark:text-gray-400">Route:</dt>
                  <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {claim.flightInfo.departureAirport} →{' '}
                    {claim.flightInfo.arrivalAirport}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600 dark:text-gray-400">
                    Incident Type:
                  </dt>
                  <dd className="text-sm font-medium capitalize text-gray-900 dark:text-gray-100">
                    {claim.incidentType.replace('_', ' ')}
                  </dd>
                </div>
              </dl>
            </Card>

            {/* Documents */}
            {claim.documents && claim.documents.length > 0 && (
              <Card>
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <FileText className="h-5 w-5 text-gray-500" />
                    <CardTitle>Uploaded Documents</CardTitle>
                  </div>
                </CardHeader>

                <div className="space-y-2">
                  {claim.documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between rounded-lg border border-gray-200 p-4 dark:border-gray-700"
                    >
                      <div className="flex items-center space-x-3">
                        <FileText className="h-5 w-5 text-gray-400" />
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100">
                            {doc.filename}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {formatStatusLabel(doc.documentType)} •{' '}
                            {(doc.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDownloadDocument(doc.id, doc.filename)}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download
                      </Button>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Notes */}
            {claim.notes && (
              <Card>
                <CardHeader>
                  <CardTitle>Additional Notes</CardTitle>
                </CardHeader>
                <p className="text-sm text-gray-700 dark:text-gray-300">{claim.notes}</p>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
