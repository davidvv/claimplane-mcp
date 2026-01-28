/**
 * Document Viewer Modal - View uploaded documents in admin panel
 * Supports PDFs and images natively, triggers download for other file types
 */

import { useEffect, useState, useCallback } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { downloadClaimFile, type ClaimFile } from '../../services/admin';

interface DocumentViewerModalProps {
  file: ClaimFile | null;
  isOpen: boolean;
  onClose: () => void;
}

export function DocumentViewerModal({ file, isOpen, onClose }: DocumentViewerModalProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Determine file type for rendering
  const getFileType = useCallback((mimeType: string): 'pdf' | 'image' | 'other' => {
    if (mimeType === 'application/pdf') return 'pdf';
    if (mimeType.startsWith('image/')) return 'image';
    return 'other';
  }, []);

  // Fetch file when modal opens
  useEffect(() => {
    if (!isOpen || !file) {
      // Cleanup blob URL when modal closes
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
        setBlobUrl(null);
      }
      return;
    }

    const fetchFile = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const blob = await downloadClaimFile(file.id);
        const url = URL.createObjectURL(blob);
        setBlobUrl(url);

        // For non-viewable files, trigger download immediately
        const fileType = getFileType(file.mime_type);
        if (fileType === 'other') {
          const a = document.createElement('a');
          a.href = url;
          a.download = file.original_filename || 'download';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          onClose();
        }
      } catch (err: any) {
        console.error('Failed to load file:', err);
        setError(err.response?.data?.detail || 'Failed to load file');
      } finally {
        setIsLoading(false);
      }
    };

    fetchFile();

    // Cleanup function
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [isOpen, file?.id]); // Only re-fetch when these change

  // Handle download
  const handleDownload = () => {
    if (!blobUrl || !file) return;
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = file.original_filename || 'download';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // Close on escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !file) return null;

  const fileType = getFileType(file.mime_type);

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <Card className="w-full max-w-5xl max-h-[90vh] flex flex-col bg-white">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold truncate">{file.original_filename || 'Document'}</h3>
            <p className="text-sm text-muted-foreground">
              {file.document_type.replace(/_/g, ' ')} - {(file.file_size / 1024).toFixed(1)} KB
            </p>
          </div>
          <div className="flex items-center gap-2 ml-4">
            <Button variant="outline" size="sm" onClick={handleDownload} disabled={!blobUrl}>
              Download
            </Button>
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 min-h-[400px] bg-gray-100">
          {isLoading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading document...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-red-600">
                <p className="font-medium mb-2">Failed to load document</p>
                <p className="text-sm">{error}</p>
                <Button variant="outline" size="sm" className="mt-4" onClick={onClose}>
                  Close
                </Button>
              </div>
            </div>
          )}

          {!isLoading && !error && blobUrl && fileType === 'pdf' && (
            <iframe
              src={blobUrl}
              className="w-full h-full min-h-[600px] rounded border"
              title={file.original_filename || 'PDF Document'}
            />
          )}

          {!isLoading && !error && blobUrl && fileType === 'image' && (
            <div className="flex items-center justify-center h-full">
              <img
                src={blobUrl}
                alt={file.original_filename || 'Document'}
                className="max-w-full max-h-[70vh] object-contain rounded shadow-lg"
              />
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
