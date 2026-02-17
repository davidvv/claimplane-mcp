"""Service layer for blog system.

Provides business logic for blog operations including markdown processing,
caching, and content management.
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
from uuid import UUID

import yaml
from markdown import markdown
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BlogPost, BlogCategory, BlogTag, BlogAuthor
from app.repositories.blog_repository import BlogRepository
from app.schemas.blog import (
    BlogPostCreate, BlogPostUpdate, BlogPostResponse, BlogPostSummaryResponse,
    BlogCategoryCreate, BlogCategoryUpdate, BlogCategoryResponse,
    BlogTagCreate, BlogTagUpdate, BlogTagResponse,
    BlogAuthorCreate, BlogAuthorUpdate, BlogAuthorResponse,
    PaginationMeta, BlogDashboardStats
)


# Content storage paths
CONTENT_DIR = Path("content")
POSTS_DIR = CONTENT_DIR / "posts"
AUTHORS_DIR = CONTENT_DIR / "authors"
CATEGORIES_DIR = CONTENT_DIR / "categories"


class BlogService:
    """Service for blog business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = BlogRepository(session)
    
    # =========================================================================
    # Markdown Processing
    # =========================================================================
    
    @staticmethod
    def parse_frontmatter(content: str) -> Tuple[dict, str]:
        """Parse YAML frontmatter from markdown content.
        
        Returns:
            Tuple of (frontmatter dict, markdown content)
        """
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
                markdown_content = match.group(2)
                return frontmatter or {}, markdown_content
            except yaml.YAMLError:
                pass
        
        return {}, content
    
    @staticmethod
    def render_markdown(content: str) -> str:
        """Render markdown to HTML with extensions."""
        return markdown(
            content,
            extensions=[
                'toc',
                'fenced_code',
                'tables',
                'nl2br'
            ]
        )
    
    @staticmethod
    def calculate_reading_time(content: str) -> int:
        """Calculate estimated reading time in minutes.
        
        Average reading speed: 200 words per minute
        """
        # Remove markdown syntax for word count
        text = re.sub(r'[#*_\[\](){}|`]', '', content)
        words = len(text.split())
        minutes = max(1, round(words / 200))
        return minutes
    
    @staticmethod
    def generate_slug(title: str) -> str:
        """Generate URL-friendly slug from title."""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    # =========================================================================
    # File Operations
    # =========================================================================
    
    def get_content_path(self, slug: str, language: str) -> Path:
        """Get the file path for a blog post."""
        return POSTS_DIR / language / f"{slug}.md"
    
    async def save_post_content(
        self,
        slug: str,
        language: str,
        frontmatter: dict,
        content: str
    ) -> None:
        """Save blog post content to markdown file."""
        # Ensure directory exists
        post_dir = POSTS_DIR / language
        post_dir.mkdir(parents=True, exist_ok=True)
        
        # Build markdown with frontmatter
        frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        markdown_content = f"---\n{frontmatter_yaml}---\n\n{content}"
        
        # Write to file
        file_path = self.get_content_path(slug, language)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    async def load_post_content(self, slug: str, language: str) -> Tuple[Optional[dict], Optional[str]]:
        """Load blog post content from markdown file."""
        file_path = self.get_content_path(slug, language)
        
        if not file_path.exists():
            return None, None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter, markdown_content = self.parse_frontmatter(content)
            return frontmatter, markdown_content
        except Exception:
            return None, None
    
    async def delete_post_content(self, slug: str, language: str) -> bool:
        """Delete blog post markdown file."""
        file_path = self.get_content_path(slug, language)
        
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    # =========================================================================
    # Post Operations
    # =========================================================================
    
    async def get_post(self, slug: str, language: str, increment_views: bool = False) -> Optional[BlogPostResponse]:
        """Get a single blog post by slug."""
        post = await self.repository.get_post_by_slug(slug, language)
        
        if not post:
            return None
        
        # Load content from markdown file
        frontmatter, markdown_content = await self.load_post_content(slug, language)
        
        if increment_views and post.status == "published":
            await self.repository.increment_view_count(post.id)
            post.view_count += 1
        
        # Render HTML if needed
        content_html = None
        if markdown_content:
            content_html = self.render_markdown(markdown_content)
        elif post.content_html_cache:
            content_html = post.content_html_cache
        
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
            author=BlogAuthorResponse.model_validate(post.author) if post.author else None,
            categories=[BlogCategoryResponse.model_validate(c) for c in post.categories],
            tags=[BlogTagResponse.model_validate(t) for t in post.tags],
            published_at=post.published_at,
            created_at=post.created_at,
            updated_at=post.updated_at
        )
    
    async def get_posts(
        self,
        language: Optional[str] = None,
        status: str = "published",
        page: int = 1,
        limit: int = 10,
        sort_by: str = "published_at",
        sort_order: str = "desc"
    ) -> Tuple[List[BlogPostSummaryResponse], PaginationMeta]:
        """Get paginated list of blog posts."""
        posts, total = await self.repository.get_posts(
            language=language,
            status=status,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        total_pages = (total + limit - 1) // limit
        
        data = []
        for post in posts:
            data.append(BlogPostSummaryResponse(
                id=post.id,
                slug=post.slug,
                language=post.language,
                title=post.title,
                excerpt=post.excerpt,
                featured_image_url=post.featured_image_url,
                status=post.status,
                published_at=post.published_at,
                view_count=post.view_count,
                reading_time_minutes=post.reading_time_minutes,
                author=BlogAuthorResponse.model_validate(post.author) if post.author else None,
                categories=[BlogCategoryResponse.model_validate(c) for c in post.categories],
                created_at=post.created_at
            ))
        
        pagination = PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return data, pagination
    
    async def create_post(self, post_data: BlogPostCreate) -> BlogPostResponse:
        """Create a new blog post."""
        # Generate slug if not provided
        slug = post_data.slug or self.generate_slug(post_data.title)
        
        # Calculate reading time
        reading_time = self.calculate_reading_time(post_data.content or "")
        
        # Create database record
        post = BlogPost(
            slug=slug,
            language=post_data.language,
            canonical_slug=post_data.canonical_slug,
            title=post_data.title,
            excerpt=post_data.excerpt,
            featured_image_url=post_data.featured_image_url,
            content_path=str(self.get_content_path(slug, post_data.language)),
            meta_title=post_data.meta_title,
            meta_description=post_data.meta_description,
            status=post_data.status,
            author_id=post_data.author_id,
            published_at=post_data.published_at,
            reading_time_minutes=reading_time
        )
        
        created_post = await self.repository.create_post(post)
        
        # Add categories and tags
        if post_data.category_ids:
            for category_id in post_data.category_ids:
                category = await self.repository.get_category_by_id(category_id)
                if category:
                    created_post.categories.append(category)
        
        if post_data.tag_ids:
            for tag_id in post_data.tag_ids:
                tag = await self.repository.get_tag_by_id(tag_id)
                if tag:
                    created_post.tags.append(tag)
        
        await self.session.commit()
        
        # Save markdown content
        frontmatter = {
            "title": post_data.title,
            "excerpt": post_data.excerpt,
            "author_id": str(post_data.author_id),
            "published_at": post_data.published_at.isoformat() if post_data.published_at else None,
            "featured_image": post_data.featured_image_url,
            "categories": [await self._get_category_slug(cid) for cid in (post_data.category_ids or [])],
            "tags": [await self._get_tag_slug(tid) for tid in (post_data.tag_ids or [])],
            "meta_title": post_data.meta_title,
            "meta_description": post_data.meta_description,
            "language": post_data.language,
            "canonical_slug": post_data.canonical_slug,
        }
        
        await self.save_post_content(slug, post_data.language, frontmatter, post_data.content or "")
        
        return await self.get_post(slug, post_data.language)
    
    async def _get_category_slug(self, category_id: UUID) -> str:
        """Helper to get category slug by ID."""
        category = await self.repository.get_category_by_id(category_id)
        return category.slug if category else ""
    
    async def _get_tag_slug(self, tag_id: UUID) -> str:
        """Helper to get tag slug by ID."""
        tag = await self.repository.get_tag_by_id(tag_id)
        return tag.slug if tag else ""
    
    async def update_post(
        self,
        post_id: UUID,
        post_data: BlogPostUpdate
    ) -> Optional[BlogPostResponse]:
        """Update an existing blog post."""
        post = await self.repository.get_post_by_id(post_id)
        
        if not post:
            return None
        
        # Update fields
        if post_data.slug:
            post.slug = post_data.slug
        if post_data.language:
            post.language = post_data.language
        if post_data.canonical_slug is not None:
            post.canonical_slug = post_data.canonical_slug
        if post_data.title:
            post.title = post_data.title
        if post_data.excerpt is not None:
            post.excerpt = post_data.excerpt
        if post_data.featured_image_url is not None:
            post.featured_image_url = post_data.featured_image_url
        if post_data.meta_title is not None:
            post.meta_title = post_data.meta_title
        if post_data.meta_description is not None:
            post.meta_description = post_data.meta_description
        if post_data.status:
            post.status = post_data.status
        if post_data.author_id:
            post.author_id = post_data.author_id
        if post_data.published_at is not None:
            post.published_at = post_data.published_at
        if post_data.reading_time_minutes is not None:
            post.reading_time_minutes = post_data.reading_time_minutes
        elif post_data.content:
            post.reading_time_minutes = self.calculate_reading_time(post_data.content)
        
        # Update categories
        if post_data.category_ids is not None:
            post.categories = []
            for category_id in post_data.category_ids:
                category = await self.repository.get_category_by_id(category_id)
                if category:
                    post.categories.append(category)
        
        # Update tags
        if post_data.tag_ids is not None:
            post.tags = []
            for tag_id in post_data.tag_ids:
                tag = await self.repository.get_tag_by_id(tag_id)
                if tag:
                    post.tags.append(tag)
        
        await self.repository.update_post(post)
        
        # Update markdown content if provided
        if post_data.content is not None:
            frontmatter = {
                "title": post.title,
                "excerpt": post.excerpt,
                "author_id": str(post.author_id),
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "featured_image": post.featured_image_url,
                "categories": [c.slug for c in post.categories],
                "tags": [t.slug for t in post.tags],
                "meta_title": post.meta_title,
                "meta_description": post.meta_description,
                "language": post.language,
                "canonical_slug": post.canonical_slug,
            }
            
            await self.save_post_content(post.slug, post.language, frontmatter, post_data.content)
        
        return await self.get_post(post.slug, post.language)
    
    async def delete_post(self, post_id: UUID) -> bool:
        """Delete a blog post."""
        post = await self.repository.get_post_by_id(post_id)
        
        if not post:
            return False
        
        # Delete markdown file
        await self.delete_post_content(post.slug, post.language)
        
        # Delete database record
        return await self.repository.delete_post(post_id)
    
    async def get_related_posts(self, slug: str, language: str, limit: int = 3) -> List[BlogPostSummaryResponse]:
        """Get related posts for a given post."""
        post = await self.repository.get_post_by_slug(slug, language)
        
        if not post:
            return []
        
        related = await self.repository.get_related_posts(post.id, limit)
        
        return [
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
                author=BlogAuthorResponse.model_validate(p.author) if p.author else None,
                categories=[BlogCategoryResponse.model_validate(c) for c in p.categories],
                created_at=p.created_at
            )
            for p in related
        ]
    
    # =========================================================================
    # Category Operations
    # =========================================================================
    
    async def get_categories(self) -> List[BlogCategoryResponse]:
        """Get all categories."""
        categories = await self.repository.get_categories()
        return [BlogCategoryResponse.model_validate(c) for c in categories]
    
    async def get_category_by_slug(self, slug: str) -> Optional[BlogCategory]:
        """Get category by slug."""
        return await self.repository.get_category_by_slug(slug)
    
    async def create_category(self, category_data: BlogCategoryCreate) -> BlogCategoryResponse:
        """Create a new category."""
        category = BlogCategory(
            slug=category_data.slug,
            name=category_data.name,
            description=category_data.description,
            parent_id=category_data.parent_id,
            sort_order=category_data.sort_order
        )
        
        created = await self.repository.create_category(category)
        return BlogCategoryResponse.model_validate(created)
    
    async def update_category(
        self,
        category_id: UUID,
        category_data: BlogCategoryUpdate
    ) -> Optional[BlogCategoryResponse]:
        """Update a category."""
        category = await self.repository.get_category_by_id(category_id)
        
        if not category:
            return None
        
        if category_data.slug:
            category.slug = category_data.slug
        if category_data.name:
            category.name = category_data.name
        if category_data.description is not None:
            category.description = category_data.description
        if category_data.parent_id is not None:
            category.parent_id = category_data.parent_id
        if category_data.sort_order is not None:
            category.sort_order = category_data.sort_order
        
        updated = await self.repository.update_category(category)
        return BlogCategoryResponse.model_validate(updated)
    
    async def delete_category(self, category_id: UUID) -> bool:
        """Delete a category."""
        return await self.repository.delete_category(category_id)
    
    # =========================================================================
    # Tag Operations
    # =========================================================================
    
    async def get_tags(self) -> List[BlogTagResponse]:
        """Get all tags."""
        tags = await self.repository.get_tags()
        return [BlogTagResponse.model_validate(t) for t in tags]
    
    async def get_tag_by_slug(self, slug: str) -> Optional[BlogTag]:
        """Get tag by slug."""
        return await self.repository.get_tag_by_slug(slug)
    
    async def create_tag(self, tag_data: BlogTagCreate) -> BlogTagResponse:
        """Create a new tag."""
        tag = BlogTag(slug=tag_data.slug, name=tag_data.name)
        created = await self.repository.create_tag(tag)
        return BlogTagResponse.model_validate(created)
    
    async def update_tag(self, tag_id: UUID, tag_data: BlogTagUpdate) -> Optional[BlogTagResponse]:
        """Update a tag."""
        tag = await self.repository.get_tag_by_id(tag_id)
        
        if not tag:
            return None
        
        if tag_data.slug:
            tag.slug = tag_data.slug
        if tag_data.name:
            tag.name = tag_data.name
        
        updated = await self.repository.update_tag(tag)
        return BlogTagResponse.model_validate(updated)
    
    async def delete_tag(self, tag_id: UUID) -> bool:
        """Delete a tag."""
        return await self.repository.delete_tag(tag_id)
    
    # =========================================================================
    # Author Operations
    # =========================================================================
    
    async def get_authors(self) -> List[BlogAuthorResponse]:
        """Get all authors."""
        authors = await self.repository.get_authors()
        return [BlogAuthorResponse.model_validate(a) for a in authors]
    
    async def get_author(self, author_id: UUID) -> Optional[BlogAuthor]:
        """Get author by ID."""
        return await self.repository.get_author_by_id(author_id)
    
    async def create_author(self, author_data: BlogAuthorCreate) -> BlogAuthorResponse:
        """Create a new author."""
        author = BlogAuthor(
            name=author_data.name,
            bio=author_data.bio,
            avatar_url=author_data.avatar_url,
            social_links=author_data.social_links,
            email=author_data.email
        )
        
        created = await self.repository.create_author(author)
        return BlogAuthorResponse.model_validate(created)
    
    async def update_author(
        self,
        author_id: UUID,
        author_data: BlogAuthorUpdate
    ) -> Optional[BlogAuthorResponse]:
        """Update an author."""
        author = await self.repository.get_author_by_id(author_id)
        
        if not author:
            return None
        
        if author_data.name:
            author.name = author_data.name
        if author_data.bio is not None:
            author.bio = author_data.bio
        if author_data.avatar_url is not None:
            author.avatar_url = author_data.avatar_url
        if author_data.social_links is not None:
            author.social_links = author_data.social_links
        if author_data.email is not None:
            author.email = author_data.email
        
        updated = await self.repository.update_author(author)
        return BlogAuthorResponse.model_validate(updated)
    
    async def delete_author(self, author_id: UUID) -> bool:
        """Delete an author."""
        return await self.repository.delete_author(author_id)
    
    # =========================================================================
    # Dashboard & Statistics
    # =========================================================================
    
    async def get_dashboard_stats(self) -> BlogDashboardStats:
        """Get blog dashboard statistics."""
        stats = await self.repository.get_blog_stats()
        
        # Get recent posts
        recent_posts, _ = await self.repository.get_posts(
            status="published",
            page=1,
            limit=5,
            sort_by="published_at",
            sort_order="desc"
        )
        
        return BlogDashboardStats(
            total_posts=stats["total_posts"],
            published_posts=stats["published_posts"],
            draft_posts=stats["draft_posts"],
            archived_posts=stats["archived_posts"],
            total_views=stats["total_views"],
            recent_posts=[
                BlogPostSummaryResponse.model_validate(p) for p in recent_posts
            ]
        )
    
    # =========================================================================
    # SEO Operations
    # =========================================================================
    
    async def generate_sitemap(self, base_url: str) -> str:
        """Generate XML sitemap for blog."""
        posts, _ = await self.repository.get_posts(status="published", page=1, limit=1000)
        categories = await self.repository.get_categories()
        tags = await self.repository.get_tags()
        
        urls = []
        
        # Add posts
        for post in posts:
            urls.append(f"""
    <url>
        <loc>{base_url}/blog/{post.language}/{post.slug}</loc>
        <lastmod>{post.updated_at.strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>""")
        
        # Add categories
        for category in categories:
            urls.append(f"""
    <url>
        <loc>{base_url}/blog/category/{category.slug}</loc>
        <changefreq>weekly</changefreq>
        <priority>0.6</priority>
    </url>""")
        
        # Add tags
        for tag in tags:
            urls.append(f"""
    <url>
        <loc>{base_url}/blog/tag/{tag.slug}</loc>
        <changefreq>weekly</changefreq>
        <priority>0.4</priority>
    </url>""")
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(urls)}
</urlset>"""
    
    async def generate_rss(self, base_url: str, title: str, description: str) -> str:
        """Generate RSS feed for blog."""
        posts, _ = await self.repository.get_posts(
            status="published",
            page=1,
            limit=20,
            sort_by="published_at",
            sort_order="desc"
        )
        
        items = []
        for post in posts:
            content = post.excerpt or ""
            items.append(f"""
        <item>
            <title>{post.title}</title>
            <link>{base_url}/blog/{post.language}/{post.slug}</link>
            <description><![CDATA[{content}]]></description>
            <pubDate>{post.published_at.strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
            <guid>{base_url}/blog/{post.language}/{post.slug}</guid>
            {f'<author>{post.author.email}</author>' if post.author and post.author.email else ''}
        </item>""")
        
        last_build = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>{title}</title>
        <link>{base_url}/blog</link>
        <description>{description}</description>
        <lastBuildDate>{last_build}</lastBuildDate>
        <language>en</language>
        {''.join(items)}
    </channel>
</rss>"""