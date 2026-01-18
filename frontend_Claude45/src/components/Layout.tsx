/**
 * Main application layout with navigation
 */

import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Plane, LogIn, LogOut, User, FileText, Settings, ChevronDown, LayoutDashboard } from 'lucide-react';
import { DarkModeToggle } from './DarkModeToggle';
import { MobileNav } from './MobileNav';
import { Button } from './ui/Button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/DropdownMenu';
import { cn } from '@/lib/utils';
import { isAuthenticated, getStoredUserInfo, logout } from '@/services/auth';

/**
 * Get user role from localStorage (stored during login)
 * Note: JWT tokens are in HTTP-only cookies, user info is in localStorage for UI
 */
function getUserRole(): string | null {
  return localStorage.getItem('user_role');
}

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const authenticated = isAuthenticated();
  const userInfo = getStoredUserInfo();
  const userRole = getUserRole();
  const isAdmin = userRole === 'admin' || userRole === 'superadmin';

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
            <span>ClaimPlane</span>
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
            <Link
              to="/about"
              className={cn(
                'text-sm font-medium transition-colors hover:text-primary',
                isActive('/about') ? 'text-foreground' : 'text-muted-foreground'
              )}
            >
              About Us
            </Link>
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {authenticated ? (
              <>
                {/* Desktop User Menu */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="gap-2 hidden md:flex">
                      <User className="w-4 h-4" />
                      <span className="hidden sm:inline">{userInfo.name || userInfo.email}</span>
                      <ChevronDown className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuLabel>
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">{userInfo.name || 'My Account'}</p>
                        <p className="text-xs leading-none text-muted-foreground">
                          {userInfo.email}
                        </p>
                        {isAdmin && (
                          <p className="text-xs leading-none text-primary font-semibold mt-1">
                            {userRole === 'superadmin' ? 'Super Admin' : 'Admin'}
                          </p>
                        )}
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {isAdmin ? (
                      <>
                        <DropdownMenuItem onClick={() => navigate('/panel/dashboard')}>
                          <LayoutDashboard className="w-4 h-4 mr-2" />
                          Admin Dashboard
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => navigate('/my-claims')}>
                          <FileText className="w-4 h-4 mr-2" />
                          My Claims (Customer View)
                        </DropdownMenuItem>
                      </>
                    ) : (
                      <DropdownMenuItem onClick={() => navigate('/my-claims')}>
                        <FileText className="w-4 h-4 mr-2" />
                        My Claims
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuItem onClick={() => navigate('/account/settings')}>
                      <Settings className="w-4 h-4 mr-2" />
                      Account Settings
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout}>
                      <LogOut className="w-4 h-4 mr-2" />
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <>
                {/* Desktop Auth Button */}
                <Link to="/auth" className="hidden md:block">
                  <Button size="sm">
                    <LogIn className="w-4 h-4 mr-2" />
                    Login
                  </Button>
                </Link>
              </>
            )}
            <DarkModeToggle />
            {/* Mobile Navigation Menu */}
            <MobileNav userRole={userRole} />
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
              <span>&copy; 2025 ClaimPlane. All rights reserved.</span>
            </div>

            <div className="flex flex-wrap gap-4 sm:gap-6 text-sm text-muted-foreground">
              <Link to="/privacy" className="hover:text-foreground transition-colors">
                Privacy Policy
              </Link>
              <Link to="/terms" className="hover:text-foreground transition-colors">
                Terms and Conditions
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
