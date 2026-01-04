/**
 * Admin Deletion Requests Page
 * Manage customer account deletion requests (GDPR compliance)
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { Trash2, AlertTriangle, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react';
import {
  listDeletionRequests,
  reviewDeletionRequest,
  processDeletion,
  type DeletionRequestListItem,
  type DeletionRequestFilters
} from '../../services/admin';
import { buildDisplayName } from '../../services/auth';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Label } from '../../components/ui/Label';
import { Badge } from '../../components/ui/Badge';

export function DeletionRequests() {
  const navigate = useNavigate();
  const [requests, setRequests] = useState<DeletionRequestListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<DeletionRequestFilters>({
    skip: 0,
    limit: 50,
    sort_by: 'requested_at',
    sort_order: 'desc',
  });

  // Form states for review modal
  const [selectedRequest, setSelectedRequest] = useState<DeletionRequestListItem | null>(null);
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject' | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load deletion requests
  const loadRequests = async (newFilters?: DeletionRequestFilters) => {
    setIsLoading(true);
    setError(null);
    try {
      const filterToUse = newFilters || filters;
      const response = await listDeletionRequests(filterToUse);
      setRequests(response.requests);
      setTotal(response.total);
    } catch (error: any) {
      console.error('Failed to load deletion requests:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to load deletion requests';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Check authentication
    const userEmail = localStorage.getItem('user_email');
    if (!userEmail) {
      navigate('/auth');
      return;
    }

    loadRequests();
  }, [navigate]);

  const handleFiltersChange = (newFilters: Partial<DeletionRequestFilters>) => {
    const updatedFilters = {
      ...filters,
      ...newFilters,
      skip: 0, // Reset to first page
    };
    setFilters(updatedFilters);
    loadRequests(updatedFilters);
  };

  const handleReview = (request: DeletionRequestListItem, action: 'approve' | 'reject') => {
    setSelectedRequest(request);
    setReviewAction(action);
    setReviewNotes('');
  };

  const submitReview = async () => {
    if (!selectedRequest || !reviewAction) return;

    if (reviewAction === 'reject' && !reviewNotes.trim()) {
      toast.error('Rejection reason is required');
      return;
    }

    setIsSubmitting(true);
    try {
      await reviewDeletionRequest(
        selectedRequest.id,
        reviewAction,
        reviewNotes.trim() || undefined
      );

      toast.success(
        reviewAction === 'approve'
          ? 'Deletion request approved successfully'
          : 'Deletion request rejected successfully'
      );

      // Close modal and reload
      setSelectedRequest(null);
      setReviewAction(null);
      setReviewNotes('');
      loadRequests();
    } catch (error: any) {
      console.error('Review failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to review deletion request');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleProcessDeletion = async (request: DeletionRequestListItem) => {
    if (request.status !== 'approved') {
      toast.error('Only approved requests can be processed');
      return;
    }

    const customerName = request.customer
      ? buildDisplayName(request.customer.first_name, request.customer.last_name, request.email)
      : request.email;

    // Confirmation dialog
    if (!confirm(
      `⚠️ WARNING: This will permanently delete all data for ${customerName} (${request.email}).\n\n` +
      `This action is IRREVERSIBLE and will:\n` +
      `• Delete all uploaded files from storage\n` +
      `• Anonymize all claims (retained for legal compliance)\n` +
      `• Permanently anonymize the customer profile\n\n` +
      `Are you absolutely sure you want to continue?`
    )) {
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await processDeletion(request.id);
      toast.success(response.message);

      // Show summary
      const summary = response.summary;
      if (summary.errors && summary.errors.length > 0) {
        toast.warning(`Completed with ${summary.errors.length} error(s). Check admin email for details.`);
      }

      loadRequests();
    } catch (error: any) {
      console.error('Deletion processing failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to process deletion');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return (
          <Badge variant="default" className="bg-yellow-500 hover:bg-yellow-600">
            <Clock className="w-3 h-3 mr-1" />
            Pending
          </Badge>
        );
      case 'approved':
        return (
          <Badge variant="default" className="bg-green-600 hover:bg-green-700">
            <CheckCircle className="w-3 h-3 mr-1" />
            Approved
          </Badge>
        );
      case 'rejected':
        return (
          <Badge variant="destructive">
            <XCircle className="w-3 h-3 mr-1" />
            Rejected
          </Badge>
        );
      case 'completed':
        return (
          <Badge variant="secondary">
            <CheckCircle className="w-3 h-3 mr-1" />
            Completed
          </Badge>
        );
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Trash2 className="w-8 h-8" />
            Account Deletion Requests
          </h1>
          <p className="text-muted-foreground mt-1">
            Review and process GDPR deletion requests
          </p>
        </div>
        <Button variant="outline" onClick={() => loadRequests()} disabled={isLoading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="search">Search</Label>
            <Input
              id="search"
              placeholder="Search by email or name..."
              onChange={(e) => handleFiltersChange({ search: e.target.value || undefined })}
            />
          </div>
          <div>
            <Label htmlFor="status">Status</Label>
            <select
              id="status"
              className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              onChange={(e) => handleFiltersChange({ status: e.target.value || undefined })}
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div className="flex items-end">
            <div className="text-sm text-muted-foreground">
              Total: <strong>{total}</strong> request{total !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </Card>

      {/* Requests Table */}
      {isLoading ? (
        <Card className="p-8 text-center">
          <RefreshCw className="w-12 h-12 mx-auto text-muted-foreground mb-4 animate-spin" />
          <p className="text-muted-foreground">Loading deletion requests...</p>
        </Card>
      ) : error ? (
        <Card className="p-8 text-center">
          <AlertTriangle className="w-12 h-12 mx-auto text-destructive mb-4" />
          <p className="text-destructive font-medium">{error}</p>
          <Button variant="outline" onClick={() => loadRequests()} className="mt-4">
            Try Again
          </Button>
        </Card>
      ) : requests.length === 0 ? (
        <Card className="p-8 text-center">
          <Trash2 className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">No deletion requests found</p>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b">
                <tr className="text-left">
                  <th className="p-4 font-medium">Customer</th>
                  <th className="p-4 font-medium">Status</th>
                  <th className="p-4 font-medium">Claims</th>
                  <th className="p-4 font-medium">Requested</th>
                  <th className="p-4 font-medium">Reason</th>
                  <th className="p-4 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {requests.map((request) => (
                  <tr key={request.id} className="hover:bg-muted/50">
                    <td className="p-4">
                      <div>
                        <div className="font-medium">
                          {request.customer
                            ? buildDisplayName(request.customer.first_name, request.customer.last_name, request.email)
                            : 'Unknown'}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {request.email}
                        </div>
                        {request.customer && (
                          <div className="text-xs text-muted-foreground mt-1">
                            Member since {format(new Date(request.customer.created_at), 'MMM yyyy')}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      {getStatusBadge(request.status)}
                    </td>
                    <td className="p-4">
                      <div className="text-sm">
                        <div>{request.total_claims_count} total</div>
                        {request.open_claims_count > 0 && (
                          <div className="flex items-center gap-1 text-orange-600 font-medium">
                            <AlertTriangle className="w-3 h-3" />
                            {request.open_claims_count} open
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="p-4 text-sm">
                      {format(new Date(request.requested_at), 'MMM d, yyyy')}
                    </td>
                    <td className="p-4 text-sm max-w-xs">
                      <div className="truncate" title={request.reason || undefined}>
                        {request.reason || (
                          <span className="text-muted-foreground italic">No reason provided</span>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex gap-2">
                        {request.status === 'pending' && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleReview(request, 'approve')}
                              className="text-green-600 border-green-600 hover:bg-green-50"
                            >
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleReview(request, 'reject')}
                              className="text-red-600 border-red-600 hover:bg-red-50"
                            >
                              <XCircle className="w-4 h-4 mr-1" />
                              Reject
                            </Button>
                          </>
                        )}
                        {request.status === 'approved' && (
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleProcessDeletion(request)}
                            disabled={isSubmitting}
                          >
                            <Trash2 className="w-4 h-4 mr-1" />
                            Process Deletion
                          </Button>
                        )}
                        {request.status === 'completed' && (
                          <Badge variant="secondary">Processed</Badge>
                        )}
                        {request.status === 'rejected' && (
                          <Badge variant="outline">Closed</Badge>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Review Modal */}
      {selectedRequest && reviewAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-lg w-full mx-4 p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              {reviewAction === 'approve' ? (
                <CheckCircle className="w-6 h-6 text-green-600" />
              ) : (
                <XCircle className="w-6 h-6 text-red-600" />
              )}
              {reviewAction === 'approve' ? 'Approve' : 'Reject'} Deletion Request
            </h2>

            <div className="space-y-4 mb-6">
              <div>
                <p className="text-sm text-muted-foreground">Customer:</p>
                <p className="font-medium">
                  {selectedRequest.customer
                    ? buildDisplayName(selectedRequest.customer.first_name, selectedRequest.customer.last_name, selectedRequest.email)
                    : 'Unknown'}
                </p>
                <p className="text-sm">{selectedRequest.email}</p>
              </div>

              {selectedRequest.open_claims_count > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded p-3 flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 text-orange-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-orange-900">
                    This customer has <strong>{selectedRequest.open_claims_count}</strong> open claim
                    {selectedRequest.open_claims_count !== 1 ? 's' : ''}.{' '}
                    {reviewAction === 'approve' &&
                      'Consider resolving these before approving deletion.'}
                  </span>
                </div>
              )}

              {selectedRequest.reason && (
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Customer's reason:</p>
                  <p className="text-sm bg-muted p-2 rounded">{selectedRequest.reason}</p>
                </div>
              )}

              <div>
                <Label htmlFor="review-notes">
                  {reviewAction === 'approve' ? 'Notes (optional)' : 'Rejection Reason (required)'}
                </Label>
                <textarea
                  id="review-notes"
                  className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder={
                    reviewAction === 'approve'
                      ? 'Add any notes for the customer...'
                      : 'Explain why the deletion request is being rejected...'
                  }
                />
              </div>
            </div>

            <div className="flex gap-3 justify-end">
              <Button
                variant="outline"
                onClick={() => {
                  setSelectedRequest(null);
                  setReviewAction(null);
                  setReviewNotes('');
                }}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                variant={reviewAction === 'approve' ? 'default' : 'destructive'}
                onClick={submitReview}
                disabled={isSubmitting || (reviewAction === 'reject' && !reviewNotes.trim())}
              >
                {isSubmitting ? 'Processing...' : reviewAction === 'approve' ? 'Approve' : 'Reject'}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
