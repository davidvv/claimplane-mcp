import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { jwtPayloadSchema, JWTPayload } from '../schemas';
import { toast } from 'sonner';

interface AuthContextType {
  isAuthenticated: boolean;
  user: JWTPayload | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<JWTPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on mount
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      const mockToken = import.meta.env.VITE_MOCK_JWT;
      
      if (token || mockToken) {
        const payload = parseJWT(token || mockToken);
        if (payload && !isTokenExpired(payload)) {
          setUser(payload);
          setIsAuthenticated(true);
        } else {
          // Token expired or invalid
          localStorage.removeItem('jwt_token');
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const parseJWT = (token: string): JWTPayload | null => {
    try {
      // JWT tokens have 3 parts separated by dots
      const parts = token.split('.');
      if (parts.length !== 3) {
        throw new Error('Invalid JWT format');
      }

      // Decode the payload (second part)
      const payload = JSON.parse(atob(parts[1]));
      
      // Validate with Zod schema
      return jwtPayloadSchema.parse(payload);
    } catch (error) {
      console.error('Failed to parse JWT:', error);
      return null;
    }
  };

  const isTokenExpired = (payload: JWTPayload): boolean => {
    const now = Math.floor(Date.now() / 1000);
    return payload.exp < now;
  };

  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    
    try {
      // Mock authentication - in real app, this would call an API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Validate credentials (mock validation)
      if (!email || !password) {
        throw new Error('Email and password are required');
      }
      
      if (password.length < 6) {
        throw new Error('Password must be at least 6 characters');
      }
      
      // Generate mock JWT token
      const mockPayload: JWTPayload = {
        sub: '123e4567-e89b-12d3-a456-426614174000',
        email,
        exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60), // 24 hours
        iat: Math.floor(Date.now() / 1000),
      };
      
      // Create mock JWT token
      const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
      const payload = btoa(JSON.stringify(mockPayload));
      const signature = btoa('mock-signature');
      const mockToken = `${header}.${payload}.${signature}`;
      
      // Store token
      localStorage.setItem('jwt_token', mockToken);
      
      // Update state
      setUser(mockPayload);
      setIsAuthenticated(true);
      
      toast.success('Login successful!');
      
      // Track analytics
      if (window.analytics) {
        window.analytics.track('login_success', { email });
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      toast.error(errorMessage);
      
      // Track analytics
      if (window.analytics) {
        window.analytics.track('login_failed', { email, error: errorMessage });
      }
      
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('jwt_token');
    setUser(null);
    setIsAuthenticated(false);
    toast.success('Logged out successfully');
    
    // Track analytics
    if (window.analytics) {
      window.analytics.track('logout');
    }
  };

  const value = {
    isAuthenticated,
    user,
    login,
    logout,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Extend Window interface for analytics
declare global {
  interface Window {
    analytics?: {
      track: (event: string, properties?: Record<string, any>) => void;
    };
  }
}