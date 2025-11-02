/**
 * Main App component with routing
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/Layout';
import { HomePage } from './pages/Home';
import { ClaimFormPage } from './pages/ClaimForm';
import { StatusPage } from './pages/Status';
import { SuccessPage } from './pages/Success';
import { AuthPage } from './pages/Auth';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/claim" element={<ClaimFormPage />} />
          <Route path="/status" element={<StatusPage />} />
          <Route path="/success" element={<SuccessPage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        expand={false}
        richColors
        closeButton
        duration={4000}
      />
    </BrowserRouter>
  );
}

export default App;
