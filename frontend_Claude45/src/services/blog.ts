/**
 * Blog API Service
 * Handles all blog-related API calls
 */
import type { BlogPost, BlogCategory, BlogTag, BlogAuthor, PaginatedResponse, BlogPostSummary } from '@/types/blog';
import apiClient from './api';

const BLOG_API_BASE = '/blog';

export const blogService = {
  // Posts
  async getPosts(params?: {
    language?: string;
    page?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: string;
  }): Promise<PaginatedResponse<BlogPostSummary>> {
    const searchParams = new URLSearchParams();
    if (params?.language) searchParams.set('language', params.language);
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.sort_by) searchParams.set('sort_by', params.sort_by);
    if (params?.sort_order) searchParams.set('sort_order', params.sort_order);
    
    const query = searchParams.toString();
    const response = await apiClient.get(`${BLOG_API_BASE}/posts${query ? `?${query}` : ''}`);
    return response.data;
  },

  async getPost(slug: string, language: string = 'en'): Promise<BlogPost> {
    const response = await apiClient.get(`${BLOG_API_BASE}/posts/${slug}?language=${language}`);
    return response.data;
  },

  async getRelatedPosts(slug: string, language: string = 'en', limit: number = 3): Promise<BlogPostSummary[]> {
    const response = await apiClient.get(`${BLOG_API_BASE}/posts/${slug}/related?language=${language}&limit=${limit}`);
    return response.data.data;
  },

  async searchPosts(query: string, params?: {
    language?: string;
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<BlogPostSummary>> {
    const searchParams = new URLSearchParams({ q: query });
    if (params?.language) searchParams.set('language', params.language);
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    
    const response = await apiClient.get(`${BLOG_API_BASE}/posts/search?${searchParams.toString()}`);
    return response.data;
  },

  // Categories
  async getCategories(): Promise<BlogCategory[]> {
    const response = await apiClient.get(`${BLOG_API_BASE}/categories`);
    return response.data.data;
  },

  async getPostsByCategory(categorySlug: string, params?: {
    language?: string;
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<BlogPostSummary>> {
    const searchParams = new URLSearchParams();
    if (params?.language) searchParams.set('language', params.language);
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    
    const query = searchParams.toString();
    const response = await apiClient.get(`${BLOG_API_BASE}/categories/${categorySlug}/posts${query ? `?${query}` : ''}`);
    return response.data;
  },

  // Tags
  async getTags(): Promise<BlogTag[]> {
    const response = await apiClient.get(`${BLOG_API_BASE}/tags`);
    return response.data.data;
  },

  async getPostsByTag(tagSlug: string, params?: {
    language?: string;
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<BlogPostSummary>> {
    const searchParams = new URLSearchParams();
    if (params?.language) searchParams.set('language', params.language);
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    
    const query = searchParams.toString();
    const response = await apiClient.get(`${BLOG_API_BASE}/tags/${tagSlug}/posts${query ? `?${query}` : ''}`);
    return response.data;
  },

  // Authors
  async getAuthors(): Promise<BlogAuthor[]> {
    const response = await apiClient.get(`${BLOG_API_BASE}/authors`);
    return response.data.data;
  },

  async getPostsByAuthor(authorId: string, params?: {
    language?: string;
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<BlogPostSummary>> {
    const searchParams = new URLSearchParams();
    if (params?.language) searchParams.set('language', params.language);
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    
    const query = searchParams.toString();
    const response = await apiClient.get(`${BLOG_API_BASE}/authors/${authorId}/posts${query ? `?${query}` : ''}`);
    return response.data;
  },
};