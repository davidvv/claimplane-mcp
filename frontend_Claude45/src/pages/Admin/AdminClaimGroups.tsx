/**
 * Admin Claim Groups Page - Manage multi-passenger claim groups
 * 
 * WP #365: Admin Dashboard for Claim Groups
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { 
  Users, 
  Plane, 
  Calendar, 
  Euro, 
  Search, 
  Filter, 
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  MessageSquare,
  AlertCircle,
  Loader2
} from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { formatCurrency, formatDateTime, getStatusLabel, getStatusColor } from '@/lib/utils';
import apiClient from '@/services/api';

interface ClaimGroup {
  id: string;
  group_name: string | null;
  flight_number: string;
  flight_date: string;
  total_claims: number;
  total_compensation: number | null;
  status_summary: Record<string, number>;
  created_at: string;
  account_holder_id: string;
}

interface ClaimGroupDetail extends ClaimGroup {
  consent_confirmed: boolean;
  consent_confirmed_at: string | null;
  claims: Array<{
    id: string;
    status: string;
    compensation_amount: number | null;
    passenger_name: string;
    flight_info: {
      airline: string;
      flightNumber: string;
      departureAirport: string;
      arrivalAirport: string;
    };
  }>;
  notes: Array<{
    id: string;
    admin_id: string;
    note_text: string;
    created_at: string;
  }>;
}

export function AdminClaimGroups() {
  useDocumentTitle('Admin - Claim Groups');
  const navigate = useNavigate();
  
  const [groups, setGroups] = useState<ClaimGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<ClaimGroupDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [noteText, setNoteText] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    dateFrom: '',
    dateTo: '',
  });

  // Load claim groups
  const loadGroups = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);
      if (searchQuery) params.append('flight_number', searchQuery);

      const response = await apiClient.get(`/admin/claim-groups?${params.toString()}`);
      if (response.data.success) {
        setGroups(response.data.data.groups || []);
      }
    } catch (error: any) {
      console.error('Failed to load claim groups:', error);
      toast.error('Failed to load claim groups');
    } finally {
      setIsLoading(false);
    }
  };

  // Load group details
  const loadGroupDetail = async (groupId: string) => {
    setIsDetailLoading(true);
    try {
      const response = await apiClient.get(`/admin/claim-groups/${groupId}`);
      if (response.data.success) {
        setSelectedGroup(response.data.data);
      }
    } catch (error: any) {
      console.error('Failed to load group detail:', error);
      toast.error('Failed to load group details');
    } finally {
      setIsDetailLoading(false);
    }
  };

  // Bulk action
  const handleBulkAction = async (action: 'approve_all' | 'reject_all' | 'request_info_all') => {
    if (!selectedGroup) return;
    
    setIsActionLoading(true);
    try {
      const response = await apiClient.put(`/admin/claim-groups/${selectedGroup.id}/bulk-action`, {
        action,
        rejection_reason: action === 'reject_all' ? 'Bulk rejection' : undefined,
      });
      
      if (response.data.success) {
        toast.success(response.data.message);
        // Reload group detail
        await loadGroupDetail(selectedGroup.id);
        // Reload list
        await loadGroups();
      }
    } catch (error: any) {
      console.error('Bulk action failed:', error);
      toast.error(error.response?.data?.detail || 'Bulk action failed');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Add note
  const handleAddNote = async () => {
    if (!selectedGroup || !noteText.trim()) return;
    
    try {
      const response = await apiClient.post(`/admin/claim-groups/${selectedGroup.id}/notes`, {
        note_text: noteText,
      });
      
      if (response.data.success) {
        toast.success('Note added successfully');
        setNoteText('');
        // Reload group detail to show new note
        await loadGroupDetail(selectedGroup.id);
      }
    } catch (error: any) {
      console.error('Failed to add note:', error);
      toast.error('Failed to add note');
    }
  };

  useEffect(() => {
    loadGroups();
  }, [filters]);

  // Calculate overall status
  const getGroupStatus = (statusSummary: Record<string, number>): string => {
    const statuses = Object.keys(statusSummary);
    if (statuses.length === 0) return 'pending';
    if (statuses.length === 1) return statuses[0];
    return 'mixed';
  };

  // List View
  if (!selectedGroup) {
    return (
      <div className="min-h-screen bg-background py-8 md:py-12">
        <div className="container mx-auto px-4 max-w-7xl">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Claim Groups</h1>
            <p className="text-muted-foreground">
              Manage multi-passenger claim groups and perform bulk operations
            </p>
          </div>

          {/* Filters */}
          <Card className="mb-6">
            <CardContent className="pt-6">
              <div className="flex flex-wrap gap-4">
                <div className="flex-1 min-w-[200px]">
                  <div className="relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search by flight number..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && loadGroups()}
                      className="pl-10"
                    />
                  </div>
                </div>
                
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                  className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">All Statuses</option>
                  <option value="submitted">Submitted</option>
                  <option value="under_review">Under Review</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                </select>

                <Input
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                  className="w-auto"
                />
                
                <Input
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                  className="w-auto"
                />

                <Button onClick={loadGroups}>
                  <Filter className="w-4 h-4 mr-2" />
                  Filter
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Groups List */}
          {isLoading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : groups.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No claim groups found</h3>
                <p className="text-muted-foreground">
                  Try adjusting your filters or search criteria
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {groups.map((group) => (
                <Card
                  key={group.id}
                  className="cursor-pointer hover:shadow-lg transition-shadow border-l-4 border-l-primary"
                  onClick={() => loadGroupDetail(group.id)}
                >
                  <CardContent className="p-6">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Users className="w-5 h-5 text-primary" />
                          <h3 className="text-lg font-semibold">
                            {group.group_name || `Group - ${group.flight_number}`}
                          </h3>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Plane className="w-4 h-4" />
                            {group.flight_number}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {formatDateTime(group.flight_date)}
                          </span>
                          <span>{group.total_claims} passengers</span>
                        </div>
                      </div>

                      <div className="flex flex-col items-end gap-2">
                        <Badge className={getStatusColor(getGroupStatus(group.status_summary))}>
                          {getGroupStatus(group.status_summary) === 'mixed' 
                            ? 'Mixed Status' 
                            : getStatusLabel(getGroupStatus(group.status_summary))}
                        </Badge>
                        
                        {group.total_compensation && (
                          <div className="flex items-center gap-1 text-sm font-medium text-primary">
                            <Euro className="w-4 h-4" />
                            {formatCurrency(Number(group.total_compensation), 'EUR')}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Status Summary */}
                    <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t">
                      {Object.entries(group.status_summary).map(([status, count]) => (
                        <Badge key={status} variant="outline" className="text-xs">
                          {getStatusLabel(status)}: {count}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Detail View
  return (
    <div className="min-h-screen bg-background py-8 md:py-12">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Back Button */}
        <Button
          variant="ghost"
          className="mb-6"
          onClick={() => setSelectedGroup(null)}
        >
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back to Groups
        </Button>

        {isDetailLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <>
            {/* Group Header */}
            <div className="mb-8">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h1 className="text-3xl font-bold mb-2">
                    {selectedGroup.group_name || `Group - ${selectedGroup.flight_number}`}
                  </h1>
                  <div className="flex items-center gap-4 text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Plane className="w-4 h-4" />
                      {selectedGroup.flight_number}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {formatDateTime(selectedGroup.flight_date)}
                    </span>
                    <Badge className={getStatusColor(getGroupStatus(selectedGroup.status_summary))}>
                      {getGroupStatus(selectedGroup.status_summary) === 'mixed' 
                        ? 'Mixed Status' 
                        : getStatusLabel(getGroupStatus(selectedGroup.status_summary))}
                    </Badge>
                  </div>
                </div>

                {/* Bulk Actions */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => handleBulkAction('request_info_all')}
                    disabled={isActionLoading}
                  >
                    {isActionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <MessageSquare className="w-4 h-4 mr-2" />}
                    Request Info
                  </Button>
                  <Button
                    variant="default"
                    className="bg-green-600 hover:bg-green-700"
                    onClick={() => handleBulkAction('approve_all')}
                    disabled={isActionLoading}
                  >
                    {isActionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                    Approve All
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => handleBulkAction('reject_all')}
                    disabled={isActionLoading}
                  >
                    {isActionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4 mr-2" />}
                    Reject All
                  </Button>
                </div>
              </div>
            </div>

            <div className="grid lg:grid-cols-3 gap-6">
              {/* Claims List */}
              <div className="lg:col-span-2 space-y-4">
                <h2 className="text-xl font-semibold mb-4">
                  Claims ({selectedGroup.claims?.length || 0})
                </h2>
                
                {selectedGroup.claims?.map((claim) => (
                  <Card key={claim.id} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-medium">{claim.passenger_name}</h3>
                          <p className="text-sm text-muted-foreground">
                            {claim.flight_info.airline} {claim.flight_info.flightNumber}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {claim.flight_info.departureAirport} → {claim.flight_info.arrivalAirport}
                          </p>
                        </div>
                        <div className="text-right">
                          <Badge className={getStatusColor(claim.status)}>
                            {getStatusLabel(claim.status)}
                          </Badge>
                          {claim.compensation_amount && (
                            <p className="text-sm font-medium text-primary mt-1">
                              {formatCurrency(Number(claim.compensation_amount), 'EUR')}
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Consent Info */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Authorization Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2">
                      {selectedGroup.consent_confirmed ? (
                        <>
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <span className="text-sm">Consent confirmed</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-5 h-5 text-amber-600" />
                          <span className="text-sm">Consent pending</span>
                        </>
                      )}
                    </div>
                    {selectedGroup.consent_confirmed_at && (
                      <p className="text-xs text-muted-foreground mt-2">
                        Confirmed on {formatDateTime(selectedGroup.consent_confirmed_at)}
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* Notes */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Admin Notes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {selectedGroup.notes?.map((note) => (
                        <div key={note.id} className="bg-muted p-3 rounded-lg">
                          <p className="text-sm">{note.note_text}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatDateTime(note.created_at)}
                          </p>
                        </div>
                      ))}
                      
                      <div className="space-y-2">
                        <textarea
                          value={noteText}
                          onChange={(e) => setNoteText(e.target.value)}
                          placeholder="Add a note..."
                          className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                        />
                        <Button 
                          onClick={handleAddNote} 
                          disabled={!noteText.trim()}
                          className="w-full"
                          size="sm"
                        >
                          <MessageSquare className="w-4 h-4 mr-2" />
                          Add Note
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Total Compensation */}
                {selectedGroup.total_compensation && (
                  <Card className="bg-primary/5 border-primary">
                    <CardHeader>
                      <CardTitle className="text-sm text-primary">Total Compensation</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-3xl font-bold text-primary">
                        {formatCurrency(Number(selectedGroup.total_compensation), 'EUR')}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        For {selectedGroup.total_claims} passengers
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
