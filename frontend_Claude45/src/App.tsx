/**
 * Main App component with routing
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { lazy, Suspense } from 'react';
import { Layout } from './components/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useAuthSync } from './hooks/useAuthSync';
import { ScrollToTop } from './components/ScrollToTop';

// Lazy load Pages
const Home = lazy(() => import('./pages/Home').then(m => ({ default: m.Home })));
const ClaimFormPage = lazy(() => import('./pages/ClaimForm/ClaimFormPage').then(m => ({ default: m.ClaimFormPage })));
const Status = lazy(() => import('./pages/Status').then(m => ({ default: m.Status })));
const Success = lazy(() => import('./pages/Success').then(m => ({ default: m.Success })));
const Auth = lazy(() => import('./pages/Auth').then(m => ({ default: m.Auth })));
const MagicLinkPage = lazy(() => import('./pages/Auth/MagicLinkPage').then(m => ({ default: m.MagicLinkPage })));
const MyClaims = lazy(() => import('./pages/MyClaims').then(m => ({ default: m.MyClaims })));
const AccountSettings = lazy(() => import('./pages/AccountSettings').then(m => ({ default: m.AccountSettings })));
const TermsAndConditions = lazy(() => import('./pages/TermsAndConditions').then(m => ({ default: m.TermsAndConditions })));
const PrivacyPolicy = lazy(() => import('./pages/PrivacyPolicy').then(m => ({ default: m.PrivacyPolicy })));
const About = lazy(() => import('./pages/About').then(m => ({ default: m.About })));
const Contact = lazy(() => import('./pages/Contact').then(m => ({ default: m.Contact })));

// Lazy load Admin Pages
const AdminDashboard = lazy(() => import('./pages/Admin/AdminDashboard').then(m => ({ default: m.AdminDashboard })));
const ClaimDetailPage = lazy(() => import('./pages/Admin/ClaimDetailPage').then(m => ({ default: m.ClaimDetailPage })));
const DeletionRequests = lazy(() => import('./pages/Admin/DeletionRequests').then(m => ({ default: m.DeletionRequests })));

// Loading component for Suspense
const PageLoader = () => (
  <div className="min-h-[60vh] flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
  </div>
);

function App() {
  // Validate authentication state on app load
  // This prevents stale sessionStorage from showing user as logged in when cookies expired
  const { isValidating } = useAuthSync();

  // Show minimal loading state while validating session
  // This prevents flash of wrong UI state on page load
  if (isValidating) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <ScrollToTop />
      <ErrorBoundary>
        <Layout>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/claim/new" element={<ClaimFormPage />} />
              <Route path="/claim/success" element={<Success />} />
              <Route path="/status" element={<Status />} />
              <Route path="/my-claims" element={<MyClaims />} />
              <Route path="/auth" element={<Auth />} />
              <Route path="/auth/magic-link" element={<MagicLinkPage />} />
              <Route path="/account/settings" element={<AccountSettings />} />
              <Route path="/terms" element={<TermsAndConditions />} />
              <Route path="/privacy" element={<PrivacyPolicy />} />
              <Route path="/about" element={<About />} />
              <Route path="/contact" element={<Contact />} />

              {/* Admin Panel Routes (non-obvious path for security) */}
              <Route path="/panel/dashboard" element={<AdminDashboard />} />
              <Route path="/panel/claims/:claimId" element={<ClaimDetailPage />} />
              <Route path="/panel/deletion-requests" element={<DeletionRequests />} />

              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </Layout>
      </ErrorBoundary>

      {/* Toast notifications */}
      <Toaster
        position="top-right"
        expand={false}
        richColors
        closeButton
        duration={4000}
        gap={8}
        offset={16}
        theme="light"
        visibleToasts={3}
        className="toast-container"
        style={{
          zIndex: 9999,
        }}
      />
    </BrowserRouter>
  );
}

/**
 * 404 Not Found page
 */
function NotFound() {
  return (
    <div className="py-20">
      <div className="container text-center">
        <h1 className="text-6xl font-bold mb-4">404</h1>
        <p className="text-xl text-muted-foreground mb-8">
          Page not found
        </p>
        <a
          href="/"
          className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
        >
          Go Home
        </a>
      </div>
    </div>
  );
}

export default App;
