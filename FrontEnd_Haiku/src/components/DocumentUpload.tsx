import React, { useState, useCallback } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';

export interface DocumentUploadProps {
  onUpload: (files: File[]) => void;
  acceptedFormats?: string[];
  maxSize?: number;
  maxFiles?: number;
  className?: string;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onUpload,
  acceptedFormats = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'],
  maxSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 5,
  className = '',
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const [errors, setErrors] = useState<string[]>([]);

  const onDrop = useCallback((acceptedFiles: File[], fileRejections: FileRejection[]) => {
    // Clear previous errors
    setErrors([]);

    // Process file rejections
    if (fileRejections.length > 0) {
      const rejectionErrors = fileRejections.flatMap(rejection =>
        rejection.errors.map(error => error.message)
      );
      setErrors(rejectionErrors);
    }

    // Check file limit
    const totalFiles = files.length + acceptedFiles.length;
    if (totalFiles > maxFiles) {
      setErrors([`Maximum ${maxFiles} files allowed`]);
      return;
    }

    // Add valid files
    const newFiles = [...files, ...acceptedFiles];
    setFiles(newFiles);
    onUpload(acceptedFiles);
  }, [files, maxFiles, onUpload]);

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFormats.reduce((acc, format) => ({
      ...acc,
      [format]: [],
    }), {}),
    maxSize,
    maxFiles: maxFiles - files.length,
  });

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors duration-200
          ${isDragActive 
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' 
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          }
          ${errors.length > 0 ? 'border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/10' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center justify-center space-y-2">
          <Upload className={`h-12 w-12 ${isDragActive ? 'text-primary-600' : 'text-gray-400'}`} />
          
          {isDragActive ? (
            <p className="text-sm text-primary-600 dark:text-primary-400">Drop the files here...</p>
          ) : (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Drag & drop files here, or click to select files
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                {acceptedFormats.map(format => format.split('/')[1]).join(', ')} up to {maxSize / (1024 * 1024)}MB each
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                {files.length} of {maxFiles} files uploaded
              </p>
            </>
          )}
        </div>
      </div>

      {/* Error Messages */}
      {errors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
          <div className="flex items-start">
            <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400 mr-2 mt-0.5" />
            <div className="text-sm text-red-800 dark:text-red-200">
              {errors.map((error, index) => (
                <p key={index}>{error}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Uploaded Files List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Uploaded Files ({files.length}/{maxFiles})
          </h4>
          
          {files.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <File className="h-5 w-5 text-gray-400" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              </div>
              
              <button
                type="button"
                onClick={() => removeFile(index)}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-200"
                title="Remove file"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Success Message */}
      {files.length > 0 && errors.length === 0 && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-3">
          <div className="flex items-center">
            <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400 mr-2" />
            <p className="text-sm text-green-800 dark:text-green-200">
              Files uploaded successfully!
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;