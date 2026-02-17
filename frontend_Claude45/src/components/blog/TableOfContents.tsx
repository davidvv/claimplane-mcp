/**
 * Table of Contents Component
 * Auto-generated from markdown headings with scroll tracking
 */

import { useState, useEffect, useRef } from 'react';
import { ChevronDown, ChevronRight, Menu } from 'lucide-react';
import type { HeadingItem } from './MarkdownRenderer';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';

interface TableOfContentsProps {
  headings: HeadingItem[];
  className?: string;
}

export function TableOfContents({ headings, className }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Track which heading is currently in view
  useEffect(() => {
    if (headings.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        // Find the first heading that's visible
        const visibleHeadings = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        
        if (visibleHeadings.length > 0) {
          setActiveId(visibleHeadings[0].target.id);
        }
      },
      {
        rootMargin: '-80px 0px -70% 0px',
        threshold: 0,
      }
    );

    headings.forEach(({ id }) => {
      const element = document.getElementById(id);
      if (element) {
        observer.observe(element);
      }
    });

    return () => observer.disconnect();
  }, [headings]);

  // Smooth scroll to heading
  const scrollToHeading = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setActiveId(id);
      setIsMobileOpen(false);
    }
  };

  // Filter to only show H2 and H3
  const filteredHeadings = headings.filter((h) => h.level <= 3);

  if (filteredHeadings.length === 0) {
    return null;
  }

  return (
    <>
      {/* Mobile Toggle */}
      <div className="lg:hidden mb-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="w-full flex items-center justify-between"
        >
          <span className="flex items-center gap-2">
            <Menu className="w-4 h-4" />
            Table of Contents
          </span>
          <ChevronDown
            className={cn(
              'w-4 h-4 transition-transform',
              isMobileOpen && 'rotate-180'
            )}
          />
        </Button>
      </div>

      {/* TOC Content */}
      <nav
        className={cn(
          'bg-card border rounded-lg',
          className,
          // Mobile: show/hide based on state
          isMobileOpen ? 'block' : 'hidden lg:block'
        )}
      >
        <div className="p-4">
          {/* Header */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="hidden lg:flex items-center justify-between w-full text-sm font-semibold mb-3 hover:text-primary transition-colors"
          >
            <span>On This Page</span>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>

          {/* Desktop header (non-collapsible on mobile) */}
          <div className="lg:hidden text-sm font-semibold mb-3">
            On This Page
          </div>

          {/* Links */}
          {isExpanded && (
            <ul className="space-y-1">
              {filteredHeadings.map((heading) => (
                <li key={heading.id}>
                  <button
                    onClick={() => scrollToHeading(heading.id)}
                    className={cn(
                      'w-full text-left text-sm py-1.5 px-2 rounded transition-colors',
                      heading.level === 2 && 'font-medium',
                      heading.level === 3 && 'pl-6 text-muted-foreground',
                      activeId === heading.id
                        ? 'bg-primary/10 text-primary font-medium'
                        : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                    )}
                  >
                    {heading.text}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Progress indicator */}
        <div className="h-1 bg-muted rounded-b-lg overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{
              width: `${
                activeId
                  ? ((filteredHeadings.findIndex((h) => h.id === activeId) + 1) /
                      filteredHeadings.length) *
                    100
                  : 0
              }%`,
            }}
          />
        </div>
      </nav>
    </>
  );
}

export default TableOfContents;
