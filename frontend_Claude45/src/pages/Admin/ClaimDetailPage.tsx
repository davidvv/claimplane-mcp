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
import { DocumentViewerModal } from '../../components/admin/DocumentViewerModal';
import { Input } from '../../components/ui/Input';
import { Label } from '../../components/ui/Label';
import {
  getClaimDetail,
  updateClaimStatus,
  addClaimNote,
  getValidStatusTransitions,
  assignClaim,
  getAdminUsers,
  reviewFile,
  type ClaimDetail,
  type ClaimFile,
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
  const [isAssigning, setIsAssigning] = useState(false);

  // Status update form
  const [selectedStatus, setSelectedStatus] = useState('');
  const [changeReason, setChangeReason] = useState('');

  // Note form
  const [noteText, setNoteText] = useState('');
  const [isInternalNote, setIsInternalNote] = useState(true);

  // Assignment form
  const [adminUsers, setAdminUsers] = useState<Array<{ id: string; email: string; first_name: string; last_name: string }>>([]);
  const [selectedAdmin, setSelectedAdmin] = useState<string>('');
  const [currentUserId, setCurrentUserId] = useState<string>('');

  // Document review
  const [reviewingFileId, setReviewingFileId] = useState<string | null>(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [isReviewingFile, setIsReviewingFile] = useState(false);

  // Document viewer
  const [viewingFile, setViewingFile] = useState<ClaimFile | null>(null);
  const [showViewerModal, setShowViewerModal] = useState(false);

  useEffect(() => {
    if (!claimId) {
      navigate('/panel/dashboard');
      return;
    }

    loadClaimData();
    loadAdminUsers();

    // Get current user ID from localStorage (set during login)
    const userId = sessionStorage.getItem('user_id');
    if (userId) {
      setCurrentUserId(userId);
    }
  }, [claimId, navigate]);

  const loadAdminUsers = async () => {
    try {
      const users = await getAdminUsers();
      setAdminUsers(users);
    } catch (error: any) {
      console.error('Failed to load admin users:', error);
      // Don't show error toast - not critical
    }
  };

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

    // Validate that rejection reason is provided for rejected status
    if (selectedStatus === 'rejected' && !changeReason?.trim()) {
      toast.error('Rejection reason is required when changing status to "rejected"');
      return;
    }

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
      // Error will be handled by API interceptor, so no need to show toast here
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

  const handleAssignToMe = async () => {
    if (!claimId || !currentUserId) return;

    setIsAssigning(true);
    try {
      const updatedClaim = await assignClaim(claimId, currentUserId);
      setClaim(updatedClaim);
      toast.success('Claim assigned to you');
    } catch (error: any) {
      console.error('Failed to assign claim:', error);
      toast.error(error.response?.data?.detail || 'Failed to assign claim');
    } finally {
      setIsAssigning(false);
    }
  };

  const handleAssignToAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimId || !selectedAdmin) return;

    setIsAssigning(true);
    try {
      const updatedClaim = await assignClaim(claimId, selectedAdmin);
      setClaim(updatedClaim);
      toast.success('Claim assigned successfully');
      setSelectedAdmin('');
    } catch (error: any) {
      console.error('Failed to assign claim:', error);
      toast.error(error.response?.data?.detail || 'Failed to assign claim');
    } finally {
      setIsAssigning(false);
    }
  };

  const handleApproveFile = async (fileId: string) => {
    setIsReviewingFile(true);
    try {
      await reviewFile(fileId, true);
      toast.success('Document approved successfully');
      // Reload claim data to get updated file status
      await loadClaimData();
    } catch (error: any) {
      console.error('Failed to approve document:', error);
      toast.error(error.response?.data?.detail || 'Failed to approve document');
    } finally {
      setIsReviewingFile(false);
    }
  };

  const handleRejectFile = (fileId: string) => {
    setReviewingFileId(fileId);
    setShowRejectModal(true);
  };

  const handleConfirmReject = async () => {
    if (!reviewingFileId || !rejectionReason.trim()) {
      toast.error('Please provide a rejection reason');
      return;
    }

    setIsReviewingFile(true);
    try {
      await reviewFile(reviewingFileId, false, rejectionReason);
      toast.success('Document rejected and customer notified');
      // Reload claim data to get updated file status
      await loadClaimData();
      setShowRejectModal(false);
      setRejectionReason('');
      setReviewingFileId(null);
    } catch (error: any) {
      console.error('Failed to reject document:', error);
      toast.error(error.response?.data?.detail || 'Failed to reject document');
    } finally {
      setIsReviewingFile(false);
    }
  };

  const handleCancelReject = () => {
    setShowRejectModal(false);
    setRejectionReason('');
    setReviewingFileId(null);
  };

  const handleViewFile = (file: ClaimFile) => {
    setViewingFile(file);
    setShowViewerModal(true);
  };

  const handleCloseViewer = () => {
    setShowViewerModal(false);
    setViewingFile(null);
  };

  if (isLoading || !claim) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">Loading claim details...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 md:py-8 space-y-6 px-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
        <Button variant="outline" size="sm" onClick={() => navigate('/panel/dashboard')}>
          ← Back
        </Button>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl sm:text-3xl font-bold truncate">
            Claim #{claim.id.slice(0, 8)}
          </h1>
          <p className="text-sm text-muted-foreground mt-1 truncate">
            {claim.customer.first_name} {claim.customer.last_name}
          </p>
        </div>
        <StatusBadge status={claim.status} className="text-sm px-3 py-1" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column - Main details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Flight Information */}
          <Card className="p-4 md:p-6">
            <h2 className="text-lg font-semibold mb-4">Flight Information</h2>
            <div className="grid grid-cols-1 xs:grid-cols-2 gap-3 md:gap-4">
              <div>
                <Label className="text-muted-foreground text-xs">Flight</Label>
                <p className="font-medium">{claim.flight_number}</p>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">Airline</Label>
                <p className="font-medium">{claim.airline}</p>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">Route</Label>
                <p className="font-medium">
                  {claim.departure_airport} → {claim.arrival_airport}
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">Incident</Label>
                <p className="font-medium capitalize">
                  {claim.incident_type.replace(/_/g, ' ')}
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">Date</Label>
                <p className="font-medium">
                  {formatDate(claim.departure_date, 'PPP')}
                </p>
              </div>
              {claim.delay_hours !== null && (
                <div>
                  <Label className="text-muted-foreground text-xs">Delay</Label>
                  <p className="font-medium">{claim.delay_hours}h</p>
                </div>
              )}
              <div className="col-span-2">
                <Label className="text-muted-foreground text-xs">Compensation</Label>
                <p className="font-medium text-lg">
                  {claim.calculated_compensation
                    ? `€${parseFloat(claim.calculated_compensation).toFixed(0)}`
                    : '—'}
                </p>
              </div>
            </div>
          </Card>

          {/* Customer Information */}
          <Card className="p-4 md:p-6">
            <h2 className="text-lg font-semibold mb-4">Customer</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
              <div>
                <Label className="text-muted-foreground text-xs">Name</Label>
                <p className="font-medium">
                  {claim.customer.first_name} {claim.customer.last_name}
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">Email</Label>
                <p className="font-medium truncate">{claim.customer.email}</p>
              </div>
              {claim.customer.phone && (
                <div>
                  <Label className="text-muted-foreground text-xs">Phone</Label>
                  <p className="font-medium">{claim.customer.phone}</p>
                </div>
              )}
              {claim.customer.street && (
                <div className="sm:col-span-2">
                  <Label className="text-muted-foreground text-xs">Address</Label>
                  <p className="font-medium text-sm">
                    {claim.customer.street}, {claim.customer.city} {claim.customer.postal_code}, {claim.customer.country}
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Customer Information */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Customer Information</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
          <Card className="p-4 md:p-6">
            <h2 className="text-lg font-semibold mb-4">Documents ({claim.files?.length || 0})</h2>
            {!claim.files || claim.files.length === 0 ? (
              <p className="text-muted-foreground text-sm">No documents</p>
            ) : (
              <div className="space-y-2">
                {claim.files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 border rounded-lg gap-2"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{file.original_filename || 'Unknown'}</p>
                      <p className="text-xs text-muted-foreground">
                        {file.document_type.replace(/_/g, ' ')} · {(file.file_size / 1024).toFixed(1)} KB
                      </p>
                      {file.rejection_reason && (
                        <p className="text-xs text-red-600 mt-1">
                          Rejected: {file.rejection_reason}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <StatusBadge status={file.status} />
                      {file.status === 'uploaded' && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-green-600 hover:text-green-700 hover:bg-green-50"
                            onClick={() => handleApproveFile(file.id)}
                            disabled={isReviewingFile}
                          >
                            Approve
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            onClick={() => handleRejectFile(file.id)}
                            disabled={isReviewingFile}
                          >
                            Reject
                          </Button>
                        </>
                      )}
                      <Button variant="outline" size="sm" onClick={() => handleViewFile(file)}>
                        View
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Notes */}
          <Card className="p-4 md:p-6">
            <h2 className="text-lg font-semibold mb-4">Notes ({claim.claim_notes?.length || 0})</h2>

            {/* Add Note Form */}
            <form onSubmit={handleAddNote} className="space-y-3 mb-4 pb-4 border-b">
              <div>
                <Label htmlFor="note" className="text-xs">Add Note</Label>
                <textarea
                  id="note"
                  className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="Write a note..."
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  disabled={isAddingNote}
                />
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={isInternalNote}
                    onChange={(e) => setIsInternalNote(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-xs">Internal</span>
                </label>
                <Button type="submit" size="sm" disabled={isAddingNote || !noteText.trim()}>
                  {isAddingNote ? '...' : 'Add'}
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

          {/* Airline Communication Data - Comprehensive View */}
          <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-blue-900">
                  📋 Complete Claim Data for Airline
                </h2>
                <p className="text-sm text-blue-700 mt-1">
                  All information needed for airline communication in one place
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.print()}
                className="hidden md:flex"
              >
                Print/Save
              </Button>
            </div>

            {/* Two-column layout for comprehensive data */}
            <div className="grid md:grid-cols-2 gap-6 bg-white p-6 rounded-lg shadow-sm">
              {/* Column 1: Flight & Passenger Details */}
              <div className="space-y-6">
                {/* Flight Details */}
                <div>
                  <h3 className="font-semibold text-lg mb-3 pb-2 border-b border-gray-200">
                    ✈️ Flight Details
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Flight Number:</span>
                      <span className="font-medium">{claim.flight_number}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Airline:</span>
                      <span className="font-medium">{claim.airline}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Route:</span>
                      <span className="font-medium">
                        {claim.departure_airport} → {claim.arrival_airport}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Departure Date:</span>
                      <span className="font-medium">
                        {formatDate(claim.departure_date, 'PPPP')}
                      </span>
                    </div>
                    {claim.flight_distance_km && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Flight Distance:</span>
                        <span className="font-medium">{claim.flight_distance_km} km</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Passenger Information */}
                <div>
                  <h3 className="font-semibold text-lg mb-3 pb-2 border-b border-gray-200">
                    👤 Passenger Information
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Name:</span>
                      <span className="font-medium">
                        {claim.customer.first_name} {claim.customer.last_name}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Email:</span>
                      <span className="font-medium">{claim.customer.email}</span>
                    </div>
                    {claim.customer.phone && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Phone:</span>
                        <span className="font-medium">{claim.customer.phone}</span>
                      </div>
                    )}
                    {claim.customer.street && (
                      <div className="pt-2">
                        <span className="text-muted-foreground block mb-1">Address:</span>
                        <div className="font-medium text-sm leading-relaxed">
                          {claim.customer.street}<br />
                          {claim.customer.postal_code} {claim.customer.city}<br />
                          {claim.customer.country}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Column 2: Incident & Compensation Details */}
              <div className="space-y-6">
                {/* Incident Details */}
                <div>
                  <h3 className="font-semibold text-lg mb-3 pb-2 border-b border-gray-200">
                    ⚠️ Incident Details
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Incident Type:</span>
                      <span className="font-medium capitalize">
                        {claim.incident_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    {claim.delay_hours !== null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Delay Duration:</span>
                        <span className="font-medium">{claim.delay_hours} hours</span>
                      </div>
                    )}
                    {claim.extraordinary_circumstances && (
                      <div className="pt-2">
                        <span className="text-muted-foreground block mb-1">
                          Extraordinary Circumstances:
                        </span>
                        <div className="bg-yellow-50 border border-yellow-200 rounded p-2 text-yellow-800 text-xs">
                          {claim.extraordinary_circumstances}
                        </div>
                      </div>
                    )}
                    {claim.incident_description && (
                      <div className="pt-2">
                        <span className="text-muted-foreground block mb-1">Description:</span>
                        <div className="font-medium text-sm bg-gray-50 p-2 rounded">
                          {claim.incident_description}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Compensation Details */}
                <div>
                  <h3 className="font-semibold text-lg mb-3 pb-2 border-b border-gray-200">
                    💰 Compensation Details
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Calculated Amount:</span>
                      <span className="font-bold text-2xl text-green-600">
                        {claim.calculated_compensation
                          ? `€${parseFloat(claim.calculated_compensation).toFixed(0)}`
                          : 'Not calculated'}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground pt-2">
                      <span>Submitted:</span>
                      <span>{formatDate(claim.submitted_at, 'PPP')}</span>
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Claim ID:</span>
                      <span className="font-mono">{claim.id.slice(0, 13)}...</span>
                    </div>
                  </div>
                </div>

                {/* Documents Summary */}
                <div>
                  <h3 className="font-semibold text-lg mb-3 pb-2 border-b border-gray-200">
                    📎 Attached Documents
                  </h3>
                  <div className="text-sm space-y-1">
                    {claim.files && claim.files.length > 0 ? (
                      <ul className="space-y-1">
                        {claim.files.map((file) => (
                          <li key={file.id} className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground truncate">
                              {file.document_type.replace(/_/g, ' ')}
                            </span>
                            <span className="font-medium ml-2">
                              {file.original_filename && file.original_filename.length > 20
                                ? `${file.original_filename.substring(0, 20)}...`
                                : file.original_filename || 'Unknown'}
                            </span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-muted-foreground text-xs italic">No documents uploaded</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Copy Section */}
            <div className="mt-4 p-4 bg-white rounded-lg border border-blue-200">
              <p className="text-xs text-blue-700 mb-2 font-semibold">
                📧 Quick Reference for Airline Communication:
              </p>
              <div className="text-xs font-mono bg-gray-50 p-3 rounded border border-gray-200 leading-relaxed">
                Claim #{claim.id.slice(0, 8)} | Flight {claim.flight_number} ({claim.airline}) |
                {claim.departure_airport}→{claim.arrival_airport} |
                {formatDate(claim.departure_date, 'yyyy-MM-dd')} |
                Passenger: {claim.customer.first_name} {claim.customer.last_name} |
                Compensation: €{claim.calculated_compensation ? parseFloat(claim.calculated_compensation).toFixed(0) : '0'}
              </div>
            </div>
          </Card>
        </div>

        {/* Right column - Status & History */}
        <div className="space-y-6">
          {/* Update Status */}
          <Card className="p-4 md:p-6">
            <h2 className="text-lg font-semibold mb-4">Update Status</h2>
            <form onSubmit={handleStatusUpdate} className="space-y-4">
              <div>
                <Label htmlFor="status" className="text-xs">New Status</Label>
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
                <Label htmlFor="reason" className="text-xs">
                  Reason {selectedStatus === 'rejected' && <span className="text-destructive">*</span>}
                </Label>
                <Input
                  id="reason"
                  placeholder={selectedStatus === 'rejected' ? 'Required...' : 'Optional...'}
                  value={changeReason}
                  onChange={(e) => setChangeReason(e.target.value)}
                  disabled={isUpdatingStatus}
                  required={selectedStatus === 'rejected'}
                />
              </div>
              <Button
                type="submit"
                className="w-full"
                disabled={isUpdatingStatus || selectedStatus === claim.status}
              >
                {isUpdatingStatus ? '...' : 'Update'}
              </Button>
            </form>
          </Card>

          {/* Assign Claim */}
          <Card className="p-4 md:p-6">
            <h2 className="text-lg font-semibold mb-4">Assign</h2>

            {/* Current assignment */}
            <div className="mb-3 p-2 bg-muted/30 rounded-lg">
              <Label className="text-xs text-muted-foreground">Current</Label>
              {claim.assignee ? (
                <p className="font-medium text-sm mt-1 truncate">
                  {claim.assignee.first_name} {claim.assignee.last_name}
                </p>
              ) : (
                <p className="text-sm text-muted-foreground italic mt-1">Unassigned</p>
              )}
            </div>

            {/* Quick assign to me */}
            <Button
              onClick={handleAssignToMe}
              disabled={isAssigning}
              className="w-full mb-3"
              variant="outline"
              size="sm"
            >
              {isAssigning ? '...' : 'Assign to Me'}
            </Button>

            {/* Assign to specific admin */}
            <form onSubmit={handleAssignToAdmin} className="space-y-4">
              <div>
                <Label htmlFor="assignTo" className="text-xs">Or assign to</Label>
                <select
                  id="assignTo"
                  className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={selectedAdmin}
                  onChange={(e) => setSelectedAdmin(e.target.value)}
                  disabled={isAssigning}
                >
                  <option value="">Select...</option>
                  {adminUsers.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.first_name} {user.last_name}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                type="submit"
                className="w-full"
                disabled={isAssigning || !selectedAdmin}
              >
                {isAssigning ? '...' : 'Assign'}
              </Button>
            </form>
          </Card>

          {/* Status History */}
          <Card className="p-4 md:p-6">
            <h2 className="text-lg font-semibold mb-4">History</h2>
            {!claim.status_history || claim.status_history.length === 0 ? (
              <p className="text-muted-foreground text-sm">No changes yet</p>
            ) : (
              <div className="space-y-3">
                {claim.status_history.slice(0, 5).map((history) => (
                  <div key={history.id} className="pb-2 border-b last:border-0">
                    <div className="flex items-center gap-2 mb-1">
                      <StatusBadge status={history.new_status} />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(history.changed_at, 'MMM d, HH:mm')}
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
          <Card className="p-4 md:p-6">
            <h2 className="text-lg font-semibold mb-4">Info</h2>
            <div className="space-y-2 text-sm">
              <div>
                <Label className="text-muted-foreground text-xs">Claim ID</Label>
                <p className="font-mono text-xs truncate">{claim.id}</p>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground text-xs">Submitted</span>
                <span className="text-xs">{formatDate(claim.submitted_at, 'MMM d, yyyy')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground text-xs">Updated</span>
                <span className="text-xs">{formatDate(claim.updated_at, 'MMM d')}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Rejection Reason Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md p-6">
            <h3 className="text-lg font-semibold mb-4">Reject Document</h3>
            <div className="space-y-4">
              <div>
                <Label htmlFor="rejectionReason">Rejection Reason</Label>
                <textarea
                  id="rejectionReason"
                  className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
                  placeholder="Provide a clear reason for rejection..."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  disabled={isReviewingFile}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  The customer will receive an email with this reason.
                </p>
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={handleCancelReject}
                  disabled={isReviewingFile}
                >
                  Cancel
                </Button>
                <Button
                  variant="default"
                  onClick={handleConfirmReject}
                  disabled={isReviewingFile || !rejectionReason.trim()}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {isReviewingFile ? 'Rejecting...' : 'Reject Document'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Document Viewer Modal */}
      <DocumentViewerModal
        file={viewingFile}
        isOpen={showViewerModal}
        onClose={handleCloseViewer}
      />
    </div>
  );
}
