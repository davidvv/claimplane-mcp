import React, { useState } from 'react';
import { Search, Clock, CheckCircle, XCircle, AlertCircle, Download, Eye } from 'lucide-react';
import { getClaim, getMockClaim, getClaimTimeline, getClaimStatusInfo } from '../services/claims';
import { formatFileSize, getDocumentTypeLabel, getFileIcon } from '../services/documents';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

export default function Status() {
  const [claimId, setClaimId] = useState('');
  const [claim, setClaim] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  
  const { isAuthenticated } = useAuth();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!claimId.trim()) {
      toast.error('Please enter a claim ID');
      return;
    }
    
    setIsSearching(true);
    setIsLoading(true);
    
    try {
      // Try to get claim from API first
      try {
        const claimData = await getClaim(claimId.trim());
        setClaim(claimData);
      } catch (error) {
        // If API fails, use mock data for demo
        console.log('Using mock data for demo');
        const mockClaim = getMockClaim(claimId.trim());
        setClaim(mockClaim);
      }
      
      toast.success('Claim found successfully!');
    } catch (error) {
      toast.error('Claim not found. Please check your claim ID.');
      setClaim(null);
    } finally {
      setIsSearching(false);
      setIsLoading(false);
    }
  };

  const handleDownloadDocument = async (documentId: string, filename: string) => {
    try {
      // In a real app, this would download the actual document
      toast.success(`Downloading ${filename}...`);
      
      // Create a mock download
      const link = document.createElement('a');
      link.href = '#';
      link.download = filename;
      link.click();
    } catch (error) {
      toast.error('Failed to download document');
    }
  };

  const timeline = claim ? getClaimTimeline(claim) : [];
  const statusInfo = claim ? getClaimStatusInfo(claim.status) : null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Check Your Claim Status
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Enter your claim ID to view the status and details of your compensation claim.
          </p>
        </div>

        {/* Search Form */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label htmlFor="claimId" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Claim ID
              </label>
              <div className="relative">
                <input
                  id="claimId"
                  type="text"
                  value={claimId}
                  onChange={(e) => setClaimId(e.target.value)}
                  placeholder="Enter your claim ID (e.g., 123e4567-e89b-12d3-a456-426614174002)"
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              </div>
            </div>
            
            <button
              type="submit"
              disabled={isSearching}
              className="w-full flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {isSearching ? (
                <>
                  <Clock className="animate-spin h-4 w-4 mr-2" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Check Status
                </>
              )}
            </button>
          </form>
        </div>

        {/* Claim Details */}
        {claim && (
          <div className="space-y-8">
            {/* Status Overview */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Claim Overview
                </h2>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${statusInfo?.color === 'green' ? 'bg-green-500' : statusInfo?.color === 'yellow' ? 'bg-yellow-500' : statusInfo?.color === 'red' ? 'bg-red-500' : 'bg-gray-500'}`}></div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {statusInfo?.label}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Claim ID</h3>
                  <p className="text-gray-900 dark:text-white">{claim.id}</p>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Submitted</h3>
                  <p className="text-gray-900 dark:text-white">
                    {new Date(claim.submittedAt).toLocaleDateString()}
                  </p>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Flight</h3>
                  <p className="text-gray-900 dark:text-white">
                    {claim.flightInfo.flightNumber} - {claim.flightInfo.airline}
                  </p>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Compensation</h3>
                  <p className="text-gray-900 dark:text-white">
                    {claim.compensationAmount ? `€${claim.compensationAmount}` : 'Calculating...'}
                  </p>
                </div>
              </div>
            </div>

            {/* Timeline */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                Claim Timeline
              </h2>
              
              <div className="space-y-4">
                {timeline.map((step, index) => (
                  <div key={step.id} className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        step.completed 
                          ? 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400' 
                          : step.current
                          ? 'bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500'
                      }`}>
                        {step.completed ? (
                          <CheckCircle className="h-4 w-4" />
                        ) : step.current ? (
                          <Clock className="h-4 w-4" />
                        ) : (
                          <div className="w-2 h-2 bg-current rounded-full" />
                        )}
                      </div>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                          {step.label}
                        </h3>
                        {step.date && (
                          <span className="text-sm text-gray-500 dark:text-gray-400">
                            {new Date(step.date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {step.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Documents */}
            {claim.documents && claim.documents.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  Uploaded Documents
                </h2>
                
                <div className="space-y-4">
                  {claim.documents.map((doc: any) => (
                    <div key={doc.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="text-2xl">{getFileIcon(doc.contentType)}</div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            {getDocumentTypeLabel(doc.documentType)}
                          </h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {doc.filename} • {formatFileSize(doc.size)}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleDownloadDocument(doc.id, doc.filename)}
                          className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors duration-200"
                          title="Download document"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        
                        <button
                          className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors duration-200"
                          title="View document"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Notes */}
            {claim.notes && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Additional Notes
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  {claim.notes}
                </p>
              </div>
            )}
          </div>
        )}

        {/* No results message */}
        {!claim && !isLoading && claimId && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2" />
              <p className="text-yellow-800 dark:text-yellow-200">
                No claim found with ID "{claimId}". Please check your claim ID and try again.
              </p>
            </div>
          </div>
        )}

        {/* Authentication notice */}
        {!isAuthenticated && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
              <p className="text-blue-800 dark:text-blue-200">
                <strong>Pro tip:</strong> Sign in to access additional features and view all your claims in one place.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}