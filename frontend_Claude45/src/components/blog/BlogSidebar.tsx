/**
 * Blog Sidebar Component
 * Displays categories, tags, and recent posts
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Tag, Folder, Clock, ChevronRight } from 'lucide-react';
import { blogService } from '@/services/blog';
import type { BlogCategory, BlogTag, BlogPostSummary } from '@/types/blog';
import { cn } from '@/lib/utils';
import { LoadingSpinner } from '@/components/LoadingSpinner';

interface BlogSidebarProps {
  className?: string;
}

/**
 * Format date for display
 */
function formatDate(dateString?: string | null): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function BlogSidebar({ className }: BlogSidebarProps) {
  const [categories, setCategories] = useState<BlogCategory[]>([]);
  const [tags, setTags] = useState<BlogTag[]>([]);
  const [recentPosts, setRecentPosts] = useState<BlogPostSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSidebarData() {
      try {
        setLoading(true);
        
        // Fetch all data in parallel
        const [categoriesData, tagsData, recentData] = await Promise.all([
          blogService.getCategories(),
          blogService.getTags(),
          blogService.getPosts({ limit: 5, sort_by: 'published_at', sort_order: 'desc' }),
        ]);

        setCategories(categoriesData);
        setTags(tagsData);
        setRecentPosts(recentData.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching sidebar data:', err);
        setError('Failed to load sidebar content');
      } finally {
        setLoading(false);
      }
    }

    fetchSidebarData();
  }, []);

  if (loading) {
    return (
      <div className={cn('bg-card rounded-lg border p-6', className)}>
        <LoadingSpinner className="py-8" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('bg-card rounded-lg border p-6', className)}>
        <p className="text-sm text-muted-foreground">{error}</p>
      </div>
    );
  }

  return (
    <aside className={cn('space-y-8', className)}>
      {/* Categories */}
      {categories.length > 0 && (
        <div className="bg-card rounded-lg border p-6">
          <div className="flex items-center gap-2 mb-4">
            <Folder className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-lg">Categories</h3>
          </div>
          <ul className="space-y-2">
            {categories.map((category) => (
              <li key={category.id}>
                <Link
                  to={`/blog/category/${category.slug}`}
                  className="flex items-center justify-between py-1.5 px-2 rounded-md hover:bg-muted transition-colors group"
                >
                  <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">
                    {category.name}
                  </span>
                  {category.post_count !== undefined && (
                    <span className="text-xs bg-muted px-2 py-0.5 rounded-full text-muted-foreground">
                      {category.post_count}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
          <Link
            to="/blog"
            className="flex items-center gap-1 text-sm text-primary hover:text-primary/80 mt-4 pt-4 border-t"
          >
            View All Categories
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Tags */}
      {tags.length > 0 && (
        <div className="bg-card rounded-lg border p-6">
          <div className="flex items-center gap-2 mb-4">
            <Tag className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-lg">Popular Tags</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {tags.slice(0, 12).map((tag) => (
              <Link
                key={tag.id}
                to={`/blog/tag/${tag.slug}`}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-muted rounded-full hover:bg-primary/10 hover:text-primary transition-colors"
              >
                {tag.name}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recent Posts */}
      {recentPosts.length > 0 && (
        <div className="bg-card rounded-lg border p-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-lg">Recent Posts</h3>
          </div>
          <ul className="space-y-4">
            {recentPosts.map((post) => (
              <li key={post.id}>
                <Link
                  to={`/blog/${post.slug}`}
                  className="group block"
                >
                  <h4 className="text-sm font-medium text-muted-foreground group-hover:text-primary transition-colors line-clamp-2">
                    {post.title}
                  </h4>
                  <time className="text-xs text-muted-foreground/70 mt-1 block">
                    {formatDate(post.published_at)}
                  </time>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* CTA Box */}
      <div className="bg-primary/5 border border-primary/20 rounded-lg p-6">
        <h3 className="font-semibold text-lg mb-2">Claim Your Compensation</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Did your flight get delayed or cancelled? You may be entitled to compensation up to €600.
        </p>
        <Link
          to="/claim/new"
          className="inline-flex items-center justify-center w-full rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4"
        >
          Start Your Claim
        </Link>
      </div>
    </aside>
  );
}

export default BlogSidebar;
