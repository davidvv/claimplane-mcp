/**
 * Main application layout with navigation
 */

import { Link, useLocation } from 'react-router-dom';
import { Plane } from 'lucide-react';
import { DarkModeToggle } from './DarkModeToggle';
import { cn } from '@/lib/utils';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 font-bold text-xl">
            <div className="p-2 bg-primary rounded-lg">
              <Plane className="w-5 h-5 text-white" />
            </div>
            <span>EasyAirClaim</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link
              to="/"
              className={cn(
                'text-sm font-medium transition-colors hover:text-primary',
                isActive('/') ? 'text-foreground' : 'text-muted-foreground'
              )}
            >
              Home
            </Link>
            <Link
              to="/claim/new"
              className={cn(
                'text-sm font-medium transition-colors hover:text-primary',
                isActive('/claim/new') ? 'text-foreground' : 'text-muted-foreground'
              )}
            >
              File Claim
            </Link>
            <Link
              to="/status"
              className={cn(
                'text-sm font-medium transition-colors hover:text-primary',
                isActive('/status') ? 'text-foreground' : 'text-muted-foreground'
              )}
            >
              Check Status
            </Link>
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <DarkModeToggle />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t py-6 md:py-8">
        <div className="container">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Plane className="w-4 h-4" />
              <span>&copy; 2025 EasyAirClaim. All rights reserved.</span>
            </div>

            <div className="flex gap-6 text-sm text-muted-foreground">
              <a href="#" className="hover:text-foreground transition-colors">
                Privacy Policy
              </a>
              <a href="#" className="hover:text-foreground transition-colors">
                Terms of Service
              </a>
              <a href="#" className="hover:text-foreground transition-colors">
                Contact
              </a>
            </div>
          </div>

          {/* Trust badges */}
          <div className="mt-6 pt-6 border-t">
            <div className="flex flex-wrap justify-center gap-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-2 px-4 py-2 border rounded-lg">
                <span className="font-semibold">GDPR</span>
                <span>Compliant</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 border rounded-lg">
                <span className="font-semibold">256-bit</span>
                <span>SSL Encrypted</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 border rounded-lg">
                <span className="font-semibold">EU261</span>
                <span>Certified</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
