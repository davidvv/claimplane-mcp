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

interface UploadedFile {
  file: File;
  documentType: DocumentType;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress?: number;
  error?: string;
  uploadedId?: string;  // Server-side file ID after successful upload
}

interface FileUploadZoneProps {
  onFilesChange: (files: UploadedFile[]) => void;
  maxFiles?: number;
  maxSizeMB?: number;
  claimId?: string;  // Workflow v2: If provided, upload files immediately
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
}: FileUploadZoneProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

  // Progressive upload function for Workflow v2
  const uploadFileToServer = async (
    fileEntry: UploadedFile,
    index: number,
    currentFiles: UploadedFile[]
  ) => {
    if (!claimId) return;

    // Update status to uploading
    const updatingFiles = [...currentFiles];
    updatingFiles[index] = { ...updatingFiles[index], status: 'uploading', progress: 0 };
    setUploadedFiles(updatingFiles);
    onFilesChange(updatingFiles);

    try {
      const result = await uploadDocument(
        claimId,
        fileEntry.file,
        fileEntry.documentType,
        (progressEvent: any) => {
          const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
          const progressFiles = [...currentFiles];
          progressFiles[index] = { ...progressFiles[index], progress };
          setUploadedFiles(progressFiles);
        }
      );

      // Update status to success
      const successFiles = [...currentFiles];
      successFiles[index] = {
        ...successFiles[index],
        status: 'success',
        progress: 100,
        uploadedId: result.id,
      };
      setUploadedFiles(successFiles);
      onFilesChange(successFiles);
      console.log(`File uploaded successfully: ${fileEntry.file.name}`);

    } catch (error: any) {
      console.error(`Failed to upload ${fileEntry.file.name}:`, error);

      // Update status to error
      const errorFiles = [...currentFiles];
      errorFiles[index] = {
        ...errorFiles[index],
        status: 'error',
        error: error.message || 'Upload failed',
      };
      setUploadedFiles(errorFiles);
      onFilesChange(errorFiles);
      toast.error(`Failed to upload ${fileEntry.file.name}`);
    }
  };

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
        file,
        documentType: getDocumentType(file.name),
        status: claimId ? 'pending' : 'pending',  // Will be uploaded if claimId exists
      }));

      const updatedFiles = [...uploadedFiles, ...newFiles].slice(0, maxFiles);
      setUploadedFiles(updatedFiles);
      onFilesChange(updatedFiles);

      // Progressive upload if claimId is provided
      if (claimId) {
        const startIndex = uploadedFiles.length;
        for (let i = 0; i < newFiles.length && startIndex + i < maxFiles; i++) {
          await uploadFileToServer(newFiles[i], startIndex + i, updatedFiles);
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
        <div className="space-y-2">
          <p className="text-sm font-medium">
            Uploaded files ({uploadedFiles.length}/{maxFiles})
          </p>
          {uploadedFiles.map((uploadedFile, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 border rounded-lg bg-card"
            >
              <File className="w-5 h-5 text-muted-foreground shrink-0" />

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {uploadedFile.file.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(uploadedFile.file.size)}
                </p>
              </div>

              {/* Document type selector */}
              <select
                value={uploadedFile.documentType}
                onChange={(e) =>
                  updateDocumentType(index, e.target.value as DocumentType)
                }
                className="text-sm border rounded px-2 py-1 bg-background"
              >
                <option value="boarding_pass">Boarding Pass</option>
                <option value="id_document">ID Document</option>
                <option value="receipt">Receipt</option>
                <option value="bank_statement">Bank Statement</option>
                <option value="other">Other</option>
              </select>

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
                <CheckCircle className="w-5 h-5 text-green-600" />
              )}
              {uploadedFile.status === 'error' && (
                <AlertCircle className="w-5 h-5 text-destructive" />
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
