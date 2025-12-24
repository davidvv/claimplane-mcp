/**
 * My Claims Page - Shows all claims for the authenticated user
 *
 * Note: Admins and superadmins will be automatically redirected to the admin dashboard.
 * This page is designed for customers to view their own claims.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Euro, Calendar, Plane } from 'lucide-react';
import { toast } from 'sonner';

import { listClaims } from '@/services/claims';
import type { Claim } from '@/types/api';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import {
  formatCurrency,
  formatDateTime,
  getStatusLabel,
  getStatusColor,
  getIncidentLabel,
} from '@/lib/utils';

/**
 * Decode JWT token to get user role
 */
function getUserRoleFromToken(): string | null {
  const token = localStorage.getItem('auth_token');
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.role || null;
  } catch (error) {
    console.error('Failed to decode token:', error);
    return null;
  }
}

export function MyClaims() {
  useDocumentTitle('My Claims');
  const navigate = useNavigate();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchClaims = async () => {
      try {
        // Check if user is authenticated
        const token = localStorage.getItem('auth_token');
        console.log('[MyClaims] Auth token present:', !!token);

        if (!token) {
          console.log('[MyClaims] No token found, redirecting to auth');
          toast.error('Please log in to view your claims');
          navigate('/auth');
          return;
        }

        // Redirect admins and superadmins to the admin dashboard
        // The "My Claims" page is designed for customers only
        const userRole = getUserRoleFromToken();
        console.log('[MyClaims] User role:', userRole);

        if (userRole === 'admin' || userRole === 'superadmin') {
          console.log('[MyClaims] Admin/superadmin detected, redirecting to admin dashboard');
          toast.info('Redirecting to Admin Dashboard...', {
            description: 'Use the admin dashboard to manage all claims.'
          });
          navigate('/panel/dashboard', { replace: true });
          return;
        }

        console.log('[MyClaims] Fetching claims...');
        const response = await listClaims({ limit: 100 }); // Get all user's claims
        console.log('[MyClaims] Claims response:', response);

        // Backend returns plain array, not paginated response
        const claimsArray = Array.isArray(response) ? response : (response.data || []);
        console.log('[MyClaims] Claims count:', claimsArray.length);

        setClaims(claimsArray);
      } catch (error: any) {
        console.error('[MyClaims] Failed to fetch claims:', error);
        console.error('[MyClaims] Error response:', error.response);

        if (error.response?.status === 401) {
          toast.error('Session expired. Please log in again');
          localStorage.removeItem('auth_token');
          localStorage.removeItem('refresh_token');
          navigate('/auth');
        } else {
          toast.error('Failed to load your claims');
        }
      } finally {
        console.log('[MyClaims] Setting isLoading to false');
        setIsLoading(false);
      }
    };

    fetchClaims();
  }, [navigate]);

  const handleViewClaim = (claimId: string) => {
    navigate(`/status?claimId=${claimId}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">My Claims</h1>
          <p className="text-muted-foreground">
            View and manage all your flight compensation claims
          </p>
        </div>

        {claims.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">
                No claims yet
              </h3>
              <p className="text-muted-foreground mb-6">
                You haven't submitted any flight compensation claims yet.
              </p>
              <Button onClick={() => navigate('/claim')}>
                Submit Your First Claim
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 md:grid-cols-2">
            {claims.map((claim) => (
              <Card
                key={claim.id}
                className="hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => handleViewClaim(claim.id!)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Plane className="w-5 h-5 text-primary" />
                      <CardTitle className="text-lg">
                        {claim.flightInfo.airline} {claim.flightInfo.flightNumber}
                      </CardTitle>
                    </div>
                    <Badge className={getStatusColor(claim.status || 'draft')}>
                      {getStatusLabel(claim.status || 'draft')}
                    </Badge>
                  </div>
                  <CardDescription>
                    {claim.flightInfo.departureAirport} → {claim.flightInfo.arrivalAirport}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Flight Date */}
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="w-4 h-4" />
                    <span>{formatDateTime(claim.flightInfo.departureDate)}</span>
                  </div>

                  {/* Incident Type */}
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium text-foreground">
                      Issue:
                    </span>
                    <span className="text-muted-foreground">
                      {getIncidentLabel(claim.incidentType)}
                    </span>
                  </div>

                  {/* Compensation Amount */}
                  {claim.compensationAmount && (
                    <div className="flex items-center gap-2 bg-primary/10 p-3 rounded-lg">
                      <Euro className="w-5 h-5 text-primary" />
                      <div>
                        <p className="text-xs text-muted-foreground">
                          Eligible Amount
                        </p>
                        <p className="text-lg font-bold text-primary">
                          {formatCurrency(claim.compensationAmount, claim.currency)}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Submission Date */}
                  {claim.submittedAt && (
                    <div className="pt-3 border-t text-xs text-muted-foreground">
                      Submitted {formatDateTime(claim.submittedAt)}
                    </div>
                  )}

                  {/* View Details Button */}
                  <Button
                    className="w-full"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleViewClaim(claim.id!);
                    }}
                  >
                    View Details
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
