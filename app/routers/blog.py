"""Public API router for blog system.

Provides read-only endpoints for serving blog content to the frontend.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.rate_limit import limiter
from app.services.blog_service import BlogService
from app.schemas.blog import (
    BlogPostResponse, BlogPostListResponse,
    BlogCategoryResponse, BlogCategoryListResponse,
    BlogTagResponse, BlogTagListResponse,
    BlogAuthorListResponse, BlogPostRelatedResponse,
    BlogSearchResponse, BlogSearchQuery
)

# Create router
router = APIRouter(prefix="/blog", tags=["Blog"])


# ============================================================================
# Posts
# ============================================================================

@router.get(
    "/posts",
    response_model=BlogPostListResponse,
    summary="List all published blog posts",
    description="Get paginated list of published blog posts with optional filtering"
)
@limiter.limit("60/minute")
async def list_posts(
    request: Request,
    response: Response,
    language: Optional[str] = Query(None, regex="^(en|de|fr)$", description="Filter by language"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page"),
    sort_by: str = Query("published_at", regex="^(published_at|created_at|updated_at|title|view_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of published blog posts."""
    service = BlogService(db)
    posts, pagination = await service.get_posts(
        language=language,
        status="published",
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return BlogPostListResponse(data=posts, pagination=pagination)


@router.get(
    "/posts/search",
    response_model=BlogSearchResponse,
    summary="Search blog posts",
    description="Search published blog posts by title and excerpt"
)
@limiter.limit("30/minute")
async def search_posts(
    request: Request,
    response: Response,
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    language: Optional[str] = Query(None, regex="^(en|de|fr)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search published blog posts."""
    service = BlogService(db)
    posts, pagination = await service.repository.search_posts(
        query=q,
        language=language,
        status="published",
        page=page,
        limit=limit
    )
    
    from app.schemas.blog import BlogPostSummaryResponse, BlogCategoryResponse
    
    data = [
        BlogPostSummaryResponse(
            id=p.id,
            slug=p.slug,
            language=p.language,
            title=p.title,
            excerpt=p.excerpt,
            featured_image_url=p.featured_image_url,
            status=p.status,
            published_at=p.published_at,
            view_count=p.view_count,
            reading_time_minutes=p.reading_time_minutes,
            author=p.author,
            categories=[BlogCategoryResponse.model_validate(c) for c in p.categories],
            created_at=p.created_at
        )
        for p in posts
    ]
    
    return BlogSearchResponse(data=data, pagination=pagination, query=q)


@router.get(
    "/posts/{slug}",
    response_model=BlogPostResponse,
    summary="Get a single blog post",
    description="Get complete blog post by slug and language"
)
@limiter.limit("60/minute")
async def get_post(
    request: Request,
    response: Response,
    slug: str,
    language: str = Query("en", regex="^(en|de|fr)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get a single blog post by slug."""
    service = BlogService(db)
    post = await service.get_post(slug, language, increment_views=True)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return post


@router.get(
    "/posts/{slug}/related",
    response_model=BlogPostRelatedResponse,
    summary="Get related posts",
    description="Get related blog posts based on categories"
)
@limiter.limit("60/minute")
async def get_related_posts(
    request: Request,
    response: Response,
    slug: str,
    language: str = Query("en", regex="^(en|de|fr)$"),
    limit: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Get related posts for a given blog post."""
    service = BlogService(db)
    related = await service.get_related_posts(slug, language, limit)
    return BlogPostRelatedResponse(data=related)


# ============================================================================
# Categories
# ============================================================================

@router.get(
    "/categories",
    response_model=BlogCategoryListResponse,
    summary="List all categories",
    description="Get all blog categories"
)
@limiter.limit("60/minute")
async def list_categories(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Get all blog categories."""
    service = BlogService(db)
    categories = await service.get_categories()
    return BlogCategoryListResponse(data=categories)


@router.get(
    "/categories/{slug}/posts",
    response_model=BlogPostListResponse,
    summary="Get posts by category",
    description="Get all published posts in a category"
)
@limiter.limit("60/minute")
async def get_posts_by_category(
    request: Request,
    response: Response,
    slug: str,
    language: Optional[str] = Query(None, regex="^(en|de|fr)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get posts by category slug."""
    service = BlogService(db)
    posts, total = await service.repository.get_posts_by_category(
        category_slug=slug,
        language=language,
        status="published",
        page=page,
        limit=limit
    )
    
    from app.schemas.blog import BlogPostSummaryResponse, BlogCategoryResponse, PaginationMeta
    
    total_pages = (total + limit - 1) // limit
    data = [
        BlogPostSummaryResponse(
            id=p.id,
            slug=p.slug,
            language=p.language,
            title=p.title,
            excerpt=p.excerpt,
            featured_image_url=p.featured_image_url,
            status=p.status,
            published_at=p.published_at,
            view_count=p.view_count,
            reading_time_minutes=p.reading_time_minutes,
            author=p.author,
            categories=[BlogCategoryResponse.model_validate(c) for c in p.categories],
            created_at=p.created_at
        )
        for p in posts
    ]
    
    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
    
    return BlogPostListResponse(data=data, pagination=pagination)


# ============================================================================
# Tags
# ============================================================================

@router.get(
    "/tags",
    response_model=BlogTagListResponse,
    summary="List all tags",
    description="Get all blog tags"
)
@limiter.limit("60/minute")
async def list_tags(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Get all blog tags."""
    service = BlogService(db)
    tags = await service.get_tags()
    return BlogTagListResponse(data=tags)


@router.get(
    "/tags/{slug}/posts",
    response_model=BlogPostListResponse,
    summary="Get posts by tag",
    description="Get all published posts with a tag"
)
@limiter.limit("60/minute")
async def get_posts_by_tag(
    request: Request,
    response: Response,
    slug: str,
    language: Optional[str] = Query(None, regex="^(en|de|fr)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get posts by tag slug."""
    service = BlogService(db)
    posts, total = await service.repository.get_posts_by_tag(
        tag_slug=slug,
        language=language,
        status="published",
        page=page,
        limit=limit
    )
    
    from app.schemas.blog import BlogPostSummaryResponse, BlogCategoryResponse, PaginationMeta
    
    total_pages = (total + limit - 1) // limit
    data = [
        BlogPostSummaryResponse(
            id=p.id,
            slug=p.slug,
            language=p.language,
            title=p.title,
            excerpt=p.excerpt,
            featured_image_url=p.featured_image_url,
            status=p.status,
            published_at=p.published_at,
            view_count=p.view_count,
            reading_time_minutes=p.reading_time_minutes,
            author=p.author,
            categories=[BlogCategoryResponse.model_validate(c) for c in p.categories],
            created_at=p.created_at
        )
        for p in posts
    ]
    
    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
    
    return BlogPostListResponse(data=data, pagination=pagination)


# ============================================================================
# Authors
# ============================================================================

@router.get(
    "/authors",
    response_model=BlogAuthorListResponse,
    summary="List all authors",
    description="Get all blog authors"
)
@limiter.limit("60/minute")
async def list_authors(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Get all blog authors."""
    service = BlogService(db)
    authors = await service.get_authors()
    return BlogAuthorListResponse(data=authors)


@router.get(
    "/authors/{author_id}/posts",
    response_model=BlogPostListResponse,
    summary="Get posts by author",
    description="Get all published posts by an author"
)
@limiter.limit("60/minute")
async def get_posts_by_author(
    request: Request,
    response: Response,
    author_id: str,
    language: Optional[str] = Query(None, regex="^(en|de|fr)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get posts by author ID."""
    from uuid import UUID
    service = BlogService(db)
    posts, total = await service.repository.get_posts(
        language=language,
        status="published",
        author_id=UUID(author_id),
        page=page,
        limit=limit
    )
    
    from app.schemas.blog import BlogPostSummaryResponse, BlogCategoryResponse, PaginationMeta
    
    total_pages = (total + limit - 1) // limit
    data = [
        BlogPostSummaryResponse(
            id=p.id,
            slug=p.slug,
            language=p.language,
            title=p.title,
            excerpt=p.excerpt,
            featured_image_url=p.featured_image_url,
            status=p.status,
            published_at=p.published_at,
            view_count=p.view_count,
            reading_time_minutes=p.reading_time_minutes,
            author=p.author,
            categories=[BlogCategoryResponse.model_validate(c) for c in p.categories],
            created_at=p.created_at
        )
        for p in posts
    ]
    
    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
    
    return BlogPostListResponse(data=data, pagination=pagination)


# ============================================================================
# SEO Endpoints
# ============================================================================

@router.get(
    "/sitemap.xml",
    response_class=None,
    summary="XML Sitemap",
    description="Generate XML sitemap for search engines"
)
async def get_sitemap(db: AsyncSession = Depends(get_db)):
    """Generate XML sitemap."""
    from fastapi import Response
    service = BlogService(db)
    
    # TODO: Get base URL from config
    base_url = "https://eac.dvvcloud.work"
    sitemap_xml = await service.generate_sitemap(base_url)
    
    return Response(
        content=sitemap_xml,
        media_type="application/xml"
    )


@router.get(
    "/rss.xml",
    response_class=None,
    summary="RSS Feed",
    description="Generate RSS feed for blog"
)
async def get_rss(db: AsyncSession = Depends(get_db)):
    """Generate RSS feed."""
    from fastapi import Response
    service = BlogService(db)
    
    base_url = "https://eac.dvvcloud.work"
    rss_xml = await service.generate_rss(
        base_url=base_url,
        title="ClaimPlane Blog - Flight Compensation Guides",
        description="Expert guides on flight compensation, EU261 rights, and claiming what you're owed."
    )
    
    return Response(
        content=rss_xml,
        media_type="application/rss+xml"
    )