/**
 * Axios instance with interceptors and error handling
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { toast } from 'sonner';
import type { ApiResponse, ErrorResponse } from '@/types/openapi';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.easyairclaim.com/v1';
const API_KEY = import.meta.env.VITE_API_KEY || '';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
});

// Request interceptor - Add auth token if available
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors globally
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ErrorResponse>) => {
    if (error.response) {
      const { status, data } = error.response;

      // Handle specific error codes
      switch (status) {
        case 400:
          toast.error(data?.error?.message || 'Invalid request. Please check your input.');
          break;
        case 401:
          toast.error('Authentication required. Please log in.');
          localStorage.removeItem('auth_token');
          window.location.href = '/auth';
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

      // Log details for debugging (dev only)
      if (import.meta.env.DEV) {
        console.error('API Error:', {
          status,
          message: data?.error?.message,
          details: data?.error?.details,
          endpoint: error.config?.url,
        });
      }
    } else if (error.request) {
      toast.error('Network error. Please check your connection.');
      console.error('Network Error:', error.message);
    } else {
      toast.error('Request failed. Please try again.');
      console.error('Request Error:', error.message);
    }

    return Promise.reject(error);
  }
);

// Helper to unwrap API responses
export function unwrapApiResponse<T>(response: ApiResponse<T>): T {
  if (!response.success) {
    throw new Error('API returned unsuccessful response');
  }
  if (!response.data) {
    throw new Error('API response missing data');
  }
  return response.data;
}

// Analytics helper
export function trackEvent(eventName: string, properties?: Record<string, unknown>) {
  if (import.meta.env.VITE_ANALYTICS_ENABLED === 'true') {
    // Stub for analytics integration
    if (window.analytics) {
      window.analytics.track(eventName, properties);
    }
    console.log('Analytics Event:', eventName, properties);
  }
}

// Extend Window interface for analytics
declare global {
  interface Window {
    analytics?: {
      track: (event: string, properties?: Record<string, unknown>) => void;
    };
  }
}

export default api;
