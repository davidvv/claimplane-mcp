/**
 * Blog List Page
 * Displays all blog posts with pagination and filtering
 */

import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, ChevronLeft, ChevronRight, FileText } from 'lucide-react';
import { blogService } from '@/services/blog';
import type { BlogPostSummary, BlogPaginationMeta } from '@/types/blog';
import { BlogCard } from '@/components/blog/BlogCard';
import { BlogSidebar } from '@/components/blog/BlogSidebar';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export function BlogList() {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State
  const [posts, setPosts] = useState<BlogPostSummary[]>([]);
  const [pagination, setPagination] = useState<BlogPaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Query params
  const page = parseInt(searchParams.get('page') || '1', 10);
  const language = searchParams.get('language') || undefined;
  const sortBy = searchParams.get('sort_by') || 'published_at';
  const sortOrder = searchParams.get('sort_order') || 'desc';

  // Fetch posts
  useEffect(() => {
    async function fetchPosts() {
      try {
        setLoading(true);
        setError(null);
        
        const response = await blogService.getPosts({
          page,
          limit: 9,
          language,
          sort_by: sortBy,
          sort_order: sortOrder,
        });

        setPosts(response.data);
        setPagination(response.pagination);
      } catch (err) {
        console.error('Error fetching blog posts:', err);
        setError('Failed to load blog posts. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchPosts();
  }, [page, language, sortBy, sortOrder]);

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.location.href = `/blog/search?q=${encodeURIComponent(searchQuery.trim())}`;
    }
  };

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

  // Handle sort change
  const handleSortChange = (newSortBy: string, newSortOrder: string) => {
    const params = new URLSearchParams(searchParams);
    params.set('sort_by', newSortBy);
    params.set('sort_order', newSortOrder);
    params.set('page', '1'); // Reset to first page
    setSearchParams(params);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Hero Section */}
      <div className="bg-primary/5 border-b">
        <div className="container mx-auto px-4 py-12 md:py-16">
          <div className="max-w-2xl mx-auto text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Flight Compensation Blog</h1>
            <p className="text-lg text-muted-foreground mb-8">
              Expert insights on EU261 compensation, flight delay claims, and passenger rights
            </p>
            
            {/* Search Form */}
            <form onSubmit={handleSearch} className="relative max-w-md mx-auto">
              <Input
                type="text"
                placeholder="Search articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pr-12 h-12"
              />
              <Button
                type="submit"
                variant="ghost"
                size="icon"
                className="absolute right-1 top-1/2 -translate-y-1/2"
              >
                <Search className="w-5 h-5" />
              </Button>
            </form>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 md:py-12">
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Posts Grid */}
          <div className="lg:col-span-3">
            {/* Filters */}
            <div className="flex flex-wrap items-center justify-between gap-4 mb-8 pb-4 border-b">
              {/* Language Filter */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Language:</span>
                <div className="flex gap-1">
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

              {/* Sort */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Sort:</span>
                <select
                  value={`${sortBy}-${sortOrder}`}
                  onChange={(e) => {
                    const [newSortBy, newSortOrder] = e.target.value.split('-');
                    handleSortChange(newSortBy, newSortOrder);
                  }}
                  className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                >
                  <option value="published_at-desc">Newest First</option>
                  <option value="published_at-asc">Oldest First</option>
                  <option value="title-asc">Title A-Z</option>
                  <option value="title-desc">Title Z-A</option>
                </select>
              </div>
            </div>

            {/* Loading State */}
            {loading && (
              <div className="flex justify-center py-16">
                <LoadingSpinner className="py-8" />
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="text-center py-16">
                <p className="text-red-500 mb-4">{error}</p>
                <Button onClick={() => window.location.reload()}>
                  Try Again
                </Button>
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && posts.length === 0 && (
              <div className="text-center py-16">
                <FileText className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
                <h3 className="text-xl font-semibold mb-2">No posts found</h3>
                <p className="text-muted-foreground">
                  We couldn't find any blog posts. Please check back later.
                </p>
              </div>
            )}

            {/* Posts Grid */}
            {!loading && !error && posts.length > 0 && (
              <>
                {/* Featured Post (first one) */}
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
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    
                    <div className="flex items-center gap-1">
                      {Array.from({ length: Math.min(5, pagination.total_pages) }, (_, i) => {
                        let pageNum: number;
                        if (pagination.total_pages <= 5) {
                          pageNum = i + 1;
                        } else if (page <= 3) {
                          pageNum = i + 1;
                        } else if (page >= pagination.total_pages - 2) {
                          pageNum = pagination.total_pages - 4 + i;
                        } else {
                          pageNum = page - 2 + i;
                        }
                        
                        return (
                          <Button
                            key={pageNum}
                            variant={page === pageNum ? 'default' : 'ghost'}
                            size="icon"
                            onClick={() => goToPage(pageNum)}
                          >
                            {pageNum}
                          </Button>
                        );
                      })}
                    </div>

                    <Button
                      variant="outline"
                      size="icon"
                      disabled={!pagination.has_next}
                      onClick={() => goToPage(page + 1)}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                )}

                {/* Results Count */}
                <p className="text-center text-sm text-muted-foreground mt-8">
                  Showing {(pagination?.page || 1) - 1 * (pagination?.limit || 9) + 1} to{' '}
                  {Math.min((pagination?.page || 1) * (pagination?.limit || 9), pagination?.total || 0)} of{' '}
                  {pagination?.total || 0} posts
                </p>
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

export default BlogList;
