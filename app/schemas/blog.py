"""Pydantic schemas for blog system.

This module defines all Pydantic models for blog-related API requests and responses.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Blog Author Schemas
# ============================================================================


class BlogAuthorBase(BaseModel):
    """Base schema for blog authors."""
    name: str = Field(..., min_length=1, max_length=255)
    bio: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=500)
    social_links: Optional[dict] = None
    email: Optional[str] = Field(None, max_length=255)


class BlogAuthorCreate(BlogAuthorBase):
    """Schema for creating a new blog author."""
    pass


class BlogAuthorUpdate(BaseModel):
    """Schema for updating a blog author."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    bio: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=500)
    social_links: Optional[dict] = None
    email: Optional[str] = Field(None, max_length=255)


class BlogAuthorResponse(BlogAuthorBase):
    """Schema for blog author responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BlogAuthorListResponse(BaseModel):
    """Schema for list of blog authors."""
    data: List[BlogAuthorResponse]


# ============================================================================
# Blog Category Schemas
# ============================================================================


class BlogCategoryBase(BaseModel):
    """Base schema for blog categories."""
    slug: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    sort_order: int = 0


class BlogCategoryCreate(BlogCategoryBase):
    """Schema for creating a new blog category."""
    pass


class BlogCategoryUpdate(BaseModel):
    """Schema for updating a blog category."""
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    sort_order: Optional[int] = None


class BlogCategoryResponse(BlogCategoryBase):
    """Schema for blog category responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    post_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class BlogCategoryListResponse(BaseModel):
    """Schema for list of blog categories."""
    data: List[BlogCategoryResponse]


class BlogCategoryWithPosts(BlogCategoryResponse):
    """Schema for category with its posts."""
    posts: List["BlogPostSummaryResponse"] = []


# ============================================================================
# Blog Tag Schemas
# ============================================================================


class BlogTagBase(BaseModel):
    """Base schema for blog tags."""
    slug: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)


class BlogTagCreate(BlogTagBase):
    """Schema for creating a new blog tag."""
    pass


class BlogTagUpdate(BaseModel):
    """Schema for updating a blog tag."""
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class BlogTagResponse(BlogTagBase):
    """Schema for blog tag responses."""
    id: UUID
    created_at: datetime
    post_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class BlogTagListResponse(BaseModel):
    """Schema for list of blog tags."""
    data: List[BlogTagResponse]


class BlogTagWithPosts(BlogTagResponse):
    """Schema for tag with its posts."""
    posts: List["BlogPostSummaryResponse"] = []


# ============================================================================
# Pagination Schema
# ============================================================================


class PaginationMeta(BaseModel):
    """Schema for pagination metadata."""
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ============================================================================
# Blog Post Schemas
# ============================================================================


class BlogPostBase(BaseModel):
    """Base schema for blog posts."""
    slug: str = Field(..., min_length=1, max_length=255)
    language: str = Field(default="en", pattern="^(en|de|fr)$")
    canonical_slug: Optional[str] = Field(None, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    excerpt: Optional[str] = None
    featured_image_url: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None  # Markdown content
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    reading_time_minutes: Optional[int] = None


class BlogPostCreate(BlogPostBase):
    """Schema for creating a new blog post."""
    author_id: UUID
    category_ids: Optional[List[UUID]] = []
    tag_ids: Optional[List[UUID]] = []
    published_at: Optional[datetime] = None


class BlogPostUpdate(BaseModel):
    """Schema for updating a blog post."""
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    language: Optional[str] = Field(None, pattern="^(en|de|fr)$")
    canonical_slug: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    excerpt: Optional[str] = None
    featured_image_url: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")
    author_id: Optional[UUID] = None
    category_ids: Optional[List[UUID]] = None
    tag_ids: Optional[List[UUID]] = None
    published_at: Optional[datetime] = None
    reading_time_minutes: Optional[int] = None


class BlogPostResponse(BlogPostBase):
    """Schema for complete blog post responses."""
    id: UUID
    content_html: Optional[str] = None  # Pre-rendered HTML
    view_count: int
    author: Optional["BlogAuthorResponse"] = None
    categories: List["BlogCategoryResponse"] = []
    tags: List["BlogTagResponse"] = []
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Blog Post Schemas (Summary - after PaginationMeta for proper references)
# ============================================================================


class BlogPostSummaryResponse(BaseModel):
    """Schema for blog post summary (for lists)."""
    id: UUID
    slug: str
    language: str
    title: str
    excerpt: Optional[str]
    featured_image_url: Optional[str]
    status: str
    published_at: Optional[datetime]
    view_count: int
    reading_time_minutes: Optional[int]
    author: Optional["BlogAuthorResponse"] = None
    categories: List["BlogCategoryResponse"] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class BlogPostListResponse(BaseModel):
    """Schema for paginated blog post list."""
    data: List[BlogPostSummaryResponse]
    pagination: PaginationMeta


class BlogPostRelatedResponse(BaseModel):
    """Schema for related blog posts."""
    data: List[BlogPostSummaryResponse]


# ============================================================================
# Blog Search Schemas
# ============================================================================


class BlogSearchQuery(BaseModel):
    """Schema for blog search query parameters."""
    q: str = Field(..., min_length=1, max_length=200)
    language: Optional[str] = Field(None, pattern="^(en|de|fr)$")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=50)


class BlogSearchResponse(BaseModel):
    """Schema for blog search results."""
    data: List[BlogPostSummaryResponse]
    pagination: PaginationMeta
    query: str


# ============================================================================
# Blog Filter/Query Schemas
# ============================================================================


class BlogPostFilter(BaseModel):
    """Schema for filtering blog posts."""
    language: Optional[str] = Field(None, pattern="^(en|de|fr)$")
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")
    author_id: Optional[UUID] = None
    category_slug: Optional[str] = None
    tag_slug: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=50)
    sort_by: str = Field(default="published_at", pattern="^(published_at|created_at|updated_at|title|view_count)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


# ============================================================================
# SEO Schemas
# ============================================================================


class BlogSitemapEntry(BaseModel):
    """Schema for sitemap entry."""
    loc: str
    lastmod: Optional[datetime] = None
    changefreq: str = "weekly"
    priority: float = Field(default=0.5, ge=0.0, le=1.0)


class BlogSitemapResponse(BaseModel):
    """Schema for blog sitemap."""
    posts: List[BlogSitemapEntry]
    categories: List[BlogSitemapEntry]
    tags: List[BlogSitemapEntry]


class BlogRSSEntry(BaseModel):
    """Schema for RSS feed entry."""
    title: str
    link: str
    description: str
    pub_date: datetime
    guid: str
    author: Optional[str] = None


class BlogRSSResponse(BaseModel):
    """Schema for blog RSS feed."""
    title: str
    link: str
    description: str
    last_build_date: datetime
    items: List[BlogRSSEntry]


# ============================================================================
# Admin Dashboard Schemas
# ============================================================================


class BlogDashboardStats(BaseModel):
    """Schema for blog dashboard statistics."""
    total_posts: int
    published_posts: int
    draft_posts: int
    archived_posts: int
    total_views: int
    recent_posts: List[BlogPostSummaryResponse]


class BlogPublishRequest(BaseModel):
    """Schema for publishing a blog post."""
    published_at: Optional[datetime] = None


class BlogDuplicateRequest(BaseModel):
    """Schema for duplicating a blog post."""
    new_slug: Optional[str] = None
    new_language: Optional[str] = Field(None, pattern="^(en|de|fr)$")


# Resolve forward references
BlogCategoryWithPosts.model_rebuild()
BlogTagWithPosts.model_rebuild()