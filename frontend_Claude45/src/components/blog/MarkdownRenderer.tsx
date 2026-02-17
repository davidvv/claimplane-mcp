/**
 * Markdown Renderer Component
 * Renders markdown content to HTML with styling and features
 */

import { useMemo, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  onHeadingsExtracted?: (headings: HeadingItem[]) => void;
}

export interface HeadingItem {
  id: string;
  text: string;
  level: number;
}

/**
 * Simple markdown to HTML converter
 * Handles: headings, paragraphs, lists, links, images, code, blockquotes, tables
 */
function parseMarkdown(markdown: string): string {
  let html = markdown;

  // Escape HTML entities first (but preserve our markdown)
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks (must be before inline code)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre class="bg-muted rounded-lg p-4 overflow-x-auto my-4"><code class="language-${lang || 'text'}">${code.trim()}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="bg-muted px-1.5 py-0.5 rounded text-sm font-mono">$1</code>');

  // Headings with anchor IDs
  html = html.replace(/^#### (.+)$/gm, (_, text) => {
    const id = text.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    return `<h4 id="${id}" class="text-lg font-semibold mt-6 mb-3 scroll-mt-20">${text}</h4>`;
  });
  html = html.replace(/^### (.+)$/gm, (_, text) => {
    const id = text.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    return `<h3 id="${id}" class="text-xl font-semibold mt-8 mb-4 scroll-mt-20">${text}</h3>`;
  });
  html = html.replace(/^## (.+)$/gm, (_, text) => {
    const id = text.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    return `<h2 id="${id}" class="text-2xl font-bold mt-10 mb-4 scroll-mt-20 border-b pb-2">${text}</h2>`;
  });
  html = html.replace(/^# (.+)$/gm, (_, text) => {
    const id = text.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    return `<h1 id="${id}" class="text-3xl font-bold mt-8 mb-4 scroll-mt-20">${text}</h1>`;
  });

  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold">$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em class="italic">$1</em>');
  html = html.replace(/__(.+?)__/g, '<strong class="font-semibold">$1</strong>');
  html = html.replace(/_(.+?)_/g, '<em class="italic">$1</em>');

  // Links - distinguish internal vs external
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, text, url) => {
    const isExternal = url.startsWith('http://') || url.startsWith('https://');
    const isAnchor = url.startsWith('#');
    
    if (isAnchor) {
      return `<a href="${url}" class="text-primary hover:underline">${text}</a>`;
    } else if (isExternal) {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-primary hover:underline inline-flex items-center gap-1">${text}<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg></a>`;
    } else {
      // Internal link - will be handled by React Router
      return `<a href="${url}" class="text-primary hover:underline" data-internal-link>${text}</a>`;
    }
  });

  // Images with lazy loading
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, src) => {
    return `<img src="${src}" alt="${alt}" loading="lazy" class="rounded-lg my-6 max-w-full h-auto" />`;
  });

  // Blockquotes
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote class="border-l-4 border-primary/50 pl-4 py-2 my-4 bg-muted/50 italic text-muted-foreground">$1</blockquote>');

  // Horizontal rules
  html = html.replace(/^---$/gm, '<hr class="my-8 border-border" />');

  // Unordered lists
  html = html.replace(/^[\*\-] (.+)$/gm, '<li class="ml-6 list-disc">$1</li>');
  html = html.replace(/(<li.*<\/li>\n?)+/g, '<ul class="my-4 space-y-2">$&</ul>');

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li class="ml-6 list-decimal">$1</li>');

  // Tables (basic support)
  html = html.replace(/^\|(.+)\|$/gm, (_, content) => {
    const cells = content.split('|').map((c: string) => c.trim());
    const isHeader = cells.some((c: string) => /^[-:]+$/.test(c));
    
    if (isHeader) {
      return ''; // Skip separator row
    }
    
    const cellTags = cells.map((c: string) => `<td class="border px-4 py-2">${c}</td>`).join('');
    return `<tr>${cellTags}</tr>`;
  });
  html = html.replace(/(<tr>.*<\/tr>\n?)+/g, '<table class="my-4 w-full border-collapse border">$&</table>');

  // Paragraphs (must be last)
  // Only wrap lines that aren't already HTML tags
  html = html.split('\n\n').map(block => {
    block = block.trim();
    if (!block) return '';
    if (block.startsWith('<')) return block;
    return `<p class="my-4 leading-relaxed">${block}</p>`;
  }).join('\n');

  return html;
}

/**
 * Extract headings from markdown for table of contents
 */
function extractHeadings(markdown: string): HeadingItem[] {
  const headings: HeadingItem[] = [];
  const headingRegex = /^(#{1,4}) (.+)$/gm;
  let match;

  while ((match = headingRegex.exec(markdown)) !== null) {
    const level = match[1].length;
    const text = match[2];
    const id = text.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    
    headings.push({ id, text, level });
  }

  return headings;
}

export function MarkdownRenderer({ content, className, onHeadingsExtracted }: MarkdownRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Parse markdown to HTML
  const html = useMemo(() => parseMarkdown(content), [content]);

  // Extract headings for table of contents
  useEffect(() => {
    if (onHeadingsExtracted) {
      const headings = extractHeadings(content);
      onHeadingsExtracted(headings);
    }
  }, [content, onHeadingsExtracted]);

  // Handle internal links with React Router
  useEffect(() => {
    if (!containerRef.current) return;

    const handleLinkClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest('a[data-internal-link]');
      
      if (link) {
        e.preventDefault();
        const href = link.getAttribute('href');
        if (href) {
          window.history.pushState({}, '', href);
          window.dispatchEvent(new PopStateEvent('popstate'));
        }
      }
    };

    containerRef.current.addEventListener('click', handleLinkClick);
    return () => {
      containerRef.current?.removeEventListener('click', handleLinkClick);
    };
  }, [html]);

  // Handle anchor link smooth scrolling
  useEffect(() => {
    const handleAnchorClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest('a[href^="#"]');
      
      if (link) {
        e.preventDefault();
        const id = link.getAttribute('href')?.slice(1);
        if (id) {
          const element = document.getElementById(id);
          if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
          }
        }
      }
    };

    containerRef.current?.addEventListener('click', handleAnchorClick);
    return () => {
      containerRef.current?.removeEventListener('click', handleAnchorClick);
    };
  }, [html]);

  return (
    <div
      ref={containerRef}
      className={cn(
        'prose prose-lg max-w-none',
        // Custom prose styling
        'prose-headings:scroll-mt-20',
        'prose-a:text-primary prose-a:no-underline hover:prose-a:underline',
        'prose-img:rounded-lg prose-img:shadow-md',
        'prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded',
        'prose-pre:bg-muted prose-pre:border',
        'prose-blockquote:border-primary/50 prose-blockquote:bg-muted/50',
        className
      )}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

export default MarkdownRenderer;
