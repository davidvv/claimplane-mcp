/**
 * Claim Status Tracker Page
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useSearchParams } from 'react-router-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Search,
  CheckCircle,
  FileText,
  Euro,
  Download,
} from 'lucide-react';
import { toast } from 'sonner';

import { claimStatusLookupSchema, type ClaimStatusLookupForm } from '@/schemas/validation';
import { getClaim } from '@/services/claims';
import { listClaimDocuments, downloadDocument } from '@/services/documents';
import type { Claim, Document } from '@/types/api';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import {
  formatCurrency,
  formatDateTime,
  getStatusLabel,
  getStatusColor,
  getIncidentLabel,
  getShortClaimId,
} from '@/lib/utils';

export function Status() {
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [claim, setClaim] = useState<Claim | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ClaimStatusLookupForm>({
    resolver: zodResolver(claimStatusLookupSchema),
  });

  // Auto-load claim if claimId is in URL (e.g., from magic link redirect)
  useEffect(() => {
    const claimIdFromUrl = searchParams.get('claimId');
    if (claimIdFromUrl) {
      setValue('claimId', claimIdFromUrl);
      // Automatically submit the form to load the claim
      onSubmit({ claimId: claimIdFromUrl });
    }
  }, [searchParams]);

  const onSubmit = async (data: ClaimStatusLookupForm) => {
    setIsLoading(true);

    try {
      const claimData = await getClaim(data.claimId);
      setClaim(claimData);

      // Fetch documents
      if (claimData.id) {
        const docs = await listClaimDocuments(claimData.id);
        setDocuments(docs);
      }

      toast.success('Claim found!');
    } catch (error: any) {
      toast.error('Claim not found. Please check your Claim ID.');
      console.error('Claim lookup error:', error);
      setClaim(null);
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadDocument = async (doc: Document) => {
    if (!doc.id) return;

    try {
      const blob = await downloadDocument(doc.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Document downloaded!');
    } catch (error) {
      toast.error('Failed to download document');
      console.error('Document download error:', error);
    }
  };

  // Status timeline steps
  const statusSteps = [
    { key: 'submitted', label: 'Submitted', icon: FileText },
    { key: 'under_review', label: 'Under Review', icon: Search },
    { key: 'approved', label: 'Approved', icon: CheckCircle },
    { key: 'paid', label: 'Paid', icon: Euro },
  ];

  const getCurrentStepIndex = () => {
    if (!claim) return -1;
    return statusSteps.findIndex((step) => step.key === claim.status);
  };

  const currentStepIndex = getCurrentStepIndex();

  return (
    <div className="py-12 md:py-20">
      <div className="container max-w-4xl">
        <div className="mb-12 text-center">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            Check Claim Status
          </h1>
          <p className="text-muted-foreground">
            Enter your Claim ID to view the status of your compensation claim
          </p>
        </div>

        {/* Claim ID Lookup */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Lookup Claim</CardTitle>
            <CardDescription>
              Your Claim ID was sent to your email when you submitted your claim. It looks like: 123e4567-e89b-12d3-a456-426614174000
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="claimId">Claim ID</Label>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <Input
                      id="claimId"
                      placeholder="Paste your Claim ID here (e.g., 123e4567-e89b-12d3-a456-426614174000)"
                      {...register('claimId')}
                    />
                    {errors.claimId && (
                      <p className="text-sm text-destructive mt-1">
                        {errors.claimId.message}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      The Claim ID is a long alphanumeric string (UUID format) sent to your email after submitting your claim
                    </p>
                  </div>
                  <Button type="submit" disabled={isLoading}>
                    {isLoading ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <>
                        <Search className="w-4 h-4 mr-2" />
                        Search
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Claim Details */}
        {claim && (
          <div className="space-y-6 fade-in">
            {/* Status Timeline */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Claim Status</CardTitle>
                  <Badge className={getStatusColor(claim.status || 'draft')}>
                    {getStatusLabel(claim.status || 'draft')}
                  </Badge>
                </div>
                <CardDescription>
                  Claim ID: {getShortClaimId(claim.id || '')}
                </CardDescription>
              </CardHeader>

              <CardContent>
                {/* Timeline */}
                <div className="relative">
                  <div className="flex items-center justify-between">
                    {statusSteps.map((step, index) => {
                      const isCompleted = index <= currentStepIndex;
                      const isCurrent = index === currentStepIndex;
                      const Icon = step.icon;

                      return (
                        <div
                          key={step.key}
                          className="flex flex-col items-center relative z-10"
                        >
                          {/* Connector line */}
                          {index !== statusSteps.length - 1 && (
                            <div
                              className={`absolute top-5 left-1/2 h-0.5 w-full transition-colors ${
                                isCompleted ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'
                              }`}
                              style={{ zIndex: -1 }}
                            />
                          )}

                          {/* Step icon */}
                          <div
                            className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 transition-all ${
                              isCompleted
                                ? 'bg-primary text-white'
                                : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                            }`}
                          >
                            <Icon className="w-5 h-5" />
                          </div>

                          {/* Step label */}
                          <p
                            className={`text-xs md:text-sm font-medium ${
                              isCurrent
                                ? 'text-foreground'
                                : 'text-muted-foreground'
                            }`}
                          >
                            {step.label}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Timestamps */}
                {claim.submittedAt && (
                  <div className="mt-6 pt-6 border-t text-sm text-muted-foreground">
                    <p>Submitted: {formatDateTime(claim.submittedAt)}</p>
                    {claim.updatedAt && (
                      <p>Last Updated: {formatDateTime(claim.updatedAt)}</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Compensation */}
            {claim.compensationAmount && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Euro className="w-5 h-5" />
                    Compensation Details
                  </CardTitle>
                </CardHeader>

                <CardContent>
                  <div className="bg-primary/10 rounded-lg p-6 text-center">
                    <p className="text-sm text-muted-foreground mb-1">
                      Eligible Amount
                    </p>
                    <p className="text-4xl font-bold text-primary">
                      {formatCurrency(claim.compensationAmount, claim.currency)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Flight Info */}
            <Card>
              <CardHeader>
                <CardTitle>Flight Information</CardTitle>
              </CardHeader>

              <CardContent className="space-y-3">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Flight Number</p>
                    <p className="font-semibold">
                      {claim.flightInfo.flightNumber}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Airline</p>
                    <p className="font-semibold">{claim.flightInfo.airline}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Route</p>
                    <p className="font-semibold">
                      {claim.flightInfo.departureAirport} →{' '}
                      {claim.flightInfo.arrivalAirport}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Incident Type</p>
                    <p className="font-semibold">
                      {getIncidentLabel(claim.incidentType)}
                    </p>
                  </div>
                </div>

                {claim.notes && (
                  <div className="pt-3 border-t">
                    <p className="text-sm text-muted-foreground">Notes</p>
                    <p className="text-sm">{claim.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Documents */}
            {documents.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Uploaded Documents</CardTitle>
                </CardHeader>

                <CardContent>
                  <ul className="space-y-2">
                    {documents.map((doc) => (
                      <li
                        key={doc.id}
                        className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-muted-foreground" />
                          <div>
                            <p className="font-medium text-sm">{doc.filename}</p>
                            <p className="text-xs text-muted-foreground">
                              {doc.documentType.replace('_', ' ')} •{' '}
                              {doc.uploadedAt &&
                                formatDateTime(doc.uploadedAt)}
                            </p>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadDocument(doc)}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
