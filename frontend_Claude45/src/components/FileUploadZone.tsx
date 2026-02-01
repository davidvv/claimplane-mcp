/**
 * Drag-and-drop file upload component
 *
 * Workflow v2: When claimId is provided, files are uploaded
 * immediately as the user selects them (progressive upload).
 */

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { cn, formatFileSize } from '@/lib/utils';
import { Button } from './ui/Button';
import { uploadDocument } from '@/services/documents';
import type { DocumentType } from '@/types/api';

export interface UploadedFile {
  file?: File | null;  // Optional for already-uploaded documents (restored from server)
  name?: string;  // Fallback name when file object is not available
  documentType: DocumentType;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress?: number;
  error?: string;
  uploadedId?: string;  // Server-side file ID after successful upload
  alreadyUploaded?: boolean;  // True for documents restored from server (no need to re-upload)
}

interface FileUploadZoneProps {
  onFilesChange: (files: UploadedFile[]) => void;
  maxFiles?: number;
  maxSizeMB?: number;
  claimId?: string;  // Workflow v2: If provided, upload files immediately
  initialFiles?: UploadedFile[];  // Pre-populate with existing files (e.g., boarding pass from OCR)
}

const ALLOWED_TYPES = {
  'application/pdf': ['.pdf'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function FileUploadZone({
  onFilesChange,
  maxFiles = 5,
  maxSizeMB = 10,
  claimId,
  initialFiles,
}: FileUploadZoneProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>(initialFiles || []);

  // Progressive upload function for Workflow v2
  const uploadFileToServer = async (
    fileEntry: UploadedFile,
    index: number,
    // currentFiles argument removed as we rely on state setter
  ) => {
    if (!claimId) return;
    
    // Skip files that are already uploaded to server (e.g., restored from magic link)
    if (fileEntry.alreadyUploaded || !fileEntry.file) return;

    // Update status to uploading
    setUploadedFiles((prevFiles) => {
      const newFiles = [...prevFiles];
      // Find the file by index (index in prevFiles might match index passed if no reordering happened)
      // Since we append new files, index should be stable for the batch
      if (newFiles[index]) {
        newFiles[index] = { ...newFiles[index], status: 'uploading', progress: 0 };
        onFilesChange(newFiles);
      }
      return newFiles;
    });

    try {
      const result = await uploadDocument(
        claimId,
        fileEntry.file!,  // We already checked that file exists above
        fileEntry.documentType,
        (progressEvent: any) => {
          // Calculate upload percentage
          const rawProgress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
          
          // Cap visual progress at 95% during upload/processing phase
          // This prevents the "stuck at 100%" issue while server encrypts/moves files
          const visualProgress = Math.min(rawProgress, 95);
          
          setUploadedFiles((prevFiles) => {
            const newFiles = [...prevFiles];
            if (newFiles[index]) {
              newFiles[index] = { ...newFiles[index], progress: visualProgress };
            }
            return newFiles;
          });
        }
      );

      // Update status to success (100%)
      setUploadedFiles((prevFiles) => {
        const newFiles = [...prevFiles];
        if (newFiles[index]) {
          newFiles[index] = {
            ...newFiles[index],
            status: 'success',
            progress: 100,
            uploadedId: result.id,
            alreadyUploaded: true, // Mark as already uploaded to prevent redundant attempts in Step 5
          };
          onFilesChange(newFiles);
        }
        return newFiles;
      });
      console.log(`File uploaded successfully: ${fileEntry.file.name}`);

    } catch (error: any) {
      console.error(`Failed to upload ${fileEntry.file.name}:`, error);

      // Update status to error
      setUploadedFiles((prevFiles) => {
        const newFiles = [...prevFiles];
        if (newFiles[index]) {
          newFiles[index] = {
            ...newFiles[index],
            status: 'error',
            error: error.message || 'Upload failed',
          };
          onFilesChange(newFiles);
        }
        return newFiles;
      });
      toast.error(`Failed to upload ${fileEntry.file.name}`);
    }
  };

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
        file,
        name: file.name,  // Store name separately for sessionStorage persistence (Bug #292)
        documentType: getDocumentType(file.name),
        status: claimId ? 'pending' : 'pending',  // Will be uploaded if claimId exists
      }));

      // Calculate the starting index for new files in the updated array
      // This index will be used for state updates during async upload
      // let startIndex = 0;

      setUploadedFiles((prevFiles) => {
        const updatedFiles = [...prevFiles, ...newFiles].slice(0, maxFiles);
        // startIndex = prevFiles.length; // Correct index for appended files
        onFilesChange(updatedFiles);
        return updatedFiles;
      });

      // Progressive upload if claimId is provided
      if (claimId) {
        // We use the startIndex captured from the state update context
        // This assumes state update is synchronous enough for this logic, 
        // or effectively we know the index is `uploadedFiles.length` (from before set)
        // Actually, better to calculate startIndex from current `uploadedFiles.length` OUTSIDE
        // but `uploadedFiles` in dependency array changes... 
        
        // Wait, onDrop closes over `uploadedFiles`.
        // So startIndex = uploadedFiles.length.
        const currentCount = uploadedFiles.length;
        
        for (let i = 0; i < newFiles.length && currentCount + i < maxFiles; i++) {
          // Pass the file object directly, not from state array, to avoid stale state issues in loop
          await uploadFileToServer(newFiles[i], currentCount + i);
        }
      }
    },
    [uploadedFiles, maxFiles, onFilesChange, claimId]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: ALLOWED_TYPES,
    maxSize: MAX_FILE_SIZE,
    maxFiles: maxFiles - uploadedFiles.length,
    disabled: uploadedFiles.length >= maxFiles,
  });

  const removeFile = (index: number) => {
    const updatedFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(updatedFiles);
    onFilesChange(updatedFiles);
  };

  const updateDocumentType = (index: number, documentType: DocumentType) => {
    const updatedFiles = [...uploadedFiles];
    updatedFiles[index].documentType = documentType;
    setUploadedFiles(updatedFiles);
    onFilesChange(updatedFiles);
  };

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-gray-300 dark:border-gray-700 hover:border-primary',
          uploadedFiles.length >= maxFiles &&
            'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />

        {isDragActive ? (
          <p className="text-lg font-medium text-primary">Drop files here...</p>
        ) : (
          <>
            <p className="text-lg font-medium mb-2">
              {uploadedFiles.length >= maxFiles
                ? `Maximum ${maxFiles} files reached`
                : 'Drag & drop files here'}
            </p>
            <p className="text-sm text-muted-foreground mb-4">
              or click to browse
            </p>
            <p className="text-xs text-muted-foreground">
              Accepted: PDF, JPG, PNG (max {maxSizeMB}MB each)
            </p>
          </>
        )}
      </div>

      {/* File rejections */}
      {fileRejections.length > 0 && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-sm text-destructive">
                Some files were rejected:
              </p>
              <ul className="text-sm text-destructive/80 mt-1 space-y-1">
                {fileRejections.map(({ file, errors }) => (
                  <li key={file.name}>
                    {file.name}: {errors.map((e) => e.message).join(', ')}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Uploaded files list */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm font-medium">
            Uploaded files ({uploadedFiles.length}/{maxFiles})
          </p>
          {uploadedFiles.map((uploadedFile, index) => (
            <div
              key={index}
              className="p-3 border rounded-lg bg-card space-y-2"
            >
              {/* Top row: File icon, name, size, status, remove button */}
              <div className="flex items-center gap-3">
                <File className="w-5 h-5 text-muted-foreground shrink-0" />

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {uploadedFile.file?.name || uploadedFile.name || 'Uploaded document'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {uploadedFile.file ? formatFileSize(uploadedFile.file.size) : (uploadedFile.alreadyUploaded ? 'Already uploaded' : '')}
                  </p>
                </div>

                {/* Status indicator */}
                {uploadedFile.status === 'uploading' && (
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-5 h-5 text-primary animate-spin" />
                    <span className="text-xs text-muted-foreground">
                      {uploadedFile.progress || 0}%
                    </span>
                  </div>
                )}
                {uploadedFile.status === 'success' && (
                  <CheckCircle className="w-5 h-5 text-green-600 shrink-0" />
                )}
                {uploadedFile.status === 'error' && (
                  <AlertCircle className="w-5 h-5 text-destructive shrink-0" />
                )}

                {/* Remove button */}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeFile(index)}
                  className="shrink-0"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {/* Bottom row: Document type selector (full width on mobile) */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground whitespace-nowrap">Document type:</span>
                <select
                  value={uploadedFile.documentType}
                  onChange={(e) =>
                    updateDocumentType(index, e.target.value as DocumentType)
                  }
                  className="flex-1 text-sm border rounded px-2 py-1.5 bg-background"
                >
                  <option value="boarding_pass">Boarding Pass</option>
                  <option value="id_document">ID Document</option>
                  <option value="receipt">Receipt</option>
                  <option value="bank_statement">Bank Statement</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Error message if any */}
              {uploadedFile.status === 'error' && uploadedFile.error && (
                <p className="text-xs text-destructive">{uploadedFile.error}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Guess document type from filename
 */
function getDocumentType(filename: string): DocumentType {
  const lower = filename.toLowerCase();

  if (lower.includes('boarding') || lower.includes('pass')) {
    return 'boarding_pass';
  }
  if (lower.includes('id') || lower.includes('passport') || lower.includes('license')) {
    return 'id_document';
  }
  if (lower.includes('receipt')) {
    return 'receipt';
  }
  if (lower.includes('bank') || lower.includes('statement')) {
    return 'bank_statement';
  }

  return 'other';
}
