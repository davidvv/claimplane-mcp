import { Routes, Route } from 'react-router-dom';
import Layout from '@/components/Layout';
import Home from '@/pages/Home';
import ClaimWizard from '@/pages/ClaimForm/ClaimWizard';
import Status from '@/pages/Status';
import Success from '@/pages/Success';
import Auth from '@/pages/Auth';
import NotFound from '@/pages/NotFound';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/claim/*" element={<ClaimWizard />} />
        <Route path="/status" element={<Status />} />
        <Route path="/success/:claimId" element={<Success />} />
        <Route path="/auth" element={<Auth />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}