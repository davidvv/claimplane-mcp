/**
 * Claim Status Tracker Page
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Search,
  CheckCircle,
  FileText,
  Euro,
  Download,
  Upload,
  LogIn,
} from 'lucide-react';
import { toast } from 'sonner';

import { claimStatusLookupSchema, type ClaimStatusLookupForm } from '@/schemas/validation';
import { getClaim } from '@/services/claims';
import { listClaimDocuments, downloadDocument, uploadDocument } from '@/services/documents';
import { isAuthenticated } from '@/services/auth';
import type { Claim, Document, DocumentType } from '@/types/api';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { FileUploadZone } from '@/components/FileUploadZone';
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
  const navigate = useNavigate();
  const authenticated = isAuthenticated();
  const [isLoading, setIsLoading] = useState(false);
  const [claim, setClaim] = useState<Claim | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [hasAutoLoaded, setHasAutoLoaded] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [pendingUploads, setPendingUploads] = useState<Array<{file: File; documentType: DocumentType; status: string}>>([]);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ClaimStatusLookupForm>({
    resolver: zodResolver(claimStatusLookupSchema),
  });

  // Redirect authenticated users to My Claims page ONLY if they don't have a claimId
  // (Allow viewing specific claims when coming from My Claims page)
  useEffect(() => {
    const claimIdFromUrl = searchParams.get('claimId');
    if (authenticated && !claimIdFromUrl) {
      navigate('/my-claims');
    }
  }, [authenticated, navigate, searchParams]);

  // Debug: Track documents state changes
  useEffect(() => {
    console.log('[STATE] Documents state changed:', documents);
    console.log('[STATE] Documents count:', documents.length);
  }, [documents]);

  // Auto-load claim if claimId is in URL (e.g., from magic link redirect)
  useEffect(() => {
    const claimIdFromUrl = searchParams.get('claimId');
    if (claimIdFromUrl && !hasAutoLoaded) {
      setValue('claimId', claimIdFromUrl);

      // Comprehensive debugging for authentication state
      console.log('=== STATUS PAGE DEBUGGING ===');
      console.log('Claim ID from URL:', claimIdFromUrl);
      console.log('Current URL:', window.location.href);
      console.log('LocalStorage user_email:', localStorage.getItem('user_email'));
      console.log('LocalStorage user_id:', localStorage.getItem('user_id'));
      console.log('LocalStorage user_role:', localStorage.getItem('user_role'));

      // Check if user is authenticated (user info stored in localStorage after login)
      const userEmail = localStorage.getItem('user_email');
      if (userEmail) {
        console.log('User authenticated, proceeding with auto-load');
        setHasAutoLoaded(true);  // Mark as auto-loaded to prevent duplicate execution
        setIsLoading(true); // Show loading for auto-load
        
        // Add additional debugging for the API call
        const debugOnSubmit = async (claimId: string) => {
          console.log('Starting claim lookup for:', claimId);
          try {
            const claimData = await getClaim(claimId);
            console.log('Claim lookup successful:', claimData);
            setClaim(claimData);

            // Fetch documents (optional - don't fail if not available)
            if (claimData.id) {
              try {
                console.log('[AUTO-LOAD] Fetching documents for claim:', claimData.id);
                const docs = await listClaimDocuments(claimData.id);
                console.log('[AUTO-LOAD] Documents API response:', docs);
                console.log('[AUTO-LOAD] Number of documents:', docs?.length || 0);
                console.log('[AUTO-LOAD] Setting documents state with:', docs);
                setDocuments(docs);
                console.log('[AUTO-LOAD] Documents state updated');
              } catch (docError) {
                console.error('[AUTO-LOAD] Error fetching documents:', docError);
                setDocuments([]);
              }
            }

            toast.success('Claim found!');
          } catch (error: any) {
            console.error('Claim lookup failed:', error);
            console.error('Error response:', error.response);
            console.error('Error status:', error.response?.status);
            console.error('Error data:', error.response?.data);
            
            if (error.response?.status === 401) {
              toast.error('Authentication expired. Please log in again.');
              // Clear user info (tokens are in HTTP-only cookies, cleared by backend)
              localStorage.removeItem('user_email');
              localStorage.removeItem('user_id');
              localStorage.removeItem('user_name');
              localStorage.removeItem('user_role');
            } else if (error.response?.status === 403) {
              toast.error('Access denied. This claim may belong to another user.');
            } else if (error.response?.status === 404) {
              toast.error('Claim not found. Please check your Claim ID.');
            } else {
              toast.error('Error loading claim. Please try again.');
            }
            setClaim(null);
            setDocuments([]);
          } finally {
            setIsLoading(false);
          }
        };
        
        // Delay slightly to ensure auth state is ready
        setTimeout(() => {
          debugOnSubmit(claimIdFromUrl);
        }, 500); // Short delay to ensure localStorage is accessible
      } else {
        console.log('User not authenticated, manual submission required');
        // Don't show error toast for missing auth - let user manually enter claim ID
      }
    }
  }, [searchParams]);

  const onSubmit = async (data: ClaimStatusLookupForm) => {
    setIsLoading(true);

    try {
      const claimData = await getClaim(data.claimId);
      setClaim(claimData);

      // Fetch documents (optional - don't fail if not available)
      if (claimData.id) {
        try {
          console.log('[MANUAL LOAD] Fetching documents for claim:', claimData.id);
          const docs = await listClaimDocuments(claimData.id);
          console.log('[MANUAL LOAD] Documents API response:', docs);
          console.log('[MANUAL LOAD] Number of documents:', docs?.length || 0);
          console.log('[MANUAL LOAD] Setting documents state with:', docs);
          setDocuments(docs);
          console.log('[MANUAL LOAD] Documents state updated');
        } catch (docError) {
          console.error('[MANUAL LOAD] Error fetching documents:', docError);
          setDocuments([]);
        }
      }

      toast.success('Claim found!');
    } catch (error: any) {
      console.error('Claim lookup error:', error);
      
      if (error.response?.status === 401) {
        toast.error('Authentication expired. Please log in again.');
        // Clear user info (tokens are in HTTP-only cookies, cleared by backend)
        localStorage.removeItem('user_email');
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_name');
        localStorage.removeItem('user_role');
      } else if (error.response?.status === 403) {
        toast.error('Access denied. This claim may belong to another user.');
      } else if (error.response?.status === 404) {
        toast.error('Claim not found. Please check your Claim ID.');
      } else {
        toast.error('Error loading claim. Please try again.');
      }
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
      a.download = doc.originalFilename || doc.filename;
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

  const handleFilesChange = (files: Array<{file: File; documentType: DocumentType; status: string}>) => {
    setPendingUploads(files);
  };

  const handleUploadDocuments = async () => {
    if (pendingUploads.length === 0 || !claim?.id) return;

    setIsUploading(true);
    let successCount = 0;
    let failCount = 0;

    for (const pending of pendingUploads) {
      try {
        console.log('[UPLOAD] Uploading document:', pending.file.name);
        const uploadedDoc = await uploadDocument(claim.id, pending.file, pending.documentType);
        console.log('[UPLOAD] Upload successful:', uploadedDoc);
        console.log('[UPLOAD] Adding to documents state, current length:', documents.length);
        setDocuments(prev => {
          const updated = [uploadedDoc, ...prev];
          console.log('[UPLOAD] Documents state after update, length:', updated.length);
          return updated;
        });
        successCount++;
      } catch (error: any) {
        console.error('[UPLOAD] Upload error:', error);
        toast.error(`Failed to upload ${pending.file.name}`);
        failCount++;
      }
    }

    if (successCount > 0) {
      toast.success(`${successCount} document${successCount > 1 ? 's' : ''} uploaded successfully!`);
    }

    // Clear pending uploads
    setPendingUploads([]);
    setIsUploading(false);
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

  // If not authenticated, show login prompt instead of claim lookup
  if (!authenticated) {
    return (
      <div className="min-h-screen bg-background py-12">
        <div className="container mx-auto px-4 max-w-2xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold mb-2">
              Track Your Claim
            </h1>
            <p className="text-muted-foreground">
              Access your claim status and documents by logging into your account
            </p>
          </div>

          <Card>
            <CardContent className="py-12 text-center">
              <LogIn className="w-16 h-16 text-primary mx-auto mb-6" />
              <h2 className="text-2xl font-semibold mb-3">
                Login Required
              </h2>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                Please sign in using the email address you provided when your claim was created.
                We'll send you a secure magic link to access your claim details.
              </p>
              <Button
                size="lg"
                onClick={() => navigate('/auth')}
              >
                <LogIn className="w-5 h-5 mr-2" />
                Sign In to View Claims
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">
            Track Your Claim
          </h1>
          <p className="text-muted-foreground">
            Enter your Claim ID to check the status of your flight compensation claim.
          </p>
        </div>

        {/* Auto-loading indicator for magic link redirects */}
        {isLoading && searchParams.get('claimId') && (
          <div className="text-center mb-6">
            <div className="inline-flex items-center space-x-2 bg-primary/10 text-primary px-4 py-2 rounded-lg">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <span>Loading your claim...</span>
            </div>
          </div>
        )}

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
            <Card>
              <CardHeader>
                <CardTitle>Documents</CardTitle>
                <CardDescription>
                  Upload supporting documents for your claim (boarding passes, receipts, etc.)
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                {/* Upload Form */}
                <div className="space-y-4">
                  <FileUploadZone
                    onFilesChange={handleFilesChange}
                    maxFiles={5}
                    maxSizeMB={10}
                  />

                  {pendingUploads.length > 0 && (
                    <Button
                      onClick={handleUploadDocuments}
                      disabled={isUploading}
                      className="w-full"
                    >
                      {isUploading ? (
                        <>
                          <LoadingSpinner size="sm" className="mr-2" />
                          Uploading {pendingUploads.length} document{pendingUploads.length > 1 ? 's' : ''}...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4 mr-2" />
                          Upload {pendingUploads.length} Document{pendingUploads.length > 1 ? 's' : ''}
                        </>
                      )}
                    </Button>
                  )}
                </div>

                {/* Documents List */}
                {documents.length > 0 ? (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">Uploaded Documents ({documents.length})</h3>
                    <ul className="space-y-2">
                      {documents.map((doc) => (
                        <li
                          key={doc.id}
                          className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <FileText className="w-5 h-5 text-muted-foreground" />
                            <div>
                              <p className="font-medium text-sm">{doc.originalFilename || doc.filename}</p>
                              <p className="text-xs text-muted-foreground">
                                {doc.documentType.replace('_', ' ')} •{' '}
                                {doc.uploadedAt && formatDateTime(doc.uploadedAt)}
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
                  </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No documents uploaded yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
