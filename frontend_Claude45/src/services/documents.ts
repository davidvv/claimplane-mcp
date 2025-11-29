/**
 * Document-related API service functions
 */

import apiClient, { createFormData } from './api';
import type {
  Document,
  DocumentType,
  ApiResponse,
} from '@/types/api';

/**
 * List documents for a claim
 * GET /claims/{claimId}/documents
 */
export const listClaimDocuments = async (claimId: string): Promise<Document[]> => {
  const response = await apiClient.get<ApiResponse<Document[]>>(
    `/claims/${claimId}/documents`
  );

  if (!response.data.data) {
    return [];
  }

  return response.data.data;
};

/**
 * Upload document for a claim
 * POST /claims/{claimId}/documents
 */
export const uploadDocument = async (
  claimId: string,
  file: File,
  documentType: DocumentType,
  onUploadProgress?: (progressEvent: any) => void
): Promise<Document> => {
  const formData = createFormData({
    file,
    document_type: documentType,  // Backend expects snake_case
  });

  const response = await apiClient.post<Document>(
    `/claims/${claimId}/documents`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    }
  );

  if (!response.data) {
    throw new Error('Failed to upload document');
  }

  return response.data;
};

/**
 * Download document
 * GET /documents/{documentId}
 */
export const downloadDocument = async (documentId: string): Promise<Blob> => {
  const response = await apiClient.get(`/documents/${documentId}`, {
    responseType: 'blob',
  });

  return response.data;
};

/**
 * Delete document
 * DELETE /documents/{documentId}
 */
export const deleteDocument = async (documentId: string): Promise<void> => {
  await apiClient.delete(`/documents/${documentId}`);
};
