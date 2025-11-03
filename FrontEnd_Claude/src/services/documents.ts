/**
 * Documents service - API calls for document operations
 */
import api, { unwrapApiResponse, trackEvent } from './api';
import type { Document, DocumentType, ApiResponse } from '@/types/openapi';

export const documentService = {
  /**
   * List documents for a claim
   */
  async listDocuments(claimId: string): Promise<Document[]> {
    const response = await api.get<ApiResponse<Document[]>>(
      `/claims/${claimId}/documents`
    );
    return unwrapApiResponse(response.data);
  },

  /**
   * Upload document for a claim
   */
  async uploadDocument(
    claimId: string,
    file: File,
    documentType: DocumentType,
    onProgress?: (progress: number) => void
  ): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('documentType', documentType);

    const response = await api.post<ApiResponse<Document>>(
      `/claims/${claimId}/documents`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percentCompleted);
          }
        },
      }
    );

    const document = unwrapApiResponse(response.data);

    trackEvent('document_uploaded', {
      claimId,
      documentType,
      fileSize: file.size,
      fileName: file.name,
    });

    return document;
  },

  /**
   * Download document
   */
  async downloadDocument(documentId: string): Promise<Blob> {
    const response = await api.get<Blob>(`/documents/${documentId}`, {
      responseType: 'blob',
    });

    trackEvent('document_downloaded', {
      documentId,
    });

    return response.data;
  },

  /**
   * Delete document (admin only)
   */
  async deleteDocument(documentId: string): Promise<void> {
    await api.delete(`/documents/${documentId}`);

    trackEvent('document_deleted', {
      documentId,
    });
  },

  /**
   * Helper to trigger browser download
   */
  triggerDownload(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
};
