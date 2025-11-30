/**
 * Claims Table Component
 * Displays paginated list of claims with filters
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { StatusBadge } from './StatusBadge';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { toast } from 'react-hot-toast';
import type { ClaimListItem } from '../../services/admin';
import { bulkAssignClaims, getAdminUsers } from '../../services/admin';

interface ClaimsTableProps {
  claims: ClaimListItem[];
  total: number;
  onFiltersChange: (filters: any) => void;
  isLoading?: boolean;
}

export function ClaimsTable({ claims, total, onFiltersChange, isLoading }: ClaimsTableProps) {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [airlineFilter, setAirlineFilter] = useState('');

  // Bulk assignment state
  const [selectedClaimIds, setSelectedClaimIds] = useState<string[]>([]);
  const [adminUsers, setAdminUsers] = useState<Array<{ id: string; email: string; first_name: string; last_name: string }>>([]);
  const [selectedAdminId, setSelectedAdminId] = useState<string>('');
  const [isBulkAssigning, setIsBulkAssigning] = useState(false);

  // Load admin users on mount
  useEffect(() => {
    loadAdminUsers();
  }, []);

  const loadAdminUsers = async () => {
    try {
      const users = await getAdminUsers();
      setAdminUsers(users);
    } catch (error) {
      console.error('Failed to load admin users:', error);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[ClaimsTable] Filter button clicked');
    console.log('[ClaimsTable] Search:', searchQuery, 'Status:', statusFilter, 'Airline:', airlineFilter);
    onFiltersChange({
      search: searchQuery,
      status: statusFilter || undefined,
      airline: airlineFilter || undefined,
    });
  };

  const handleReset = () => {
    setSearchQuery('');
    setStatusFilter('');
    setAirlineFilter('');
    // Explicitly clear all filter fields
    onFiltersChange({
      search: undefined,
      status: undefined,
      airline: undefined,
    });
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedClaimIds(claims.map((claim) => claim.id));
    } else {
      setSelectedClaimIds([]);
    }
  };

  const handleSelectClaim = (claimId: string, checked: boolean) => {
    if (checked) {
      setSelectedClaimIds([...selectedClaimIds, claimId]);
    } else {
      setSelectedClaimIds(selectedClaimIds.filter((id) => id !== claimId));
    }
  };

  const handleBulkAssign = async () => {
    if (!selectedAdminId || selectedClaimIds.length === 0) {
      toast.error('Please select an admin and at least one claim');
      return;
    }

    setIsBulkAssigning(true);
    try {
      const result = await bulkAssignClaims(selectedClaimIds, selectedAdminId);
      toast.success(result.message);
      setSelectedClaimIds([]);
      setSelectedAdminId('');
      // Trigger reload by calling parent's filter change
      onFiltersChange({});
    } catch (error: any) {
      console.error('Bulk assign failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to assign claims');
    } finally {
      setIsBulkAssigning(false);
    }
  };

  const formatCurrency = (amount: string | null) => {
    if (!amount) return '—';
    return `€${parseFloat(amount).toFixed(0)}`;
  };

  const calculateDaysSince = (dateString: string): number => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card className="p-4">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Input
                placeholder="Search by customer, email, flight..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div>
              <select
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="submitted">Submitted</option>
                <option value="pending_review">Pending Review</option>
                <option value="under_review">Under Review</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="completed">Completed</option>
              </select>
            </div>
            <div>
              <Input
                placeholder="Airline (e.g., Ryanair)"
                value={airlineFilter}
                onChange={(e) => setAirlineFilter(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit" className="flex-1">
                Filter
              </Button>
              <Button type="button" variant="outline" onClick={handleReset}>
                Reset
              </Button>
            </div>
          </div>
        </form>
      </Card>

      {/* Bulk Assignment Controls */}
      {selectedClaimIds.length > 0 && (
        <Card className="p-4 bg-primary/5 border-primary/20">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <p className="text-sm font-medium">
                {selectedClaimIds.length} claim{selectedClaimIds.length > 1 ? 's' : ''} selected
              </p>
            </div>
            <div className="flex items-center gap-2">
              <select
                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={selectedAdminId}
                onChange={(e) => setSelectedAdminId(e.target.value)}
                disabled={isBulkAssigning}
              >
                <option value="">Select admin to assign...</option>
                {adminUsers.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.first_name} {user.last_name} ({user.email})
                  </option>
                ))}
              </select>
              <Button
                onClick={handleBulkAssign}
                disabled={isBulkAssigning || !selectedAdminId}
              >
                {isBulkAssigning ? 'Assigning...' : 'Assign Selected'}
              </Button>
              <Button
                variant="outline"
                onClick={() => setSelectedClaimIds([])}
                disabled={isBulkAssigning}
              >
                Clear Selection
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50 border-b">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300"
                    checked={selectedClaimIds.length === claims.length && claims.length > 0}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    disabled={isLoading || claims.length === 0}
                  />
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium">Customer</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Flight</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Route</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Incident</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Assigned To</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Compensation</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Submitted</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Age (days)</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Last Update</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Files</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {isLoading ? (
                <tr>
                  <td colSpan={13} className="px-4 py-8 text-center text-muted-foreground">
                    Loading claims...
                  </td>
                </tr>
              ) : claims.length === 0 ? (
                <tr>
                  <td colSpan={13} className="px-4 py-8 text-center text-muted-foreground">
                    No claims found
                  </td>
                </tr>
              ) : (
                claims.map((claim) => (
                  <tr
                    key={claim.id}
                    className="hover:bg-muted/50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/panel/claims/${claim.id}`)}
                  >
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        className="rounded border-gray-300"
                        checked={selectedClaimIds.includes(claim.id)}
                        onChange={(e) => handleSelectClaim(claim.id, e.target.checked)}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <span className="font-medium text-sm">
                          {claim.customer.first_name} {claim.customer.last_name}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {claim.customer.email}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <span className="font-medium text-sm">{claim.flight_number}</span>
                        <span className="text-xs text-muted-foreground">{claim.airline}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm">
                        {claim.departure_airport} → {claim.arrival_airport}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm capitalize">
                        {claim.incident_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {claim.assignee ? (
                        <div className="flex flex-col">
                          <span className="font-medium text-sm">
                            {claim.assignee.first_name} {claim.assignee.last_name}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {claim.assignee.email}
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground italic">Unassigned</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={claim.status} />
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-medium text-sm">
                        {formatCurrency(claim.calculated_compensation)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-muted-foreground">
                        {format(new Date(claim.submitted_at), 'MMM d, yyyy')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium">
                        {calculateDaysSince(claim.submitted_at)}d
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-muted-foreground">
                        {calculateDaysSince(claim.updated_at)}d ago
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">{claim.file_count} files</span>
                        {claim.note_count > 0 && (
                          <span className="text-muted-foreground">· {claim.note_count} notes</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/panel/claims/${claim.id}`);
                        }}
                      >
                        View
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination info */}
        {!isLoading && claims.length > 0 && (
          <div className="px-4 py-3 border-t bg-muted/20">
            <p className="text-sm text-muted-foreground">
              Showing {claims.length} of {total} claims
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
