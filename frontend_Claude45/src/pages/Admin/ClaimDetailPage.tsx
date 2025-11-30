/**
 * Claim Detail Page - Admin view of individual claim
 * Shows full claim details, documents, notes, and status history
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { toast } from 'sonner';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/admin/StatusBadge';
import { Input } from '../../components/ui/Input';
import { Label } from '../../components/ui/Label';
import {
  getClaimDetail,
  updateClaimStatus,
  addClaimNote,
  getValidStatusTransitions,
  type ClaimDetail,
  type ValidStatusTransitions,
} from '../../services/admin';

// Helper function to safely format dates
const formatDate = (dateString: string | null, formatStr: string = 'PPpp'): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid date';
    return format(date, formatStr);
  } catch {
    return 'Invalid date';
  }
};

export function ClaimDetailPage() {
  const { claimId } = useParams<{ claimId: string }>();
  const navigate = useNavigate();
  const [claim, setClaim] = useState<ClaimDetail | null>(null);
  const [validTransitions, setValidTransitions] = useState<ValidStatusTransitions | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [isAddingNote, setIsAddingNote] = useState(false);

  // Status update form
  const [selectedStatus, setSelectedStatus] = useState('');
  const [changeReason, setChangeReason] = useState('');

  // Note form
  const [noteText, setNoteText] = useState('');
  const [isInternalNote, setIsInternalNote] = useState(true);

  useEffect(() => {
    if (!claimId) {
      navigate('/panel/dashboard');
      return;
    }

    loadClaimData();
  }, [claimId, navigate]);

  const loadClaimData = async () => {
    if (!claimId) return;

    setIsLoading(true);
    try {
      const [claimData, transitions] = await Promise.all([
        getClaimDetail(claimId),
        getValidStatusTransitions(claimId),
      ]);
      setClaim(claimData);
      setValidTransitions(transitions);
      setSelectedStatus(claimData.status);
    } catch (error: any) {
      console.error('Failed to load claim:', error);
      toast.error(error.response?.data?.detail || 'Failed to load claim details');
      navigate('/panel/dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimId || !selectedStatus) return;

    setIsUpdatingStatus(true);
    try {
      const updatedClaim = await updateClaimStatus(claimId, {
        new_status: selectedStatus,
        change_reason: changeReason || undefined,
      });
      setClaim(updatedClaim);
      setChangeReason('');
      toast.success('Claim status updated successfully');

      // Reload transitions for new status
      const newTransitions = await getValidStatusTransitions(claimId);
      setValidTransitions(newTransitions);
      setSelectedStatus(updatedClaim.status);
    } catch (error: any) {
      console.error('Failed to update status:', error);
      toast.error(error.response?.data?.detail || 'Failed to update claim status');
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimId || !noteText.trim()) return;

    setIsAddingNote(true);
    try {
      console.log('[ClaimDetail] Adding note:', { noteText, isInternal: isInternalNote });
      const newNote = await addClaimNote(claimId, {
        note_text: noteText,
        is_internal: isInternalNote,
      });
      console.log('[ClaimDetail] Note created:', newNote);
      toast.success('Note added successfully');
      setNoteText('');
      // Reload claim to get updated notes
      console.log('[ClaimDetail] Reloading claim data...');
      await loadClaimData();
      console.log('[ClaimDetail] Claim reloaded, notes count:', claim?.claim_notes?.length);
    } catch (error: any) {
      console.error('Failed to add note:', error);
      toast.error(error.response?.data?.detail || 'Failed to add note');
    } finally {
      setIsAddingNote(false);
    }
  };

  if (isLoading || !claim) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">Loading claim details...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={() => navigate('/panel/dashboard')}>
            ← Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Claim #{claim.id.slice(0, 8)}</h1>
            <p className="text-muted-foreground mt-1">
              {claim.customer.first_name} {claim.customer.last_name} · {claim.customer.email}
            </p>
          </div>
        </div>
        <StatusBadge status={claim.status} className="text-lg px-4 py-2" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column - Main details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Flight Information */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Flight Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-muted-foreground">Flight Number</Label>
                <p className="font-medium">{claim.flight_number}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Airline</Label>
                <p className="font-medium">{claim.airline}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Route</Label>
                <p className="font-medium">
                  {claim.departure_airport} → {claim.arrival_airport}
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Incident Type</Label>
                <p className="font-medium capitalize">
                  {claim.incident_type.replace(/_/g, ' ')}
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Scheduled Departure</Label>
                <p className="font-medium">
                  {formatDate(claim.scheduled_departure)}
                </p>
              </div>
              {claim.actual_departure && (
                <div>
                  <Label className="text-muted-foreground">Actual Departure</Label>
                  <p className="font-medium">
                    {formatDate(claim.actual_departure)}
                  </p>
                </div>
              )}
              {claim.delay_hours !== null && (
                <div>
                  <Label className="text-muted-foreground">Delay Duration</Label>
                  <p className="font-medium">{claim.delay_hours} hours</p>
                </div>
              )}
              <div>
                <Label className="text-muted-foreground">Compensation</Label>
                <p className="font-medium text-lg">
                  {claim.calculated_compensation
                    ? `€${parseFloat(claim.calculated_compensation).toFixed(0)}`
                    : 'Not calculated'}
                </p>
              </div>
            </div>
            {claim.incident_description && (
              <div className="mt-4">
                <Label className="text-muted-foreground">Description</Label>
                <p className="mt-1">{claim.incident_description}</p>
              </div>
            )}
          </Card>

          {/* Customer Information */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Customer Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-muted-foreground">Name</Label>
                <p className="font-medium">
                  {claim.customer.first_name} {claim.customer.last_name}
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Email</Label>
                <p className="font-medium">{claim.customer.email}</p>
              </div>
              {claim.customer.phone && (
                <div>
                  <Label className="text-muted-foreground">Phone</Label>
                  <p className="font-medium">{claim.customer.phone}</p>
                </div>
              )}
              {claim.customer.street && (
                <div className="col-span-2">
                  <Label className="text-muted-foreground">Address</Label>
                  <p className="font-medium">
                    {claim.customer.street}
                    {claim.customer.city && `, ${claim.customer.city}`}
                    {claim.customer.postal_code && ` ${claim.customer.postal_code}`}
                    {claim.customer.country && `, ${claim.customer.country}`}
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Documents */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Documents ({claim.files?.length || 0})</h2>
            {!claim.files || claim.files.length === 0 ? (
              <p className="text-muted-foreground">No documents uploaded</p>
            ) : (
              <div className="space-y-2">
                {claim.files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex-1">
                      <p className="font-medium">{file.original_filename}</p>
                      <p className="text-sm text-muted-foreground">
                        {file.document_type.replace(/_/g, ' ')} ·{' '}
                        {(file.file_size / 1024).toFixed(1)} KB ·{' '}
                        {formatDate(file.uploaded_at, 'MMM d, yyyy')}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={file.status} />
                      <Button variant="outline" size="sm">
                        View
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Notes */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Notes ({claim.claim_notes?.length || 0})</h2>

            {/* Add Note Form */}
            <form onSubmit={handleAddNote} className="space-y-4 mb-6 pb-6 border-b">
              <div>
                <Label htmlFor="note">Add Note</Label>
                <textarea
                  id="note"
                  className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="Write a note..."
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  disabled={isAddingNote}
                />
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={isInternalNote}
                    onChange={(e) => setIsInternalNote(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">Internal note (not visible to customer)</span>
                </label>
                <Button type="submit" disabled={isAddingNote || !noteText.trim()}>
                  {isAddingNote ? 'Adding...' : 'Add Note'}
                </Button>
              </div>
            </form>

            {/* Notes List */}
            {!claim.claim_notes || claim.claim_notes.length === 0 ? (
              <p className="text-muted-foreground">No notes yet</p>
            ) : (
              <div className="space-y-3">
                {claim.claim_notes.map((note) => (
                  <div key={note.id} className="p-3 border rounded-lg">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        {note.author && (
                          <p className="font-medium">
                            {note.author.first_name} {note.author.last_name}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground">
                          {formatDate(note.created_at)}
                        </p>
                      </div>
                      {note.is_internal && (
                        <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                          Internal
                        </span>
                      )}
                    </div>
                    <p className="text-sm">{note.note_text}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right column - Status & History */}
        <div className="space-y-6">
          {/* Update Status */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Update Status</h2>
            <form onSubmit={handleStatusUpdate} className="space-y-4">
              <div>
                <Label htmlFor="status">New Status</Label>
                <select
                  id="status"
                  className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  disabled={isUpdatingStatus}
                >
                  <option value={claim.status}>{claim.status.replace(/_/g, ' ')}</option>
                  {validTransitions?.valid_next_statuses.map((status) => (
                    <option key={status} value={status}>
                      {status.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="reason">Reason (optional)</Label>
                <Input
                  id="reason"
                  placeholder="Reason for status change..."
                  value={changeReason}
                  onChange={(e) => setChangeReason(e.target.value)}
                  disabled={isUpdatingStatus}
                />
              </div>
              <Button
                type="submit"
                className="w-full"
                disabled={isUpdatingStatus || selectedStatus === claim.status}
              >
                {isUpdatingStatus ? 'Updating...' : 'Update Status'}
              </Button>
            </form>
          </Card>

          {/* Status History */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Status History</h2>
            {!claim.status_history || claim.status_history.length === 0 ? (
              <p className="text-muted-foreground text-sm">No status changes yet</p>
            ) : (
              <div className="space-y-3">
                {claim.status_history.map((history) => (
                  <div key={history.id} className="pb-3 border-b last:border-0">
                    <div className="flex items-center gap-2 mb-1">
                      <StatusBadge status={history.new_status} />
                    </div>
                    {history.changed_by_user && (
                      <p className="text-xs text-muted-foreground">
                        by {history.changed_by_user.first_name}{' '}
                        {history.changed_by_user.last_name}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {formatDate(history.changed_at)}
                    </p>
                    {history.change_reason && (
                      <p className="text-sm mt-1">{history.change_reason}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Quick Info */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Quick Info</h2>
            <div className="space-y-3 text-sm">
              <div>
                <Label className="text-muted-foreground">Claim ID</Label>
                <p className="font-mono text-xs">{claim.id}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Submitted</Label>
                <p>{formatDate(claim.submitted_at)}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Last Updated</Label>
                <p>{formatDate(claim.updated_at)}</p>
              </div>
              {claim.extraordinary_circumstances && (
                <div>
                  <Label className="text-muted-foreground">Extraordinary Circumstances</Label>
                  <p className="text-yellow-600 font-medium">Yes</p>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
