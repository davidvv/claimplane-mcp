/**
 * Related Posts Component
 * Displays related posts based on category
 */

import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { Calendar, ArrowRight } from 'lucide-react';
import { blogService } from '@/services/blog';
import type { BlogPostSummary, BlogCategory } from '@/types/blog';
import { cn } from '@/lib/utils';
import { LoadingSpinner } from '@/components/LoadingSpinner';

interface RelatedPostsProps {
  postId: string;
  categories: BlogCategory[];
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

export function RelatedPosts({ postId, categories, className }: RelatedPostsProps) {
  const [posts, setPosts] = useState<BlogPostSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRelatedPosts() {
      if (!categories.length) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        // Get posts from the first category
        const categorySlug = categories[0].slug;
        const response = await blogService.getPostsByCategory(categorySlug, {
          limit: 4,
        });

        // Filter out the current post
        const filtered = response.data.filter((p) => p.id !== postId).slice(0, 3);
        setPosts(filtered);
        setError(null);
      } catch (err) {
        console.error('Error fetching related posts:', err);
        setError('Failed to load related posts');
      } finally {
        setLoading(false);
      }
    }

    fetchRelatedPosts();
  }, [postId, categories]);

  if (loading) {
    return (
      <div className={cn('py-8', className)}>
        <LoadingSpinner className="py-4" />
      </div>
    );
  }

  if (error || posts.length === 0) {
    return null;
  }

  return (
    <div className={cn('py-8 border-t', className)}>
      <h2 className="text-2xl font-bold mb-6">Related Articles</h2>

      {/* Desktop: Grid */}
      <div className="hidden md:grid md:grid-cols-3 gap-6">
        {posts.map((post) => (
          <Link
            key={post.id}
            to={`/blog/${post.slug}`}
            className="group bg-card border rounded-lg overflow-hidden hover:shadow-md transition-shadow"
          >
            {/* Image */}
            <div className="h-36 overflow-hidden">
              <img
                src={post.featured_image_url || '/blog/images/placeholder.jpg'}
                alt={post.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
            </div>

            {/* Content */}
            <div className="p-4">
              <h3 className="font-semibold line-clamp-2 group-hover:text-primary transition-colors">
                {post.title}
              </h3>
              {post.published_at && (
                <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatDate(post.published_at)}
                </p>
              )}
            </div>
          </Link>
        ))}
      </div>

      {/* Mobile: Horizontal scroll */}
      <div className="md:hidden -mx-4 px-4 overflow-x-auto scrollbar-hide">
        <div className="flex gap-4" style={{ width: 'max-content' }}>
          {posts.map((post) => (
            <Link
              key={post.id}
              to={`/blog/${post.slug}`}
              className="group bg-card border rounded-lg overflow-hidden hover:shadow-md transition-shadow flex-shrink-0"
              style={{ width: '240px' }}
            >
              {/* Image */}
              <div className="h-32 overflow-hidden">
                <img
                  src={post.featured_image_url || '/blog/images/placeholder.jpg'}
                  alt={post.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>

              {/* Content */}
              <div className="p-3">
                <h3 className="font-medium text-sm line-clamp-2 group-hover:text-primary transition-colors">
                  {post.title}
                </h3>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* View more link */}
      {categories[0] && (
        <Link
          to={`/blog/category/${categories[0].slug}`}
          className="inline-flex items-center gap-1 mt-6 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
        >
          More in {categories[0].name}
          <ArrowRight className="w-4 h-4" />
        </Link>
      )}
    </div>
  );
}

export default RelatedPosts;
