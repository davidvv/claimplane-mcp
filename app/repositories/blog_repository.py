"""Repository layer for blog system.

Provides database operations for blog posts, categories, tags, and authors.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import BlogPost, BlogCategory, BlogTag, BlogAuthor


class BlogRepository:
    """Repository for blog-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # =========================================================================
    # Blog Post Operations
    # =========================================================================
    
    async def get_post_by_id(self, post_id: UUID) -> Optional[BlogPost]:
        """Get a blog post by ID with all relationships."""
        result = await self.session.execute(
            select(BlogPost)
            .where(BlogPost.id == post_id)
            .options(
                selectinload(BlogPost.author),
                selectinload(BlogPost.categories),
                selectinload(BlogPost.tags)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_post_by_slug(self, slug: str, language: str) -> Optional[BlogPost]:
        """Get a blog post by slug and language."""
        result = await self.session.execute(
            select(BlogPost)
            .where(BlogPost.slug == slug)
            .where(BlogPost.language == language)
            .options(
                selectinload(BlogPost.author),
                selectinload(BlogPost.categories),
                selectinload(BlogPost.tags)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_posts(
        self,
        language: Optional[str] = None,
        status: Optional[str] = None,
        author_id: Optional[UUID] = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "published_at",
        sort_order: str = "desc"
    ) -> tuple[List[BlogPost], int]:
        """Get paginated blog posts with filters."""
        # Build base query
        query = select(BlogPost).options(
            selectinload(BlogPost.author),
            selectinload(BlogPost.categories)
        )
        
        # Apply filters
        if language:
            query = query.where(BlogPost.language == language)
        if status:
            query = query.where(BlogPost.status == status)
        if author_id:
            query = query.where(BlogPost.author_id == author_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        sort_column = getattr(BlogPost, sort_by, BlogPost.published_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        posts = result.scalars().all()
        
        return list(posts), total
    
    async def get_posts_by_category(
        self,
        category_slug: str,
        language: Optional[str] = None,
        status: str = "published",
        page: int = 1,
        limit: int = 10
    ) -> tuple[List[BlogPost], int]:
        """Get posts by category slug."""
        # First get category ID
        cat_result = await self.session.execute(
            select(BlogCategory).where(BlogCategory.slug == category_slug)
        )
        category = cat_result.scalar_one_or_none()
        
        if not category:
            return [], 0
        
        # Query posts in this category
        query = (
            select(BlogPost)
            .join(BlogPost.categories)
            .where(BlogCategory.id == category.id)
            .where(BlogPost.status == status)
            .options(selectinload(BlogPost.author), selectinload(BlogPost.categories))
        )
        
        if language:
            query = query.where(BlogPost.language == language)
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.order_by(desc(BlogPost.published_at)).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def get_posts_by_tag(
        self,
        tag_slug: str,
        language: Optional[str] = None,
        status: str = "published",
        page: int = 1,
        limit: int = 10
    ) -> tuple[List[BlogPost], int]:
        """Get posts by tag slug."""
        # First get tag ID
        tag_result = await self.session.execute(
            select(BlogTag).where(BlogTag.slug == tag_slug)
        )
        tag = tag_result.scalar_one_or_none()
        
        if not tag:
            return [], 0
        
        # Query posts with this tag
        query = (
            select(BlogPost)
            .join(BlogPost.tags)
            .where(BlogTag.id == tag.id)
            .where(BlogPost.status == status)
            .options(selectinload(BlogPost.author), selectinload(BlogPost.tags))
        )
        
        if language:
            query = query.where(BlogPost.language == language)
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.order_by(desc(BlogPost.published_at)).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def search_posts(
        self,
        query: str,
        language: Optional[str] = None,
        status: str = "published",
        page: int = 1,
        limit: int = 10
    ) -> tuple[List[BlogPost], int]:
        """Search posts by title and excerpt."""
        search_term = f"%{query}%"
        
        db_query = (
            select(BlogPost)
            .where(
                (BlogPost.title.ilike(search_term)) |
                (BlogPost.excerpt.ilike(search_term))
            )
            .where(BlogPost.status == status)
            .options(selectinload(BlogPost.author), selectinload(BlogPost.categories))
        )
        
        if language:
            db_query = db_query.where(BlogPost.language == language)
        
        # Get total
        count_query = select(func.count()).select_from(db_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * limit
        db_query = db_query.order_by(desc(BlogPost.published_at)).offset(offset).limit(limit)
        
        result = await self.session.execute(db_query)
        return list(result.scalars().all()), total
    
    async def get_related_posts(
        self,
        post_id: UUID,
        limit: int = 3
    ) -> List[BlogPost]:
        """Get related posts based on categories."""
        # Get the post first to find its categories
        post = await self.get_post_by_id(post_id)
        if not post or not post.categories:
            return []
        
        category_ids = [c.id for c in post.categories]
        
        # Find posts with same categories, excluding current post
        query = (
            select(BlogPost)
            .join(BlogPost.categories)
            .where(BlogCategory.id.in_(category_ids))
            .where(BlogPost.id != post_id)
            .where(BlogPost.status == "published")
            .where(BlogPost.language == post.language)
            .options(selectinload(BlogPost.author))
            .distinct()
            .order_by(desc(BlogPost.published_at))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_post(self, post: BlogPost) -> BlogPost:
        """Create a new blog post."""
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post
    
    async def update_post(self, post: BlogPost) -> BlogPost:
        """Update an existing blog post."""
        await self.session.commit()
        await self.session.refresh(post)
        return post
    
    async def delete_post(self, post_id: UUID) -> bool:
        """Delete a blog post."""
        post = await self.get_post_by_id(post_id)
        if post:
            await self.session.delete(post)
            await self.session.commit()
            return True
        return False
    
    async def increment_view_count(self, post_id: UUID) -> None:
        """Increment the view count for a post."""
        await self.session.execute(
            select(BlogPost)
            .where(BlogPost.id == post_id)
        )
        post = await self.get_post_by_id(post_id)
        if post:
            post.view_count += 1
            await self.session.commit()
    
    # =========================================================================
    # Category Operations
    # =========================================================================
    
    async def get_category_by_id(self, category_id: UUID) -> Optional[BlogCategory]:
        """Get a category by ID."""
        result = await self.session.execute(
            select(BlogCategory).where(BlogCategory.id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def get_category_by_slug(self, slug: str) -> Optional[BlogCategory]:
        """Get a category by slug."""
        result = await self.session.execute(
            select(BlogCategory).where(BlogCategory.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def get_categories(
        self,
        parent_id: Optional[UUID] = None
    ) -> List[BlogCategory]:
        """Get all categories, optionally filtered by parent."""
        query = select(BlogCategory).order_by(BlogCategory.sort_order)
        
        if parent_id is not None:
            query = query.where(BlogCategory.parent_id == parent_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_category(self, category: BlogCategory) -> BlogCategory:
        """Create a new category."""
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def update_category(self, category: BlogCategory) -> BlogCategory:
        """Update an existing category."""
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def delete_category(self, category_id: UUID) -> bool:
        """Delete a category."""
        category = await self.get_category_by_id(category_id)
        if category:
            await self.session.delete(category)
            await self.session.commit()
            return True
        return False
    
    # =========================================================================
    # Tag Operations
    # =========================================================================
    
    async def get_tag_by_id(self, tag_id: UUID) -> Optional[BlogTag]:
        """Get a tag by ID."""
        result = await self.session.execute(
            select(BlogTag).where(BlogTag.id == tag_id)
        )
        return result.scalar_one_or_none()
    
    async def get_tag_by_slug(self, slug: str) -> Optional[BlogTag]:
        """Get a tag by slug."""
        result = await self.session.execute(
            select(BlogTag).where(BlogTag.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def get_tags(self) -> List[BlogTag]:
        """Get all tags."""
        result = await self.session.execute(select(BlogTag))
        return list(result.scalars().all())
    
    async def get_or_create_tag(self, name: str, slug: str) -> BlogTag:
        """Get existing tag or create new one."""
        result = await self.session.execute(
            select(BlogTag).where(BlogTag.slug == slug)
        )
        tag = result.scalar_one_or_none()
        
        if not tag:
            tag = BlogTag(name=name, slug=slug)
            self.session.add(tag)
            await self.session.commit()
            await self.session.refresh(tag)
        
        return tag
    
    async def create_tag(self, tag: BlogTag) -> BlogTag:
        """Create a new tag."""
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag
    
    async def update_tag(self, tag: BlogTag) -> BlogTag:
        """Update an existing tag."""
        await self.session.commit()
        await self.session.refresh(tag)
        return tag
    
    async def delete_tag(self, tag_id: UUID) -> bool:
        """Delete a tag."""
        tag = await self.get_tag_by_id(tag_id)
        if tag:
            await self.session.delete(tag)
            await self.session.commit()
            return True
        return False
    
    # =========================================================================
    # Author Operations
    # =========================================================================
    
    async def get_author_by_id(self, author_id: UUID) -> Optional[BlogAuthor]:
        """Get an author by ID."""
        result = await self.session.execute(
            select(BlogAuthor).where(BlogAuthor.id == author_id)
        )
        return result.scalar_one_or_none()
    
    async def get_authors(self) -> List[BlogAuthor]:
        """Get all authors."""
        result = await self.session.execute(select(BlogAuthor))
        return list(result.scalars().all())
    
    async def create_author(self, author: BlogAuthor) -> BlogAuthor:
        """Create a new author."""
        self.session.add(author)
        await self.session.commit()
        await self.session.refresh(author)
        return author
    
    async def update_author(self, author: BlogAuthor) -> BlogAuthor:
        """Update an existing author."""
        await self.session.commit()
        await self.session.refresh(author)
        return author
    
    async def delete_author(self, author_id: UUID) -> bool:
        """Delete an author."""
        author = await self.get_author_by_id(author_id)
        if author:
            await self.session.delete(author)
            await self.session.commit()
            return True
        return False
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    async def get_blog_stats(self) -> dict:
        """Get blog statistics for dashboard."""
        # Total posts
        total_result = await self.session.execute(select(func.count()).select_from(BlogPost))
        total_posts = total_result.scalar()
        
        # Published posts
        published_result = await self.session.execute(
            select(func.count()).where(BlogPost.status == "published")
        )
        published_posts = published_result.scalar()
        
        # Draft posts
        draft_result = await self.session.execute(
            select(func.count()).where(BlogPost.status == "draft")
        )
        draft_posts = draft_result.scalar()
        
        # Archived posts
        archived_result = await self.session.execute(
            select(func.count()).where(BlogPost.status == "archived")
        )
        archived_posts = archived_result.scalar()
        
        # Total views
        views_result = await self.session.execute(
            select(func.sum(BlogPost.view_count))
        )
        total_views = views_result.scalar() or 0
        
        return {
            "total_posts": total_posts,
            "published_posts": published_posts,
            "draft_posts": draft_posts,
            "archived_posts": archived_posts,
            "total_views": total_views
        }