import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Login from './pages/Login'
import Venues from './pages/Venues'
import Bookings from './pages/Bookings'
import MatchConsole from './pages/MatchConsole'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/venues" element={<Venues />} />
          <Route path="/bookings" element={<Bookings />} />
          <Route path="/matches/:matchId/console" element={<MatchConsole />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App

