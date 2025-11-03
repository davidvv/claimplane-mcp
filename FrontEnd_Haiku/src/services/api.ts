import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { toast } from 'sonner';
import { ErrorResponse } from '../schemas';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.easyairclaim.com/v1';
const API_KEY = import.meta.env.VITE_API_KEY || '';
const MOCK_JWT = import.meta.env.VITE_MOCK_JWT;

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add JWT token if available
    const token = localStorage.getItem('jwt_token') || MOCK_JWT;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log request for debugging
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.params || config.data);
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Log response for debugging
    if (import.meta.env.DEV) {
      console.log(`[API] Response:`, response.data);
    }
    
    return response;
  },
  (error: AxiosError<ErrorResponse>) => {
    if (error.response) {
      const { status, data } = error.response;
      
      // Handle specific error cases
      switch (status) {
        case 400:
          if (data?.error?.details) {
            data.error.details.forEach(detail => toast.error(detail));
          } else {
            toast.error(data?.error?.message || 'Invalid request');
          }
          break;
          
        case 401:
          toast.error('Authentication required. Please log in again.');
          localStorage.removeItem('jwt_token');
          window.location.href = '/auth';
          break;
          
        case 403:
          toast.error('You do not have permission to perform this action.');
          break;
          
        case 404:
          toast.error('Resource not found.');
          break;
          
        case 429:
          toast.error('Too many requests. Please try again later.');
          break;
          
        case 500:
        case 502:
        case 503:
          toast.error('Server error. Please try again later.');
          break;
          
        default:
          toast.error(data?.error?.message || 'An unexpected error occurred');
      }
    } else if (error.request) {
      toast.error('Network error. Please check your connection.');
    } else {
      toast.error('An unexpected error occurred');
    }
    
    return Promise.reject(error);
  }
);

// Helper function to handle API responses
export function handleApiResponse<T>(response: any): T {
  if (response.data?.success === false) {
    throw new Error(response.data?.error?.message || 'API request failed');
  }
  return response.data?.data || response.data;
}

// Helper function to handle paginated responses
export function handlePaginatedResponse<T>(response: any): { data: T[]; pagination: any } {
  if (response.data?.success === false) {
    throw new Error(response.data?.error?.message || 'API request failed');
  }
  return {
    data: response.data?.data || [],
    pagination: response.data?.pagination || { page: 1, limit: 20, total: 0, hasNext: false }
  };
}

// Generic API functions
export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.get(url, config);
  return handleApiResponse<T>(response);
}

export async function post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.post(url, data, config);
  return handleApiResponse<T>(response);
}

export async function put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.put(url, data, config);
  return handleApiResponse<T>(response);
}

export async function patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.patch(url, data, config);
  return handleApiResponse<T>(response);
}

export async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.delete(url, config);
  return handleApiResponse<T>(response);
}

// File upload helper
export async function uploadFile<T>(url: string, file: File, documentType: string, onProgress?: (progress: number) => void): Promise<T> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('documentType', documentType);
  
  const config: AxiosRequestConfig = {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: onProgress ? (progressEvent) => {
      const progress = progressEvent.total ? Math.round((progressEvent.loaded * 100) / progressEvent.total) : 0;
      onProgress(progress);
    } : undefined,
  };
  
  const response = await api.post(url, formData, config);
  return handleApiResponse<T>(response);
}

// Health check
export async function healthCheck(): Promise<{ status: string; timestamp: string; version: string }> {
  return get('/health');
}

export default api;