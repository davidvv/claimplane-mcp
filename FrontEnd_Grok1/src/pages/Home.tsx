import { Link } from 'react-router-dom'

const Home = () => {
  return (
    <div className="text-center">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-6">
          Welcome to EasyAirClaim Portal
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Get the flight compensation you deserve for delayed, cancelled, or disrupted flights
          across Europe, USA, and Canada.
        </p>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="card">
            <div className="text-center">
              <div className="text-3xl mb-4">✈️</div>
              <h3 className="text-lg font-semibold mb-2">Check Flight Status</h3>
              <p className="text-gray-600 mb-4">
                Verify your flight details and current status before proceeding with your claim.
              </p>
              <Link to="/flight-status" className="btn">
                Check Status
              </Link>
            </div>
          </div>

          <div className="card">
            <div className="text-center">
              <div className="text-3xl mb-4">💰</div>
              <h3 className="text-lg font-semibold mb-2">Check Eligibility</h3>
              <p className="text-gray-600 mb-4">
                Find out if your flight incident qualifies for compensation under EU261, DOT, or CTA regulations.
              </p>
              <Link to="/eligibility" className="btn">
                Check Eligibility
              </Link>
            </div>
          </div>

          <div className="card">
            <div className="text-center">
              <div className="text-3xl mb-4">📋</div>
              <h3 className="text-lg font-semibold mb-2">Submit Claim</h3>
              <p className="text-gray-600 mb-4">
                Submit your compensation claim with all required documents and information.
              </p>
              <Link to="/submit-claim" className="btn">
                Submit Claim
              </Link>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold text-blue-900 mb-4">
            Supported Regulations
          </h2>
          <div className="grid md:grid-cols-3 gap-4 text-left">
            <div>
              <h3 className="font-semibold text-blue-800">EU261</h3>
              <p className="text-blue-700 text-sm">
                European Union passenger rights regulation for flights departing from or arriving in EU airports.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-blue-800">DOT</h3>
              <p className="text-blue-700 text-sm">
                US Department of Transportation rules for domestic and international flights to/from the USA.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-blue-800">CTA</h3>
              <p className="text-blue-700 text-sm">
                Canadian Transportation Agency regulations for flights to/from Canada.
              </p>
            </div>
          </div>
        </div>

        <div className="text-center">
          <Link to="/claim-status" className="btn btn-secondary">
            Check Existing Claim Status
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Home