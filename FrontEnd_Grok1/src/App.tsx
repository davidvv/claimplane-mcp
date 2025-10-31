import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import FlightStatus from './pages/FlightStatus'
import EligibilityCheck from './pages/EligibilityCheck'
import ClaimSubmission from './pages/ClaimSubmission'
import ClaimStatus from './pages/ClaimStatus'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/flight-status" element={<FlightStatus />} />
        <Route path="/eligibility" element={<EligibilityCheck />} />
        <Route path="/submit-claim" element={<ClaimSubmission />} />
        <Route path="/claim-status" element={<ClaimStatus />} />
      </Routes>
    </Layout>
  )
}

export default App