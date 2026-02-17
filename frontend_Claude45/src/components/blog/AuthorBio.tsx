/**
 * Author Bio Component
 * Displays author information at the bottom of blog posts
 */

import { Link } from 'react-router-dom';
import { User, Twitter, Linkedin, Mail, Globe } from 'lucide-react';
import type { BlogAuthor } from '@/types/blog';
import { cn } from '@/lib/utils';

interface AuthorBioProps {
  author: BlogAuthor;
  className?: string;
}

/**
 * Get social link icon by platform name
 */
function getSocialIcon(platform: string) {
  switch (platform.toLowerCase()) {
    case 'twitter':
    case 'x':
      return <Twitter className="w-4 h-4" />;
    case 'linkedin':
      return <Linkedin className="w-4 h-4" />;
    case 'email':
    case 'mail':
      return <Mail className="w-4 h-4" />;
    case 'website':
    case 'blog':
      return <Globe className="w-4 h-4" />;
    default:
      return <Globe className="w-4 h-4" />;
  }
}

export function AuthorBio({ author, className }: AuthorBioProps) {
  // Parse social links
  const socialLinks = author.social_links || {};
  const socialEntries = Object.entries(socialLinks).filter(([_, url]) => url);

  return (
    <div
      className={cn(
        'bg-card border rounded-lg p-6 my-8',
        className
      )}
    >
      <div className="flex flex-col sm:flex-row gap-4 sm:gap-6">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {author.avatar_url ? (
            <img
              src={author.avatar_url}
              alt={author.name}
              className="w-16 h-16 sm:w-20 sm:h-20 rounded-full object-cover border-2 border-primary/20"
            />
          ) : (
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-primary/10 flex items-center justify-center border-2 border-primary/20">
              <User className="w-8 h-8 text-primary" />
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Name and title */}
          <div className="mb-2">
            <h3 className="text-lg font-semibold">{author.name}</h3>
            <p className="text-sm text-muted-foreground">Author</p>
          </div>

          {/* Bio */}
          {author.bio && (
            <p className="text-sm text-muted-foreground mb-3 line-clamp-3">
              {author.bio}
            </p>
          )}

          {/* Social Links */}
          {socialEntries.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {socialEntries.map(([platform, url]) => (
                <a
                  key={platform}
                  href={url as string}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs bg-muted hover:bg-muted/80 rounded-full transition-colors"
                  title={platform}
                >
                  {getSocialIcon(platform)}
                  <span className="capitalize">{platform}</span>
                </a>
              ))}
            </div>
          )}

          {/* Email */}
          {author.email && (
            <a
              href={`mailto:${author.email}`}
              className="inline-flex items-center gap-1.5 mt-2 text-sm text-muted-foreground hover:text-primary transition-colors"
            >
              <Mail className="w-4 h-4" />
              {author.email}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

export default AuthorBio;
