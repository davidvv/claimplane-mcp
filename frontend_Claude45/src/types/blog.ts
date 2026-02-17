/**
 * Blog System TypeScript Types
 * Type definitions for blog API responses and data structures
 */

// ==================== Blog Author Types ====================

export interface BlogAuthor {
  id: string; // UUID
  name: string;
  bio?: string | null;
  avatar_url?: string | null;
  social_links?: Record<string, string> | null;
  email?: string | null;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface BlogAuthorCreate {
  name: string;
  bio?: string | null;
  avatar_url?: string | null;
  social_links?: Record<string, string> | null;
  email?: string | null;
}

export interface BlogAuthorUpdate {
  name?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  social_links?: Record<string, string> | null;
  email?: string | null;
}

// ==================== Blog Category Types ====================

export interface BlogCategory {
  id: string; // UUID
  slug: string;
  name: string;
  description?: string | null;
  parent_id?: string | null; // UUID
  sort_order: number;
  post_count?: number;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface BlogCategoryCreate {
  slug: string;
  name: string;
  description?: string | null;
  parent_id?: string | null;
  sort_order?: number;
}

export interface BlogCategoryUpdate {
  slug?: string | null;
  name?: string | null;
  description?: string | null;
  parent_id?: string | null;
  sort_order?: number | null;
}

// ==================== Blog Tag Types ====================

export interface BlogTag {
  id: string; // UUID
  slug: string;
  name: string;
  post_count?: number;
  created_at: string; // ISO datetime
}

export interface BlogTagCreate {
  slug: string;
  name: string;
}

export interface BlogTagUpdate {
  slug?: string | null;
  name?: string | null;
}

// ==================== Pagination Types ====================

export interface BlogPaginationMeta {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// ==================== Blog Post Types ====================

export type BlogPostStatus = 'draft' | 'published' | 'archived';
export type BlogPostLanguage = 'en' | 'de' | 'fr';

/**
 * Summary of a blog post (used in lists)
 */
export interface BlogPostSummary {
  id: string; // UUID
  slug: string;
  language: BlogPostLanguage;
  title: string;
  excerpt?: string | null;
  featured_image_url?: string | null;
  status: BlogPostStatus;
  published_at?: string | null; // ISO datetime
  view_count: number;
  reading_time_minutes?: number | null;
  author?: BlogAuthor | null;
  categories: BlogCategory[];
  created_at: string; // ISO datetime
}

/**
 * Complete blog post with full content
 */
export interface BlogPost extends BlogPostSummary {
  content?: string | null; // Markdown content
  content_html?: string | null; // Pre-rendered HTML
  tags: BlogTag[];
  updated_at: string; // ISO datetime
}

export interface BlogPostCreate {
  slug: string;
  language?: BlogPostLanguage;
  canonical_slug?: string | null;
  title: string;
  excerpt?: string | null;
  featured_image_url?: string | null;
  content?: string | null;
  meta_title?: string | null;
  meta_description?: string | null;
  status?: BlogPostStatus;
  author_id: string; // UUID
  category_ids?: string[];
  tag_ids?: string[];
  published_at?: string | null;
  reading_time_minutes?: number | null;
}

export interface BlogPostUpdate {
  slug?: string | null;
  language?: BlogPostLanguage;
  canonical_slug?: string | null;
  title?: string | null;
  excerpt?: string | null;
  featured_image_url?: string | null;
  content?: string | null;
  meta_title?: string | null;
  meta_description?: string | null;
  status?: BlogPostStatus;
  author_id?: string | null;
  category_ids?: string[] | null;
  tag_ids?: string[] | null;
  published_at?: string | null;
  reading_time_minutes?: number | null;
}

// ==================== API Response Types ====================

/**
 * Paginated response for blog posts
 */
export interface BlogPostsResponse {
  data: BlogPostSummary[];
  pagination: BlogPaginationMeta;
}

/**
 * Response for related posts
 */
export interface BlogRelatedPostsResponse {
  data: BlogPostSummary[];
}

/**
 * Response for blog search results
 */
export interface BlogSearchResponse {
  data: BlogPostSummary[];
  pagination: BlogPaginationMeta;
  query: string;
}

/**
 * Response for list of categories
 */
export interface BlogCategoriesResponse {
  data: BlogCategory[];
}

/**
 * Response for list of tags
 */
export interface BlogTagsResponse {
  data: BlogTag[];
}

/**
 * Response for list of authors
 */
export interface BlogAuthorsResponse {
  data: BlogAuthor[];
}

// ==================== SEO Types ====================

export interface BlogSitemapEntry {
  loc: string;
  lastmod?: string | null;
  changefreq: string;
  priority: number;
}

export interface BlogSitemap {
  posts: BlogSitemapEntry[];
  categories: BlogSitemapEntry[];
  tags: BlogSitemapEntry[];
}

export interface BlogRSSEntry {
  title: string;
  link: string;
  description: string;
  pub_date: string;
  guid: string;
  author?: string | null;
}

export interface BlogRSS {
  title: string;
  link: string;
  description: string;
  last_build_date: string;
  items: BlogRSSEntry[];
}

// ==================== Admin Types ====================

export interface BlogDashboardStats {
  total_posts: number;
  published_posts: number;
  draft_posts: number;
  archived_posts: number;
  total_views: number;
  recent_posts: BlogPostSummary[];
}

export interface BlogPublishRequest {
  published_at?: string | null;
}

export interface BlogDuplicateRequest {
  new_slug?: string | null;
  new_language?: BlogPostLanguage;
}

// ==================== Re-export common types ====================

// Re-export the pagination type from api.ts for consistency
import type { PaginatedResponse } from './api';
export type { PaginatedResponse };
