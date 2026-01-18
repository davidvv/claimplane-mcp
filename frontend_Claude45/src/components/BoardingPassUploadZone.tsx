/**
 * BoardingPassUploadZone Component
 * 
 * Drag-and-drop zone for boarding pass uploads with OCR processing.
 * Features:
 * - Visual drag-and-drop feedback
 * - File type validation (JPEG, PNG, PDF)
 * - File size validation (max 10MB)
 * - Image preview
 * - Loading state with progress
 * - Error handling with retry
 */

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, AlertCircle, Loader2, Mail } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
// import type { OCRResponse } from '@/types/api';

interface BoardingPassUploadZoneProps {
  // onOCRSuccess: (result: OCRResponse, file: File) => void;
  // onOCRError?: (error: Error) => void;
  onFileSelect?: (file: File) => void;
  disabled?: boolean;
  isProcessing?: boolean;  // External processing state from parent
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ACCEPTED_FILE_TYPES = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'application/pdf': ['.pdf'],
  'message/rfc822': ['.eml'],
};

export function BoardingPassUploadZone({
  // onOCRSuccess,
  // onOCRError,
  onFileSelect,
  disabled = false,
  isProcessing: externalProcessing = false,
}: BoardingPassUploadZoneProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLocalProcessing, setIsLocalProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Combine local and external processing states
  const isProcessing = isLocalProcessing || externalProcessing;

  const processFile = useCallback(
    async (file: File) => {
      setError(null);
      setIsLocalProcessing(true);

      // Generate preview for images
      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } else {
        // No preview for PDFs or EMLs
        setPreviewUrl(null);
      }

      // Notify parent that file was selected
      onFileSelect?.(file);

      // Note: OCR processing will be triggered by parent component
      // This component only handles the upload UI
      setIsLocalProcessing(false);
    },
    [onFileSelect]
  );

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      if (disabled) return;

      // Handle rejected files
      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0];
        if (rejection.errors?.[0]?.code === 'file-too-large') {
          const errorMsg = 'File is too large. Maximum size is 10MB.';
          setError(errorMsg);
          toast.error(errorMsg);
        } else if (rejection.errors?.[0]?.code === 'file-invalid-type') {
          const errorMsg = 'Invalid file type. Please upload a JPG, PNG, PDF, or EML (Email).';
          setError(errorMsg);
          toast.error(errorMsg);
        } else {
          const errorMsg = 'File upload failed. Please try again.';
          setError(errorMsg);
          toast.error(errorMsg);
        }
        return;
      }

      // Handle accepted files
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        setSelectedFile(file);
        processFile(file);
      }
    },
    [disabled, processFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    disabled: disabled || isProcessing,
  });

  const handleClearFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setError(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
  };

  return (
    <div className="space-y-4">
      {/* Upload Zone */}
      {!selectedFile && (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
            ${
              isDragActive
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
            }
            ${disabled || isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
            ${error ? 'border-red-500 bg-red-50 dark:bg-red-950/20' : ''}
          `}
        >
          <input {...getInputProps()} />

          <div className="flex flex-col items-center gap-3 sm:gap-4">
            <div className="rounded-full bg-blue-100 dark:bg-blue-900 p-4">
              {isProcessing ? (
                <Loader2 className="w-8 h-8 text-blue-600 dark:text-blue-400 animate-spin" />
              ) : (
                <Upload className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              )}
            </div>

            <div>
              <p className="text-lg font-semibold mb-1">
                {isDragActive
                  ? 'Drop your boarding pass or email here'
                  : 'Drop your boarding pass or email here'}
              </p>
              <p className="text-sm text-muted-foreground mb-2">
                or click to browse files
              </p>
              <p className="text-xs text-muted-foreground">
                Supports: JPG, PNG, PDF, EML • Max size: 10MB
              </p>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <AlertCircle className="w-4 h-4" />
                <span className="text-sm">{error}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* File Preview */}
      {selectedFile && (
        <Card className="p-4">
          <div className="flex items-start gap-4">
            {/* Preview Image or PDF Icon */}
            <div className="flex-shrink-0 relative">
              {previewUrl ? (
                <div className="relative">
                  <img
                    src={previewUrl}
                    alt="Boarding pass preview"
                    className="w-24 h-24 object-cover rounded border border-gray-200 dark:border-gray-700"
                  />
                  {/* Scanning animation overlay */}
                  {isProcessing && (
                    <div className="absolute inset-0 bg-blue-500/10 rounded overflow-hidden">
                      <div className="absolute inset-0 animate-scan">
                        <div className="h-1 bg-blue-500 shadow-lg shadow-blue-500/50" />
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="w-24 h-24 flex items-center justify-center bg-gray-100 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                  {selectedFile.name.toLowerCase().endsWith('.eml') ? (
                    <Mail className="w-12 h-12 text-gray-400" />
                  ) : (
                    <FileText className="w-12 h-12 text-gray-400" />
                  )}
                </div>
              )}
            </div>

            {/* File Info */}
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{selectedFile.name}</p>
              <p className="text-sm text-muted-foreground">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
              {isProcessing && (
                <div className="mt-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                    <span className="text-sm font-medium text-blue-600">
                      Extracting flight details...
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div className="h-full bg-blue-600 rounded-full animate-pulse" style={{ width: '75%' }} />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    AI is reading your boarding pass. This usually takes 3-5 seconds.
                  </p>
                </div>
              )}
            </div>

            {/* Clear Button */}
            {!isProcessing && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleClearFile}
                className="flex-shrink-0"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
