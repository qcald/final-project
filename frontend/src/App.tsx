import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import Navbar from './components/Navbar'
import AuthPage from './pages/AuthPage'
import Feed from './pages/Feed'
import Friends from './pages/Friends'
import InvitePage from './pages/InvitePage'
import MapPage from './pages/MapPage'

export default function App() {
  const { user, loading } = useAuth()
  if (loading) return null

  return (
    <>
      <Navbar />
      <main>
        {user ? (
          <Routes>
            <Route path="/" element={<MapPage />} />
            <Route path="/feed" element={<Feed />} />
            <Route path="/friends" element={<Friends />} />
            <Route path="/invite/:code" element={<InvitePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        ) : (
          <Routes>
            <Route path="/register" element={<AuthPage mode="register" />} />
            <Route path="/invite/:code" element={<InvitePage />} />
            <Route path="*" element={<AuthPage mode="login" />} />
          </Routes>
        )}
      </main>
    </>
  )
}
