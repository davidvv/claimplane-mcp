/**
 * Blog Post Page
 * Single blog post view with rich content rendering
 */

import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Calendar, Clock, User, ChevronRight, Home, ArrowLeft, FileText } from 'lucide-react';
import { blogService } from '@/services/blog';
import type { BlogPost, HeadingItem } from '@/types/blog';
import { MarkdownRenderer } from '@/components/blog/MarkdownRenderer';
import { TableOfContents } from '@/components/blog/TableOfContents';
import { AuthorBio } from '@/components/blog/AuthorBio';
import { RelatedPosts } from '@/components/blog/RelatedPosts';
import { BlogCTAWidget } from '@/components/blog/BlogCTAWidget';
import { SocialShare } from '@/components/blog/SocialShare';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Button } from '@/components/ui/Button';

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

export function BlogPostPage() {
  const { slug } = useParams<{ slug: string }>();
  
  // State
  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [headings, setHeadings] = useState<HeadingItem[]>([]);

  // Handle headings extraction from markdown
  const handleHeadingsExtracted = useCallback((extractedHeadings: HeadingItem[]) => {
    setHeadings(extractedHeadings);
  }, []);

  // Fetch post
  useEffect(() => {
    async function fetchPost() {
      if (!slug) return;

      try {
        setLoading(true);
        setError(null);
        
        const postData = await blogService.getPostBySlug(slug);
        setPost(postData);
      } catch (err: any) {
        console.error('Error fetching blog post:', err);
        if (err.response?.status === 404) {
          setError('Post not found');
        } else {
          setError('Failed to load blog post. Please try again later.');
        }
      } finally {
        setLoading(false);
      }
    }

    fetchPost();
  }, [slug]);

  // Scroll to top when post changes
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [slug]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
        <div className="container mx-auto px-4 py-12">
          <div className="flex justify-center py-16">
            <LoadingSpinner className="py-8" />
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !post) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
        <div className="container mx-auto px-4 py-12">
          <div className="text-center py-16">
            <FileText className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
            <h1 className="text-2xl font-bold mb-2">
              {error === 'Post not found' ? 'Post Not Found' : 'Error Loading Post'}
            </h1>
            <p className="text-muted-foreground mb-6">
              {error || 'We couldn\'t load this blog post. Please try again later.'}
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link to="/blog">
                <Button variant="outline">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Blog
                </Button>
              </Link>
              <Link to="/">
                <Button>
                  Go Home
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Determine content to render
  const content = post.content_html || post.content || '';
  const imageUrl = post.featured_image_url || '/blog/images/placeholder.jpg';
  const pageUrl = `https://eac.dvvcloud.work/blog/${post.slug}`;

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* SEO Meta Tags */}
      <Helmet>
        <title>{post.title} | ClaimPlane Blog</title>
        <meta name="description" content={post.excerpt || post.title} />
        <link rel="canonical" href={pageUrl} />
        
        {/* Open Graph */}
        <meta property="og:type" content="article" />
        <meta property="og:title" content={post.title} />
        <meta property="og:description" content={post.excerpt || post.title} />
        <meta property="og:image" content={imageUrl} />
        <meta property="og:url" content={pageUrl} />
        <meta property="article:published_time" content={post.published_at || ''} />
        <meta property="article:author" content={post.author?.name || ''} />
        {post.categories.map((cat) => (
          <meta key={cat.id} property="article:section" content={cat.name} />
        ))}
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={post.title} />
        <meta name="twitter:description" content={post.excerpt || post.title} />
        <meta name="twitter:image" content={imageUrl} />

        {/* JSON-LD Structured Data */}
        <script type="application/ld+json">
          {JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'Article',
            headline: post.title,
            description: post.excerpt,
            image: imageUrl,
            datePublished: post.published_at,
            dateModified: post.updated_at,
            author: {
              '@type': 'Person',
              name: post.author?.name,
            },
            publisher: {
              '@type': 'Organization',
              name: 'ClaimPlane',
              logo: {
                '@type': 'ImageObject',
                url: 'https://eac.dvvcloud.work/logo.png',
              },
            },
            mainEntityOfPage: {
              '@type': 'WebPage',
              '@id': pageUrl,
            },
          })}
        </script>
      </Helmet>

      {/* Breadcrumb */}
      <div className="bg-muted/30 border-b">
        <div className="container mx-auto px-4 py-3">
          <nav className="flex items-center gap-2 text-sm text-muted-foreground">
            <Link to="/" className="hover:text-foreground transition-colors">
              <Home className="w-4 h-4" />
            </Link>
            <ChevronRight className="w-4 h-4" />
            <Link to="/blog" className="hover:text-foreground transition-colors">
              Blog
            </Link>
            <ChevronRight className="w-4 h-4" />
            {post.categories[0] && (
              <>
                <Link
                  to={`/blog/category/${post.categories[0].slug}`}
                  className="hover:text-foreground transition-colors"
                >
                  {post.categories[0].name}
                </Link>
                <ChevronRight className="w-4 h-4" />
              </>
            )}
            <span className="text-foreground font-medium truncate max-w-[200px]">
              {post.title}
            </span>
          </nav>
        </div>
      </div>

      {/* Featured Image */}
      {post.featured_image_url && (
        <div className="relative h-64 md:h-96 overflow-hidden">
          <img
            src={imageUrl}
            alt={post.title}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" />
        </div>
      )}

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 md:py-12">
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Main Column */}
          <div className="lg:col-span-3">
            {/* Header */}
            <header className="mb-8">
              {/* Categories */}
              {post.categories.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {post.categories.map((category) => (
                    <Link
                      key={category.id}
                      to={`/blog/category/${category.slug}`}
                      className="text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                    >
                      {category.name}
                    </Link>
                  ))}
                </div>
              )}

              {/* Title */}
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4">
                {post.title}
              </h1>

              {/* Meta */}
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
                {/* Author */}
                {post.author && (
                  <div className="flex items-center gap-2">
                    {post.author.avatar_url ? (
                      <img
                        src={post.author.avatar_url}
                        alt={post.author.name}
                        className="w-8 h-8 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                        <User className="w-4 h-4" />
                      </div>
                    )}
                    <span className="font-medium text-foreground">
                      {post.author.name}
                    </span>
                  </div>
                )}

                {/* Date */}
                {post.published_at && (
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    <span>{formatDate(post.published_at)}</span>
                  </div>
                )}

                {/* Reading Time */}
                {post.reading_time_minutes && (
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{post.reading_time_minutes} min read</span>
                  </div>
                )}
              </div>

              {/* Social Share */}
              <div className="mt-4 pt-4 border-t">
                <SocialShare url={pageUrl} title={post.title} />
              </div>
            </header>

            {/* Content */}
            <article className="mb-8">
              <MarkdownRenderer
                content={content}
                onHeadingsExtracted={handleHeadingsExtracted}
              />
            </article>

            {/* CTA Widget */}
            <BlogCTAWidget variant="banner" />

            {/* Author Bio */}
            {post.author && <AuthorBio author={post.author} />}

            {/* Tags */}
            {post.tags.length > 0 && (
              <div className="py-6 border-t">
                <h3 className="text-sm font-semibold mb-3">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {post.tags.map((tag) => (
                    <Link
                      key={tag.id}
                      to={`/blog/tag/${tag.slug}`}
                      className="px-3 py-1.5 text-sm bg-muted hover:bg-muted/80 rounded-full transition-colors"
                    >
                      {tag.name}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Related Posts */}
            <RelatedPosts postId={post.id} categories={post.categories} />

            {/* Navigation */}
            <div className="flex items-center justify-between pt-8 border-t">
              <Link to="/blog">
                <Button variant="outline">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  All Articles
                </Button>
              </Link>
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-24 space-y-6">
              {/* Table of Contents */}
              <TableOfContents headings={headings} />

              {/* CTA Widget */}
              <BlogCTAWidget />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BlogPostPage;
