/**
 * Blog Card Component
 * Displays a preview of a blog post
 */

import { Link } from 'react-router-dom';
import { Calendar, Clock, User, ArrowRight } from 'lucide-react';
import type { BlogPostSummary } from '@/types/blog';
import { cn } from '@/lib/utils';

interface BlogCardProps {
  post: BlogPostSummary;
  featured?: boolean;
  className?: string;
}

/**
 * Format date for display
 */
function formatDate(dateString?: string | null): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Strip HTML and markdown for excerpt
 */
function stripContent(content?: string | null, maxLength: number = 160): string {
  if (!content) return '';
  // Remove markdown headings
  let text = content.replace(/^#+\s+/gm, '');
  // Remove bold/italic markers
  text = text.replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, '$1');
  // Remove links but keep text
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  // Remove extra whitespace
  text = text.replace(/\s+/g, ' ').trim();
  // Truncate
  if (text.length > maxLength) {
    text = text.substring(0, maxLength).trim() + '...';
  }
  return text;
}

export function BlogCard({ post, featured = false, className }: BlogCardProps) {
  const excerpt = post.excerpt || stripContent(post.excerpt || '', 160);
  
  // Use featured image or placeholder
  const imageUrl = post.featured_image_url || '/blog/images/placeholder.jpg';
  
  // Get primary category if available
  const primaryCategory = post.categories?.[0];

  return (
    <article
      className={cn(
        'group bg-card rounded-lg border shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden',
        featured && 'md:grid md:grid-cols-2 md:gap-6',
        className
      )}
    >
      {/* Featured Image */}
      <div className={cn('overflow-hidden', featured ? 'md:h-full' : 'h-48')}>
        <img
          src={imageUrl}
          alt={post.title}
          className={cn(
            'w-full h-full object-cover transition-transform duration-300 group-hover:scale-105',
            featured ? 'md:h-full md:min-h-[300px]' : 'h-48'
          )}
          onError={(e) => {
            // Fallback to gradient background on image error
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            target.parentElement!.classList.add('bg-gradient-to-br', 'from-primary/10', 'to-primary/5');
          }}
        />
      </div>

      {/* Content */}
      <div className={cn('flex flex-col', featured ? 'p-6 md:justify-center' : 'p-5')}>
        {/* Category Badge */}
        {primaryCategory && (
          <Link
            to={`/blog/category/${primaryCategory.slug}`}
            className="inline-block self-start mb-3 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
          >
            {primaryCategory.name}
          </Link>
        )}

        {/* Title */}
        <h2 className={cn(
          'font-bold text-foreground group-hover:text-primary transition-colors',
          featured ? 'text-2xl md:text-3xl mb-3' : 'text-xl mb-2'
        )}>
          <Link to={`/blog/${post.slug}`}>
            {post.title}
          </Link>
        </h2>

        {/* Excerpt */}
        {excerpt && (
          <p className={cn(
            'text-muted-foreground mb-4',
            featured ? 'text-base line-clamp-3' : 'text-sm line-clamp-2'
          )}>
            {excerpt}
          </p>
        )}

        {/* Meta Information */}
        <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
          {/* Author */}
          {post.author && (
            <div className="flex items-center gap-1.5">
              {post.author.avatar_url ? (
                <img
                  src={post.author.avatar_url}
                  alt={post.author.name}
                  className="w-5 h-5 rounded-full object-cover"
                />
              ) : (
                <User className="w-4 h-4" />
              )}
              <span>{post.author.name}</span>
            </div>
          )}

          {/* Published Date */}
          {post.published_at && (
            <div className="flex items-center gap-1.5">
              <Calendar className="w-4 h-4" />
              <span>{formatDate(post.published_at)}</span>
            </div>
          )}

          {/* Reading Time */}
          {post.reading_time_minutes && (
            <div className="flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              <span>{post.reading_time_minutes} min read</span>
            </div>
          )}
        </div>

        {/* Read More Link */}
        <Link
          to={`/blog/${post.slug}`}
          className={cn(
            'inline-flex items-center gap-1 text-sm font-medium text-primary hover:text-primary/80 transition-colors mt-4',
            featured ? 'mt-6' : ''
          )}
        >
          Read Article
          <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </article>
  );
}

export default BlogCard;
