/**
 * Admin Dashboard - Main admin interface
 * Lists all claims with filters and search
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ClaimsTable } from '../../components/admin/ClaimsTable';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { listClaims, getAnalyticsSummary, type ClaimFilters, type AnalyticsSummary } from '../../services/admin';
import type { ClaimListItem } from '../../services/admin';

export function AdminDashboard() {
  const navigate = useNavigate();
  const [claims, setClaims] = useState<ClaimListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState<ClaimFilters>({
    skip: 0,
    limit: 50,
    sort_by: 'submitted_at',
    sort_order: 'desc',
  });

  // Load claims
  const loadClaims = async (newFilters?: ClaimFilters) => {
    setIsLoading(true);
    try {
      const filterToUse = newFilters || filters;
      const response = await listClaims(filterToUse);
      setClaims(response.claims);
      setTotal(response.total);
    } catch (error: any) {
      console.error('Failed to load claims:', error);
      toast.error(error.response?.data?.detail || 'Failed to load claims');
    } finally {
      setIsLoading(false);
    }
  };

  // Load analytics
  const loadAnalytics = async () => {
    try {
      const data = await getAnalyticsSummary();
      setAnalytics(data);
    } catch (error: any) {
      console.error('Failed to load analytics:', error);
      // Don't show error toast for analytics - it's not critical
    }
  };

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/auth');
      return;
    }

    loadClaims();
    loadAnalytics();
  }, [navigate]);

  const handleFiltersChange = (newFilters: Partial<ClaimFilters>) => {
    const updatedFilters = {
      ...filters,
      ...newFilters,
      skip: 0, // Reset pagination when filters change
    };
    setFilters(updatedFilters);
    loadClaims(updatedFilters);
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground mt-1">Manage flight compensation claims</p>
        </div>
        <Button variant="outline" onClick={() => loadClaims()}>
          Refresh
        </Button>
      </div>

      {/* Analytics Summary */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-6">
            <div className="text-sm text-muted-foreground mb-1">Total Claims</div>
            <div className="text-3xl font-bold">{analytics.total_claims}</div>
          </Card>
          <Card className="p-6">
            <div className="text-sm text-muted-foreground mb-1">Pending Review</div>
            <div className="text-3xl font-bold text-yellow-600">{analytics.pending_review}</div>
          </Card>
          <Card className="p-6">
            <div className="text-sm text-muted-foreground mb-1">Approved</div>
            <div className="text-3xl font-bold text-green-600">{analytics.approved}</div>
          </Card>
          <Card className="p-6">
            <div className="text-sm text-muted-foreground mb-1">Total Compensation</div>
            <div className="text-3xl font-bold">€{analytics.total_compensation.toFixed(0)}</div>
          </Card>
        </div>
      )}

      {/* Claims Table */}
      <ClaimsTable
        claims={claims}
        total={total}
        onFiltersChange={handleFiltersChange}
        isLoading={isLoading}
      />
    </div>
  );
}
