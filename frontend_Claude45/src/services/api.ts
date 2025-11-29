/**
 * Axios instance and interceptors for API communication
 * Handles authentication, error handling, and request/response transformation
 */

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { toast } from 'sonner';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add API key to all requests
    if (API_KEY) {
      config.headers['X-API-Key'] = API_KEY;
    }

    // Add JWT token if available (from localStorage)
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Enhanced debugging for status page issues
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
      console.log('Headers:', config.headers);
      console.log('Token present:', !!token);
      if (token) {
        // Decode JWT token for debugging (without verification)
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          console.log('Token payload:', payload);
        } catch (e) {
          console.log('Could not decode token');
        }
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    // Log response in development
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.url}`, response.data);
    }
    return response;
  },
  (error: AxiosError) => {
    // Handle different error scenarios
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as any;

      switch (status) {
        case 400:
          toast.error(data?.error?.message || 'Invalid request. Please check your input.');
          break;
        case 401:
          toast.error('Unauthorized. Please log in.');
          // Clear token and redirect to login
          localStorage.removeItem('auth_token');
          if (window.location.pathname !== '/auth') {
            window.location.href = '/auth';
          }
          break;
        case 403:
          toast.error('Access denied. You do not have permission.');
          break;
        case 404:
          toast.error(data?.error?.message || 'Resource not found.');
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
          toast.error(data?.error?.message || 'An unexpected error occurred.');
      }

      // Log error in development
      if (import.meta.env.DEV) {
        console.error(`[API Error] ${status}`, data);
      }
    } else if (error.request) {
      // Request was made but no response received
      toast.error('Network error. Please check your connection.');
      console.error('[API Error] No response received', error.request);
    } else {
      // Something else happened
      toast.error('An unexpected error occurred.');
      console.error('[API Error]', error.message);
    }

    return Promise.reject(error);
  }
);

// Helper function to handle file uploads
export const createFormData = (data: Record<string, any>): FormData => {
  const formData = new FormData();

  Object.entries(data).forEach(([key, value]) => {
    if (value instanceof File) {
      formData.append(key, value);
    } else if (value !== undefined && value !== null) {
      formData.append(key, String(value));
    }
  });

  return formData;
};

export default apiClient;
