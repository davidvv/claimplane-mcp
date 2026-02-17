"""Admin API router for blog system.

Provides full CRUD operations for managing blog content (admin only).
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.blog_service import BlogService
from app.schemas.blog import (
    BlogPostCreate, BlogPostUpdate, BlogPostResponse, BlogPostListResponse,
    BlogCategoryCreate, BlogCategoryUpdate, BlogCategoryResponse, BlogCategoryListResponse,
    BlogTagCreate, BlogTagUpdate, BlogTagResponse, BlogTagListResponse,
    BlogAuthorCreate, BlogAuthorUpdate, BlogAuthorResponse, BlogAuthorListResponse,
    BlogDashboardStats, PaginationMeta,
    BlogPublishRequest, BlogDuplicateRequest
)

# Create router - uses the same auth as other admin routes
router = APIRouter(prefix="/admin/blog", tags=["Admin - Blog"])


# ============================================================================
# Dashboard
# ============================================================================

@router.get(
    "/dashboard",
    response_model=BlogDashboardStats,
    summary="Get blog dashboard statistics",
    description="Get statistics for the blog dashboard"
)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Get blog dashboard statistics."""
    service = BlogService(db)
    return await service.get_dashboard_stats()


# ============================================================================
# Posts
# ============================================================================

@router.get(
    "/posts",
    response_model=BlogPostListResponse,
    summary="List all blog posts (admin)",
    description="Get all blog posts including drafts (admin only)"
)
async def list_all_posts(
    language: Optional[str] = Query(None, regex="^(en|de|fr)$"),
    status: Optional[str] = Query(None, regex="^(draft|published|archived)$"),
    author_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("created_at", regex="^(published_at|created_at|updated_at|title|view_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get all blog posts (including drafts)."""
    service = BlogService(db)
    
    author_uuid = UUID(author_id) if author_id else None
    posts, total = await service.repository.get_posts(
        language=language,
        status=status,
        author_id=author_uuid,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    from app.schemas.blog import BlogPostSummaryResponse, BlogCategoryResponse
    
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


@router.get(
    "/posts/{post_id}",
    response_model=BlogPostResponse,
    summary="Get blog post details (admin)",
    description="Get complete blog post details including draft posts"
)
async def get_post_admin(
    post_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get blog post by ID (admin)."""
    service = BlogService(db)
    post = await service.repository.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Load content
    frontmatter, markdown_content = await service.load_post_content(post.slug, post.language)
    content_html = service.render_markdown(markdown_content) if markdown_content else None
    
    return BlogPostResponse(
        id=post.id,
        slug=post.slug,
        language=post.language,
        canonical_slug=post.canonical_slug,
        title=post.title,
        excerpt=post.excerpt,
        featured_image_url=post.featured_image_url,
        content=markdown_content,
        content_html=content_html,
        meta_title=post.meta_title,
        meta_description=post.meta_description,
        status=post.status,
        reading_time_minutes=post.reading_time_minutes,
        view_count=post.view_count,
        author=post.author,
        categories=[BlogCategoryResponse.model_validate(c) for c in post.categories],
        tags=[BlogTagResponse.model_validate(t) for t in post.tags],
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at
    )


@router.post(
    "/posts",
    response_model=BlogPostResponse,
    status_code=201,
    summary="Create new blog post",
    description="Create a new blog post with markdown content"
)
async def create_post(
    post_data: BlogPostCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new blog post."""
    service = BlogService(db)
    return await service.create_post(post_data)


@router.put(
    "/posts/{post_id}",
    response_model=BlogPostResponse,
    summary="Update blog post",
    description="Update an existing blog post"
)
async def update_post(
    post_id: UUID,
    post_data: BlogPostUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a blog post."""
    service = BlogService(db)
    updated = await service.update_post(post_id, post_data)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return updated


@router.delete(
    "/posts/{post_id}",
    status_code=204,
    summary="Delete blog post",
    description="Permanently delete a blog post"
)
async def delete_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a blog post."""
    service = BlogService(db)
    deleted = await service.delete_post(post_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return None


@router.post(
    "/posts/{post_id}/publish",
    response_model=BlogPostResponse,
    summary="Publish blog post",
    description="Publish a draft blog post"
)
async def publish_post(
    post_id: UUID,
    publish_data: Optional[BlogPublishRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """Publish a blog post."""
    from datetime import datetime
    service = BlogService(db)
    
    update_data = BlogPostUpdate(
        status="published",
        published_at=publish_data.published_at if publish_data else datetime.utcnow()
    )
    
    updated = await service.update_post(post_id, update_data)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return updated


@router.post(
    "/posts/{post_id}/unpublish",
    response_model=BlogPostResponse,
    summary="Unpublish blog post",
    description="Unpublish a published blog post"
)
async def unpublish_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Unpublish a blog post."""
    service = BlogService(db)
    
    update_data = BlogPostUpdate(status="draft", published_at=None)
    updated = await service.update_post(post_id, update_data)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return updated


@router.post(
    "/posts/{post_id}/duplicate",
    response_model=BlogPostResponse,
    summary="Duplicate blog post",
    description="Create a copy of an existing blog post"
)
async def duplicate_post(
    post_id: UUID,
    duplicate_data: Optional[BlogDuplicateRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """Duplicate a blog post."""
    service = BlogService(db)
    
    # Get original post
    original = await service.repository.get_post_by_id(post_id)
    if not original:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Create duplicate data
    new_slug = duplicate_data.new_slug if duplicate_data else f"{original.slug}-copy"
    new_language = duplicate_data.new_language if duplicate_data else original.language
    
    # Load original content
    frontmatter, content = await service.load_post_content(original.slug, original.language)
    
    create_data = BlogPostCreate(
        slug=new_slug,
        language=new_language,
        title=f"{original.title} (Copy)",
        excerpt=original.excerpt,
        featured_image_url=original.featured_image_url,
        content=content or "",
        meta_title=original.meta_title,
        meta_description=original.meta_description,
        status="draft",
        author_id=original.author_id,
        category_ids=[c.id for c in original.categories],
        tag_ids=[t.id for t in original.tags]
    )
    
    return await service.create_post(create_data)


# ============================================================================
# Categories
# ============================================================================

@router.get(
    "/categories",
    response_model=BlogCategoryListResponse,
    summary="List all categories (admin)",
    description="Get all blog categories"
)
async def list_categories_admin(db: AsyncSession = Depends(get_db)):
    """Get all categories."""
    service = BlogService(db)
    categories = await service.get_categories()
    return BlogCategoryListResponse(data=categories)


@router.post(
    "/categories",
    response_model=BlogCategoryResponse,
    status_code=201,
    summary="Create category",
    description="Create a new blog category"
)
async def create_category(
    category_data: BlogCategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new category."""
    service = BlogService(db)
    return await service.create_category(category_data)


@router.put(
    "/categories/{category_id}",
    response_model=BlogCategoryResponse,
    summary="Update category",
    description="Update an existing blog category"
)
async def update_category(
    category_id: UUID,
    category_data: BlogCategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a category."""
    service = BlogService(db)
    updated = await service.update_category(category_id, category_data)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return updated


@router.delete(
    "/categories/{category_id}",
    status_code=204,
    summary="Delete category",
    description="Delete a blog category (only if no posts use it)"
)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a category."""
    service = BlogService(db)
    
    # Check if category has posts
    category = await service.repository.get_category_by_id(category_id)
    if category and category.posts:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete category with existing posts"
        )
    
    deleted = await service.delete_category(category_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return None


# ============================================================================
# Tags
# ============================================================================

@router.get(
    "/tags",
    response_model=BlogTagListResponse,
    summary="List all tags (admin)",
    description="Get all blog tags"
)
async def list_tags_admin(db: AsyncSession = Depends(get_db)):
    """Get all tags."""
    service = BlogService(db)
    tags = await service.get_tags()
    return BlogTagListResponse(data=tags)


@router.post(
    "/tags",
    response_model=BlogTagResponse,
    status_code=201,
    summary="Create tag",
    description="Create a new blog tag"
)
async def create_tag(
    tag_data: BlogTagCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tag."""
    service = BlogService(db)
    return await service.create_tag(tag_data)


@router.put(
    "/tags/{tag_id}",
    response_model=BlogTagResponse,
    summary="Update tag",
    description="Update an existing blog tag"
)
async def update_tag(
    tag_id: UUID,
    tag_data: BlogTagUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a tag."""
    service = BlogService(db)
    updated = await service.update_tag(tag_id, tag_data)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return updated


@router.delete(
    "/tags/{tag_id}",
    status_code=204,
    summary="Delete tag",
    description="Delete a blog tag (only if no posts use it)"
)
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a tag."""
    service = BlogService(db)
    
    # Check if tag has posts
    tag = await service.repository.get_tag_by_id(tag_id)
    if tag and tag.posts:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete tag with existing posts"
        )
    
    deleted = await service.delete_tag(tag_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return None


# ============================================================================
# Authors
# ============================================================================

@router.get(
    "/authors",
    response_model=BlogAuthorListResponse,
    summary="List all authors (admin)",
    description="Get all blog authors"
)
async def list_authors_admin(db: AsyncSession = Depends(get_db)):
    """Get all authors."""
    service = BlogService(db)
    authors = await service.get_authors()
    return BlogAuthorListResponse(data=authors)


@router.post(
    "/authors",
    response_model=BlogAuthorResponse,
    status_code=201,
    summary="Create author",
    description="Create a new blog author"
)
async def create_author(
    author_data: BlogAuthorCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new author."""
    service = BlogService(db)
    return await service.create_author(author_data)


@router.put(
    "/authors/{author_id}",
    response_model=BlogAuthorResponse,
    summary="Update author",
    description="Update an existing blog author"
)
async def update_author(
    author_id: UUID,
    author_data: BlogAuthorUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an author."""
    service = BlogService(db)
    updated = await service.update_author(author_id, author_data)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Author not found")
    
    return updated


@router.delete(
    "/authors/{author_id}",
    status_code=204,
    summary="Delete author",
    description="Delete a blog author (only if no posts use them)"
)
async def delete_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an author."""
    service = BlogService(db)
    
    # Check if author has posts
    author = await service.repository.get_author_by_id(author_id)
    if author and author.posts:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete author with existing posts"
        )
    
    deleted = await service.delete_author(author_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Author not found")
    
    return None


# ============================================================================
# Media Upload
# ============================================================================

@router.post(
    "/upload-image",
    summary="Upload blog image",
    description="Upload an image for blog posts"
)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload an image for blog posts."""
    import os
    import uuid
    from pathlib import Path
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4()}{file_ext}"
    
    # Save to blog images directory
    upload_dir = Path("frontend_Claude45/public/blog/images")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / unique_name
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Return the public URL
        return {
            "filename": unique_name,
            "url": f"/blog/images/{unique_name}",
            "original_name": file.filename,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")