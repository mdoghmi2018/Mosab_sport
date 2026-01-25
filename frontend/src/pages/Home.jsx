import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Mosab Sport Platform
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Book courts, manage matches, and generate reports
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              to="/login"
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
            >
              Get Started
            </Link>
            <Link
              to="/venues"
              className="bg-white text-blue-600 px-6 py-3 rounded-lg border border-blue-600 hover:bg-blue-50 transition"
            >
              Browse Venues
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

