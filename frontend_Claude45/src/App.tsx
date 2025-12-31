/**
 * Main App component with routing
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';

// Pages
import { Home } from './pages/Home';
import { ClaimFormPage } from './pages/ClaimForm/ClaimFormPage';
import { Status } from './pages/Status';
import { Success } from './pages/Success';
import { Auth } from './pages/Auth';
import { MagicLinkPage } from './pages/Auth/MagicLinkPage';
import { MyClaims } from './pages/MyClaims';
import { AccountSettings } from './pages/AccountSettings';
import { TermsAndConditions } from './pages/TermsAndConditions';

// Admin Pages
import { AdminDashboard } from './pages/Admin/AdminDashboard';
import { ClaimDetailPage } from './pages/Admin/ClaimDetailPage';

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Layout>
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

            {/* Admin Panel Routes (non-obvious path for security) */}
            <Route path="/panel/dashboard" element={<AdminDashboard />} />
            <Route path="/panel/claims/:claimId" element={<ClaimDetailPage />} />

            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </ErrorBoundary>

      {/* Toast notifications */}
      <Toaster
        position="top-right"
        expand={false}
        richColors
        closeButton
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
