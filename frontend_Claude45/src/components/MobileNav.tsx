/**
 * Mobile Navigation Menu
 * Hamburger menu for mobile devices
 */

import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Menu, X, Home, FileText, Search, LogIn, User, LogOut, Settings, LayoutDashboard, Info } from 'lucide-react';
import { Button } from './ui/Button';
import { isAuthenticated, getStoredUserInfo, logout } from '@/services/auth';
import { cn } from '@/lib/utils';

interface MobileNavProps {
  userRole: string | null;
}

export function MobileNav({ userRole }: MobileNavProps) {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const authenticated = isAuthenticated();
  const userInfo = getStoredUserInfo();
  const isAdmin = userRole === 'admin' || userRole === 'superadmin';

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = async () => {
    try {
      await logout();
      setIsOpen(false);
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/');
    }
  };

  const handleNavClick = (path: string) => {
    setIsOpen(false);
    navigate(path);
  };

  return (
    <div className="md:hidden">
      {/* Hamburger Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="p-2"
        aria-label="Toggle menu"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </Button>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu Panel */}
          <div className="fixed top-16 left-0 right-0 bg-background border-b shadow-lg z-50 max-h-[calc(100vh-4rem)] overflow-y-auto">
            <div className="container py-4">
              {/* User Info (if authenticated) */}
              {authenticated && (
                <div className="pb-4 mb-4 border-b">
                  <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <User className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {userInfo.name || 'My Account'}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {userInfo.email}
                      </p>
                      {isAdmin && (
                        <p className="text-xs text-primary font-semibold mt-1">
                          {userRole === 'superadmin' ? 'Super Admin' : 'Admin'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Navigation Links */}
              <nav className="space-y-1">
                <Link
                  to="/"
                  onClick={() => setIsOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-colors',
                    isActive('/')
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                >
                  <Home className="w-5 h-5" />
                  Home
                </Link>

                <Link
                  to="/claim/new"
                  onClick={() => setIsOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-colors',
                    isActive('/claim/new')
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                >
                  <FileText className="w-5 h-5" />
                  File Claim
                </Link>

                <Link
                  to="/status"
                  onClick={() => setIsOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-colors',
                    isActive('/status')
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                >
                  <Search className="w-5 h-5" />
                  Check Status
                </Link>

                <Link
                  to="/about"
                  onClick={() => setIsOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-colors',
                    isActive('/about')
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                >
                  <Info className="w-5 h-5" />
                  About Us
                </Link>

                {authenticated && (
                  <>
                    <div className="my-2 border-t" />

                    {isAdmin && (
                      <button
                        onClick={() => handleNavClick('/panel/dashboard')}
                        className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium hover:bg-muted transition-colors"
                      >
                        <LayoutDashboard className="w-5 h-5" />
                        Admin Dashboard
                      </button>
                    )}

                    <button
                      onClick={() => handleNavClick('/my-claims')}
                      className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium hover:bg-muted transition-colors"
                    >
                      <FileText className="w-5 h-5" />
                      {isAdmin ? 'My Claims (Customer View)' : 'My Claims'}
                    </button>

                    <button
                      onClick={() => handleNavClick('/account/settings')}
                      className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium hover:bg-muted transition-colors"
                    >
                      <Settings className="w-5 h-5" />
                      Account Settings
                    </button>

                    <div className="my-2 border-t" />

                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors"
                    >
                      <LogOut className="w-5 h-5" />
                      Logout
                    </button>
                  </>
                )}

                {!authenticated && (
                  <>
                    <div className="my-2 border-t" />

                    <button
                      onClick={() => handleNavClick('/auth')}
                      className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                    >
                      <LogIn className="w-5 h-5" />
                      Login
                    </button>
                  </>
                )}
              </nav>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
