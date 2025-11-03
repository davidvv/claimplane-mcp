/**
 * Drag-and-drop file upload component
 */

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';
import { cn, formatFileSize } from '@/lib/utils';
import { Button } from './ui/Button';
import type { DocumentType } from '@/types/api';

interface UploadedFile {
  file: File;
  documentType: DocumentType;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress?: number;
  error?: string;
}

interface FileUploadZoneProps {
  onFilesChange: (files: UploadedFile[]) => void;
  maxFiles?: number;
  maxSizeMB?: number;
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
}: FileUploadZoneProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
        file,
        documentType: getDocumentType(file.name),
        status: 'pending',
      }));

      const updatedFiles = [...uploadedFiles, ...newFiles].slice(0, maxFiles);
      setUploadedFiles(updatedFiles);
      onFilesChange(updatedFiles);
    },
    [uploadedFiles, maxFiles, onFilesChange]
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
