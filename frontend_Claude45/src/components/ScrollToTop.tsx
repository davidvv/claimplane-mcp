/**
 * ScrollToTop component - Automatically scrolls to top on route changes
 * This ensures users always start at the top when navigating between pages
 */

import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    // Scroll to top whenever the route changes
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [pathname]);

  return null;
}
