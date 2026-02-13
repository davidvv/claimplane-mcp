/**
 * My Claims Page - Shows all claims and claim groups for the authenticated user
 *
 * Note: Admins and superadmins will be automatically redirected to the admin dashboard.
 * This page is designed for customers to view their own claims.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Euro, Calendar, Plane, Users, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

import { listClaims } from '@/services/claims';
import { getMyClaimGroups, type ClaimGroup } from '@/services/claimGroups';
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
 * Get user role from sessionStorage (stored during login)
 * Note: JWT tokens are in HTTP-only cookies, user info is in sessionStorage for UI
 */
function getUserRole(): string | null {
  return sessionStorage.getItem('user_role');
}

export function MyClaims() {
  useDocumentTitle('My Claims');
  const navigate = useNavigate();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [claimGroups, setClaimGroups] = useState<ClaimGroup[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'claims' | 'groups'>('claims');

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Check if user is authenticated (user_email is stored in sessionStorage after login)
        const userEmail = sessionStorage.getItem('user_email');
        console.log('[MyClaims] User authenticated:', !!userEmail);

        if (!userEmail) {
          console.log('[MyClaims] No user info found, redirecting to auth');
          toast.error('Please log in to view your claims');
          navigate('/auth');
          return;
        }

        // Redirect admins and superadmins to the admin dashboard
        // The "My Claims" page is designed for customers only
        const userRole = getUserRole();
        console.log('[MyClaims] User role:', userRole);

        if (userRole === 'admin' || userRole === 'superadmin') {
          console.log('[MyClaims] Admin/superadmin detected, redirecting to admin dashboard');
          toast.info('Redirecting to Admin Dashboard...', {
            description: 'Use the admin dashboard to manage all claims.'
          });
          navigate('/panel/dashboard', { replace: true });
          return;
        }

        console.log('[MyClaims] Fetching claims and groups...');
        
        // Fetch both claims and claim groups in parallel
        const [claimsArray, groupsArray] = await Promise.all([
          listClaims({ limit: 100, includeDrafts: true }),
          getMyClaimGroups().catch(() => []) // Don't fail if claim groups endpoint fails
        ]);
        
        console.log('[MyClaims] Claims count:', claimsArray.length);
        console.log('[MyClaims] Claim groups count:', groupsArray.length);

        setClaims(claimsArray);
        setClaimGroups(groupsArray);
      } catch (error: any) {
        console.error('[MyClaims] Failed to fetch claims:', error);
        console.error('[MyClaims] Error response:', error.response);

        if (error.response?.status === 401) {
          toast.error('Session expired. Please log in again');
          sessionStorage.removeItem('auth_token');
          sessionStorage.removeItem('refresh_token');
          navigate('/auth');
        } else {
          toast.error('Failed to load your claims');
        }
      } finally {
        console.log('[MyClaims] Setting isLoading to false');
        setIsLoading(false);
      }
    };

    fetchData();
  }, [navigate]);

  const handleViewClaim = (claim: Claim) => {
    if (claim.status === 'draft') {
      navigate(`/claim/new?resume=${claim.id}`);
    } else {
      navigate(`/status?claimId=${claim.id}`);
    }
  };

  const handleViewGroup = (group: ClaimGroup) => {
    navigate(`/claim-groups/${group.id}`);
  };

  // Calculate overall status for a claim group
  const getGroupStatus = (statusSummary: Record<string, number>): string => {
    const statuses = Object.keys(statusSummary);
    if (statuses.length === 0) return 'pending';
    if (statuses.length === 1) return statuses[0];
    return 'mixed';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8 md:py-12">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="mb-6 md:mb-8">
          <h1 className="text-2xl md:text-3xl font-bold mb-2">My Claims</h1>
          <p className="text-muted-foreground text-sm">
            View and manage your flight compensation claims
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 border-b border-border">
          <button
            onClick={() => setActiveTab('claims')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'claims'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            Individual Claims
            {claims.length > 0 && (
              <span className="ml-2 px-2 py-0.5 text-xs bg-muted rounded-full">
                {claims.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('groups')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'groups'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            Claim Groups
            {claimGroups.length > 0 && (
              <span className="ml-2 px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">
                {claimGroups.length}
              </span>
            )}
          </button>
        </div>

        {/* Individual Claims Tab */}
        {activeTab === 'claims' && (
          <>
            {claims.length === 0 ? (
              <Card>
                <CardContent className="py-8 md:py-12 text-center">
                  <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg md:text-xl font-semibold mb-2">
                    No claims yet
                  </h3>
                  <p className="text-muted-foreground mb-6 text-sm">
                    You haven't submitted any flight compensation claims yet.
                  </p>
                  <Button onClick={() => navigate('/claim')}>
                    Submit Your First Claim
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:gap-6 grid-cols-1">
                {claims.map((claim) => (
                  <Card
                    key={claim.id}
                    className={`transition-all duration-200 cursor-pointer ${
                      claim.status === 'draft' 
                        ? 'border-dashed bg-muted/20 hover:bg-muted/30' 
                        : 'hover:shadow-lg'
                    }`}
                    onClick={() => handleViewClaim(claim)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <Plane className={`w-5 h-5 flex-shrink-0 ${claim.status === 'draft' ? 'text-muted-foreground' : 'text-primary'}`} />
                          <CardTitle className={`text-lg truncate ${claim.status === 'draft' ? 'text-muted-foreground' : ''}`}>
                            {claim.flightInfo.airline} {claim.flightInfo.flightNumber}
                          </CardTitle>
                        </div>
                        <Badge className={getStatusColor(claim.status || 'draft')} variant={claim.status === 'draft' ? 'outline' : 'default'}>
                          {getStatusLabel(claim.status || 'draft')}
                        </Badge>
                      </div>
                      <CardDescription className="truncate">
                        {claim.flightInfo.departureAirport} → {claim.flightInfo.arrivalAirport}
                      </CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-3">
                      {/* Flight Date */}
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Calendar className="w-4 h-4 flex-shrink-0" />
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
                        <div className={`flex items-center gap-2 p-3 rounded-lg ${claim.status === 'draft' ? 'bg-muted/50' : 'bg-primary/10'}`}>
                          <Euro className={`w-5 h-5 flex-shrink-0 ${claim.status === 'draft' ? 'text-muted-foreground' : 'text-primary'}`} />
                          <div>
                            <p className="text-xs text-muted-foreground">
                              Estimated Amount
                            </p>
                            <p className={`text-lg font-bold ${claim.status === 'draft' ? 'text-muted-foreground' : 'text-primary'}`}>
                              {formatCurrency(Number(claim.compensationAmount), claim.currency)}
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Submission Date */}
                      {claim.submittedAt && claim.status !== 'draft' ? (
                        <div className="pt-2 border-t text-xs text-muted-foreground">
                          Submitted {formatDateTime(claim.submittedAt)}
                        </div>
                      ) : claim.updatedAt && (
                        <div className="pt-2 border-t text-xs text-muted-foreground italic">
                          Last updated {formatDateTime(claim.updatedAt)}
                        </div>
                      )}

                      {/* Action Button */}
                      <Button
                        className="w-full mt-2"
                        size="sm"
                        variant={claim.status === 'draft' ? 'outline' : 'default'}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewClaim(claim);
                        }}
                      >
                        {claim.status === 'draft' ? 'Resume Draft' : 'View Details'}
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </>
        )}

        {/* Claim Groups Tab */}
        {activeTab === 'groups' && (
          <>
            {claimGroups.length === 0 ? (
              <Card>
                <CardContent className="py-8 md:py-12 text-center">
                  <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg md:text-xl font-semibold mb-2">
                    No claim groups yet
                  </h3>
                  <p className="text-muted-foreground mb-2 text-sm">
                    Claim groups let you file for multiple passengers at once.
                  </p>
                  <p className="text-muted-foreground mb-6 text-sm">
                    When you file a claim for multiple people, they'll appear here.
                  </p>
                  <Button onClick={() => navigate('/claim')}>
                    File a Claim
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:gap-6 grid-cols-1">
                {claimGroups.map((group) => (
                  <Card
                    key={group.id}
                    className="transition-all duration-200 cursor-pointer hover:shadow-lg border-l-4 border-l-primary"
                    onClick={() => handleViewGroup(group)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <Users className="w-5 h-5 flex-shrink-0 text-primary" />
                          <CardTitle className="text-lg truncate">
                            {group.group_name || `Group - ${group.flight_number}`}
                          </CardTitle>
                        </div>
                        <Badge 
                          className={getStatusColor(getGroupStatus(group.status_summary))} 
                          variant="default"
                        >
                          {getGroupStatus(group.status_summary) === 'mixed' 
                            ? 'Mixed Status' 
                            : getStatusLabel(getGroupStatus(group.status_summary))}
                        </Badge>
                      </div>
                      <CardDescription className="truncate">
                        {group.total_claims} passengers • Flight {group.flight_number}
                      </CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-3">
                      {/* Flight Date */}
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Calendar className="w-4 h-4 flex-shrink-0" />
                        <span>{formatDateTime(group.flight_date)}</span>
                      </div>

                      {/* Status Summary */}
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(group.status_summary).map(([status, count]) => (
                          <Badge 
                            key={status} 
                            variant="outline" 
                            className="text-xs"
                          >
                            {getStatusLabel(status)}: {count}
                          </Badge>
                        ))}
                      </div>

                      {/* Total Compensation */}
                      {group.total_compensation && (
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-primary/10">
                          <Euro className="w-5 h-5 flex-shrink-0 text-primary" />
                          <div>
                            <p className="text-xs text-muted-foreground">
                              Total Estimated Amount
                            </p>
                            <p className="text-lg font-bold text-primary">
                              {formatCurrency(Number(group.total_compensation), 'EUR')}
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Created Date */}
                      <div className="pt-2 border-t text-xs text-muted-foreground">
                        Created {formatDateTime(group.created_at)}
                      </div>

                      {/* Action Button */}
                      <Button
                        className="w-full mt-2"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewGroup(group);
                        }}
                      >
                        View Group Details
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
