import { LogOut, Map as MapIcon, MapPin, Newspaper, Users } from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { fetchFriends } from '../api'
import { useAuth } from '../auth'
import { Avatar } from './ui'

export default function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [requests, setRequests] = useState(0)
  const link = ({ isActive }: { isActive: boolean }) => `nav-link${isActive ? ' active' : ''}`

  // Show how many friend requests are waiting; refresh when the page changes
  useEffect(() => {
    if (!user) return
    fetchFriends()
      .then((f) => setRequests(f.incoming.length))
      .catch(() => setRequests(0))
  }, [user, location.pathname])

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <span className="brand">
          <span className="brand-mark">
            <MapPin size={18} strokeWidth={2.6} />
          </span>
          Friend Recs
        </span>
        {user && (
          <>
            <div className="nav-links">
              <NavLink to="/" end className={link}>
                <MapIcon size={16} /> Map
              </NavLink>
              <NavLink to="/feed" className={link}>
                <Newspaper size={16} /> Feed
              </NavLink>
              <NavLink to="/friends" className={link}>
                <Users size={16} /> Friends
                {requests > 0 && <span className="nav-badge">{requests}</span>}
              </NavLink>
            </div>
            <div className="nav-user">
              <Avatar name={user.display_name} size={34} />
              <div className="nav-user-name">
                {user.display_name}
                <span>@{user.username}</span>
              </div>
              <button className="icon-btn" onClick={logout} title="Log out" aria-label="Log out">
                <LogOut size={16} />
              </button>
            </div>
          </>
        )}
      </div>
    </nav>
  )
}
