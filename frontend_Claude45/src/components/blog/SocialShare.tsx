/**
 * Social Share Component
 * Social sharing buttons for blog posts
 */

import { useState } from 'react';
import { Share2, Copy, Check, Facebook, Twitter, Linkedin, Mail } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';

interface SocialShareProps {
  url: string;
  title: string;
  className?: string;
}

export function SocialShare({ url, title, className }: SocialShareProps) {
  const [copied, setCopied] = useState(false);

  const shareLinks = {
    twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
    linkedin: `https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`,
    email: `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(`Check out this article: ${url}`)}`,
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const shareNative = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title,
          url,
        });
      } catch (err) {
        // User cancelled or error
        console.log('Share cancelled');
      }
    }
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className="text-sm text-muted-foreground flex items-center gap-1">
        <Share2 className="w-4 h-4" />
        Share:
      </span>

      <div className="flex items-center gap-1">
        {/* Twitter/X */}
        <a
          href={shareLinks.twitter}
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 rounded-md hover:bg-muted transition-colors"
          title="Share on X (Twitter)"
        >
          <Twitter className="w-4 h-4" />
        </a>

        {/* Facebook */}
        <a
          href={shareLinks.facebook}
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 rounded-md hover:bg-muted transition-colors"
          title="Share on Facebook"
        >
          <Facebook className="w-4 h-4" />
        </a>

        {/* LinkedIn */}
        <a
          href={shareLinks.linkedin}
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 rounded-md hover:bg-muted transition-colors"
          title="Share on LinkedIn"
        >
          <Linkedin className="w-4 h-4" />
        </a>

        {/* Email */}
        <a
          href={shareLinks.email}
          className="p-2 rounded-md hover:bg-muted transition-colors"
          title="Share via Email"
        >
          <Mail className="w-4 h-4" />
        </a>

        {/* Copy Link */}
        <button
          onClick={copyToClipboard}
          className="p-2 rounded-md hover:bg-muted transition-colors"
          title="Copy link"
        >
          {copied ? (
            <Check className="w-4 h-4 text-green-500" />
          ) : (
            <Copy className="w-4 h-4" />
          )}
        </button>

        {/* Native Share (mobile) */}
        {navigator.share && (
          <Button
            variant="ghost"
            size="sm"
            onClick={shareNative}
            className="p-2"
          >
            <Share2 className="w-4 h-4" />
          </Button>
        )}
      </div>
    </div>
  );
}

export default SocialShare;
