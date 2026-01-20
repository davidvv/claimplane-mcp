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
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ClaimFilters>({
    skip: 0,
    limit: 50,
    sort_by: 'submitted_at',
    sort_order: 'desc',
  });

  // Load claims
  const loadClaims = async (newFilters?: ClaimFilters) => {
    setIsLoading(true);
    setError(null);
    try {
      const filterToUse = newFilters || filters;
      console.log('[AdminDashboard] loadClaims with filters:', filterToUse);
      const response = await listClaims(filterToUse);
      console.log('[AdminDashboard] Received claims:', response.claims.length, 'Total:', response.total);
      setClaims(response.claims);
      setTotal(response.total);
    } catch (error: any) {
      console.error('Failed to load claims:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to load claims. Please check your authentication.';
      setError(errorMessage);
      toast.error(errorMessage);
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
    // Check if user is authenticated (user_email stored in localStorage after login)
    const userEmail = localStorage.getItem('user_email');
    if (!userEmail) {
      navigate('/auth');
      return;
    }

    loadClaims();
    loadAnalytics();
  }, [navigate]);

  const handleFiltersChange = (newFilters: Partial<ClaimFilters>) => {
    console.log('[AdminDashboard] handleFiltersChange called with:', newFilters);
    console.log('[AdminDashboard] Current filters:', filters);
    const updatedFilters = {
      ...filters,
      ...newFilters,
      skip: 0, // Reset pagination when filters change
    };
    console.log('[AdminDashboard] Updated filters:', updatedFilters);
    setFilters(updatedFilters);
    loadClaims(updatedFilters);
  };

  return (
    <div className="container mx-auto py-6 md:py-8 space-y-6 px-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground mt-1 text-sm">Manage flight compensation claims</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => loadClaims()}>
          Refresh
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="p-4 border-destructive bg-destructive/10">
          <div className="flex items-start gap-3">
            <div className="text-destructive font-bold text-lg">!</div>
            <div className="flex-1">
              <h3 className="font-semibold text-destructive mb-1">Error</h3>
              <p className="text-sm text-muted-foreground">{error}</p>
              <p className="text-sm text-muted-foreground mt-2">
                Make sure you're logged in as an admin.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Analytics Summary */}
      {analytics && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 md:gap-4">
          <Card 
            className={`p-4 cursor-pointer transition-all hover:ring-2 hover:ring-primary/20 ${!filters.status ? 'ring-2 ring-primary/40 bg-primary/5' : ''}`}
            onClick={() => handleFiltersChange({ status: undefined })}
          >
            <div className="text-xs text-muted-foreground mb-1">Total</div>
            <div className="text-2xl md:text-3xl font-bold">{analytics.total_claims || 0}</div>
          </Card>
          
          <Card 
            className={`p-4 cursor-pointer transition-all hover:ring-2 hover:ring-primary/20 ${filters.status === 'draft' ? 'ring-2 ring-primary/40 bg-primary/5' : ''}`}
            onClick={() => handleFiltersChange({ status: 'draft' })}
          >
            <div className="text-xs text-muted-foreground mb-1">Drafts</div>
            <div className="text-2xl md:text-3xl font-bold text-gray-500">
              {analytics.claims_by_status?.draft || 0}
            </div>
          </Card>

          <Card 
            className={`p-4 cursor-pointer transition-all hover:ring-2 hover:ring-primary/20 ${filters.status === 'pending_review' ? 'ring-2 ring-primary/40 bg-primary/5' : ''}`}
            onClick={() => handleFiltersChange({ status: 'pending_review' })}
          >
            <div className="text-xs text-muted-foreground mb-1">Pending</div>
            <div className="text-2xl md:text-3xl font-bold text-yellow-600">{analytics.pending_review || 0}</div>
          </Card>
          
          <Card 
            className={`p-4 cursor-pointer transition-all hover:ring-2 hover:ring-primary/20 ${filters.status === 'approved' ? 'ring-2 ring-primary/40 bg-primary/5' : ''}`}
            onClick={() => handleFiltersChange({ status: 'approved' })}
          >
            <div className="text-xs text-muted-foreground mb-1">Approved</div>
            <div className="text-2xl md:text-3xl font-bold text-green-600">{analytics.approved || 0}</div>
          </Card>
          
          <Card className="p-4">
            <div className="text-xs text-muted-foreground mb-1">Total Comp</div>
            <div className="text-2xl md:text-3xl font-bold">€{(analytics.total_compensation || 0).toFixed(0)}</div>
          </Card>
        </div>
      )}

      {/* Claims Table */}
      <ClaimsTable
        claims={claims}
        total={total}
        filters={filters}
        onFiltersChange={handleFiltersChange}
        isLoading={isLoading}
      />
    </div>
  );
}
