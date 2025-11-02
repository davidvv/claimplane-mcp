import { get, post, del, uploadFile } from './api';
import { Document, DocumentUploadFormData } from '../types/openapi';

/**
 * List documents for a claim
 * @param claimId - Claim ID
 * @returns List of documents
 */
export async function listDocuments(claimId: string): Promise<Document[]> {
  return get<Document[]>(`/claims/${claimId}/documents`);
}

/**
 * Upload document for a claim
 * @param claimId - Claim ID
 * @param formData - Document upload form data
 * @param onProgress - Progress callback
 * @returns Uploaded document
 */
export async function uploadDocument(
  claimId: string,
  formData: DocumentUploadFormData,
  onProgress?: (progress: number) => void
): Promise<Document> {
  return uploadFile<Document>(
    `/claims/${claimId}/documents`,
    formData.file,
    formData.documentType,
    onProgress
  );
}

/**
 * Download document
 * @param documentId - Document ID
 * @returns Document blob
 */
export async function downloadDocument(documentId: string): Promise<Blob> {
  const response = await get(`/documents/${documentId}`, {
    responseType: 'blob',
  });
  return response as unknown as Blob;
}

/**
 * Delete document
 * @param documentId - Document ID
 */
export async function deleteDocument(documentId: string): Promise<void> {
  return del<void>(`/documents/${documentId}`);
}

/**
 * Get mock documents (for development)
 * @param claimId - Claim ID
 * @returns Mock documents
 */
export function getMockDocuments(claimId: string): Document[] {
  const now = new Date().toISOString();
  
  return [
    {
      id: 'doc1',
      filename: 'boarding_pass_lh1234.pdf',
      contentType: 'application/pdf',
      size: 2048576,
      documentType: 'boarding_pass',
      uploadedAt: now,
      url: `https://example.com/claims/${claimId}/documents/boarding_pass_lh1234.pdf`,
    },
    {
      id: 'doc2',
      filename: 'passport_john_doe.jpg',
      contentType: 'image/jpeg',
      size: 1024000,
      documentType: 'id_document',
      uploadedAt: now,
      url: `https://example.com/claims/${claimId}/documents/passport_john_doe.jpg`,
    },
    {
      id: 'doc3',
      filename: 'hotel_receipt.pdf',
      contentType: 'application/pdf',
      size: 512000,
      documentType: 'receipt',
      uploadedAt: now,
      url: `https://example.com/claims/${claimId}/documents/hotel_receipt.pdf`,
    },
  ];
}

/**
 * Validate file before upload
 * @param file - File to validate
 * @returns Validation result
 */
export function validateFile(file: File): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  const maxSize = 10 * 1024 * 1024; // 10MB
  const allowedTypes = [
    'application/pdf',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ];
  
  // Check file size
  if (file.size > maxSize) {
    errors.push('File size must be 10MB or less');
  }
  
  // Check file type
  if (!allowedTypes.includes(file.type)) {
    errors.push('Only PDF, JPG, PNG, GIF, and Word documents are allowed');
  }
  
  // Check filename length
  if (file.name.length > 255) {
    errors.push('Filename must be 255 characters or less');
  }
  
  // Check for suspicious file extensions
  const suspiciousExtensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs'];
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
  if (suspiciousExtensions.includes(fileExtension)) {
    errors.push('Executable files are not allowed');
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Get file icon based on content type
 * @param contentType - File content type
 * @returns Icon component or emoji
 */
export function getFileIcon(contentType: string): string {
  if (contentType.includes('pdf')) return '📄';
  if (contentType.includes('image')) return '🖼️';
  if (contentType.includes('word')) return '📝';
  if (contentType.includes('excel')) return '📊';
  if (contentType.includes('powerpoint')) return '📽️';
  if (contentType.includes('text')) return '📃';
  return '📎';
}

/**
 * Format file size
 * @param bytes - File size in bytes
 * @returns Formatted file size
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Get document type label
 * @param documentType - Document type
 * @returns Human-readable label
 */
export function getDocumentTypeLabel(documentType: string): string {
  const labels = {
    boarding_pass: 'Boarding Pass',
    id_document: 'ID Document',
    receipt: 'Receipt',
    bank_statement: 'Bank Statement',
    other: 'Other Document',
  };
  
  return labels[documentType as keyof typeof labels] || 'Document';
}

/**
 * Generate secure filename
 * @param originalName - Original filename
 * @param prefix - Optional prefix
 * @returns Secure filename
 */
export function generateSecureFilename(originalName: string, prefix?: string): string {
  const timestamp = Date.now();
  const randomString = Math.random().toString(36).substring(2, 15);
  const extension = originalName.substring(originalName.lastIndexOf('.'));
  const baseName = originalName.substring(0, originalName.lastIndexOf('.'));
  
  // Sanitize filename
  const sanitizedBaseName = baseName
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '');
  
  const prefixStr = prefix ? `${prefix}_` : '';
  return `${prefixStr}${sanitizedBaseName}_${timestamp}_${randomString}${extension}`;
}

/**
 * Create document preview URL
 * @param file - File object
 * @returns Preview URL
 */
export function createPreviewUrl(file: File): string {
  return URL.createObjectURL(file);
}

/**
 * Revoke preview URL
 * @param url - Preview URL to revoke
 */
export function revokePreviewUrl(url: string): void {
  URL.revokeObjectURL(url);
}