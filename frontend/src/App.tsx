/**
 * Main App component with routing
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/Layout';

// Pages
import { Home } from './pages/Home';
import { ClaimFormPage } from './pages/ClaimForm/ClaimFormPage';
import { Status } from './pages/Status';
import { Success } from './pages/Success';
import { Auth } from './pages/Auth';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/claim/new" element={<ClaimFormPage />} />
          <Route path="/claim/success" element={<Success />} />
          <Route path="/status" element={<Status />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>

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
