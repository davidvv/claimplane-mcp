/**
 * Blog Category Page
 * Displays posts filtered by category
 */

import { useEffect, useState } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { ChevronRight, Home, FileText } from 'lucide-react';
import { blogService } from '@/services/blog';
import type { BlogPostSummary, BlogCategory, BlogPaginationMeta } from '@/types/blog';
import { BlogCard } from '@/components/blog/BlogCard';
import { BlogSidebar } from '@/components/blog/BlogSidebar';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Button } from '@/components/ui/Button';

export function BlogCategoryPage() {
  const { categorySlug } = useParams<{ categorySlug: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State
  const [posts, setPosts] = useState<BlogPostSummary[]>([]);
  const [category, setCategory] = useState<BlogCategory | null>(null);
  const [pagination, setPagination] = useState<BlogPaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Query params
  const page = parseInt(searchParams.get('page') || '1', 10);
  const language = searchParams.get('language') || undefined;

  // Fetch category and posts
  useEffect(() => {
    async function fetchCategoryPosts() {
      if (!categorySlug) return;
      
      try {
        setLoading(true);
        setError(null);
        
        // Fetch posts by category and categories list to find the current one
        const [postsResponse, categories] = await Promise.all([
          blogService.getPostsByCategory(categorySlug, {
            page,
            limit: 9,
            language,
          }),
          blogService.getCategories(),
        ]);

        // Find the current category
        const currentCategory = categories.find((c) => c.slug === categorySlug);
        
        if (!currentCategory) {
          setError('Category not found');
          return;
        }

        setCategory(currentCategory);
        setPosts(postsResponse.data);
        setPagination(postsResponse.pagination);
      } catch (err) {
        console.error('Error fetching category posts:', err);
        setError('Failed to load category posts. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchCategoryPosts();
  }, [categorySlug, page, language]);

  // Handle pagination
  const goToPage = (newPage: number) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', newPage.toString());
    setSearchParams(params);
  };

  // Handle language filter
  const handleLanguageChange = (newLanguage: string | null) => {
    const params = new URLSearchParams(searchParams);
    if (newLanguage) {
      params.set('language', newLanguage);
    } else {
      params.delete('language');
    }
    params.set('page', '1'); // Reset to first page
    setSearchParams(params);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
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
            {category && (
              <span className="text-foreground font-medium">{category.name}</span>
            )}
          </nav>
        </div>
      </div>

      {/* Header */}
      <div className="bg-primary/5 border-b">
        <div className="container mx-auto px-4 py-8 md:py-12">
          {loading ? (
            <div className="max-w-2xl">
              <div className="h-10 w-32 bg-muted animate-pulse rounded mb-4"></div>
              <div className="h-6 w-64 bg-muted animate-pulse rounded"></div>
            </div>
          ) : category ? (
            <div className="max-w-2xl">
              <h1 className="text-4xl md:text-5xl font-bold mb-2">{category.name}</h1>
              {category.description && (
                <p className="text-lg text-muted-foreground">{category.description}</p>
              )}
              <p className="text-sm text-muted-foreground mt-2">
                {pagination?.total || 0} {pagination?.total === 1 ? 'article' : 'articles'}
              </p>
            </div>
          ) : null}
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 md:py-12">
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Posts Grid */}
          <div className="lg:col-span-3">
            {/* Filters */}
            {posts.length > 0 && (
              <div className="flex flex-wrap items-center gap-4 mb-8 pb-4 border-b">
                <span className="text-sm text-muted-foreground">Filter:</span>
                <div className="flex items-center gap-2">
                  <Button
                    variant={!language ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleLanguageChange(null)}
                  >
                    All
                  </Button>
                  <Button
                    variant={language === 'en' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleLanguageChange('en')}
                  >
                    English
                  </Button>
                  <Button
                    variant={language === 'de' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleLanguageChange('de')}
                  >
                    Deutsch
                  </Button>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="flex justify-center py-16">
                <LoadingSpinner className="py-8" />
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="text-center py-16">
                <FileText className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
                <h3 className="text-xl font-semibold mb-2">{error}</h3>
                <Link to="/blog">
                  <Button variant="outline">Back to Blog</Button>
                </Link>
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && posts.length === 0 && (
              <div className="text-center py-16">
                <FileText className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
                <h3 className="text-xl font-semibold mb-2">No posts in this category</h3>
                <p className="text-muted-foreground mb-4">
                  There are no articles in "{category?.name}" yet.
                </p>
                <Link to="/blog">
                  <Button>Browse All Articles</Button>
                </Link>
              </div>
            )}

            {/* Posts Grid */}
            {!loading && !error && posts.length > 0 && (
              <>
                {/* Featured Post (first one on page 1) */}
                {page === 1 && posts[0] && (
                  <div className="mb-8">
                    <BlogCard post={posts[0]} featured />
                  </div>
                )}

                {/* Regular Posts Grid */}
                <div className="grid md:grid-cols-2 gap-6">
                  {(page === 1 ? posts.slice(1) : posts).map((post) => (
                    <BlogCard key={post.id} post={post} />
                  ))}
                </div>

                {/* Pagination */}
                {pagination && pagination.total_pages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-12">
                    <Button
                      variant="outline"
                      size="icon"
                      disabled={!pagination.has_prev}
                      onClick={() => goToPage(page - 1)}
                    >
                      &larr;
                    </Button>
                    
                    <span className="text-sm text-muted-foreground">
                      Page {page} of {pagination.total_pages}
                    </span>

                    <Button
                      variant="outline"
                      size="icon"
                      disabled={!pagination.has_next}
                      onClick={() => goToPage(page + 1)}
                    >
                      &rarr;
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-24">
              <BlogSidebar />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BlogCategoryPage;
