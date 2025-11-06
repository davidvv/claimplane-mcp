/**
 * Main application layout with navigation
 */

import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Plane, LogIn, UserPlus, LogOut, User } from 'lucide-react';
import { DarkModeToggle } from './DarkModeToggle';
import { Button } from './ui/Button';
import { cn } from '@/lib/utils';
import { isAuthenticated, getStoredUserInfo, logout } from '@/services/auth';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const authenticated = isAuthenticated();
  const userInfo = getStoredUserInfo();

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
      // Clear local storage anyway
      navigate('/');
    }
  };

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
            {authenticated ? (
              <>
                <div className="hidden sm:flex items-center gap-2 px-3 py-2 text-sm">
                  <User className="w-4 h-4" />
                  <span>{userInfo.name || userInfo.email}</span>
                </div>
                <Button variant="ghost" size="sm" onClick={handleLogout}>
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Link to="/auth">
                  <Button variant="ghost" size="sm" className="hidden sm:flex">
                    <LogIn className="w-4 h-4 mr-2" />
                    Login
                  </Button>
                </Link>
                <Link to="/auth?mode=register">
                  <Button size="sm" className="hidden sm:flex">
                    <UserPlus className="w-4 h-4 mr-2" />
                    Sign Up
                  </Button>
                </Link>
              </>
            )}
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
              <Link to="/privacy" className="hover:text-foreground transition-colors">
                Privacy Policy
              </Link>
              <Link to="/terms" className="hover:text-foreground transition-colors">
                Terms of Service
              </Link>
              <Link to="/contact" className="hover:text-foreground transition-colors">
                Contact
              </Link>
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
