import { useState, useEffect, useRef } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Bell, Shield, LogOut, User as UserIcon } from 'lucide-react'
import { api, logout } from '../services/api'
import { useAutoRefresh } from '../hooks/useAutoRefresh'
import './Navbar.css'

export default function Navbar() {
  const [notifications, setNotifications] = useState<any[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [showDropdown, setShowDropdown] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const dropdownRef = useRef<HTMLDivElement>(null)

  const isAuthPage = location.pathname === '/login' || location.pathname === '/register' || location.pathname === '/admin-login' || location.pathname === '/authority-login'
  const isAuthenticated = !!localStorage.getItem('access_token')
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const role = localStorage.getItem('role') || user.role || 'user'
  const isStaff = role === 'admin' || role === 'authority'
  const homePath = role === 'admin' ? '/admin-dashboard' : role === 'authority' ? '/authority-dashboard' : '/dashboard'

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const fetchNotifications = async () => {
    try {
      const response = await api.get('/notifications/')
      setNotifications(response.data.notifications)
      setUnreadCount(response.data.unread_count)
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    }
  }

  useAutoRefresh(fetchNotifications, {
    scope: 'notifications',
    intervalMs: 5000,
    enabled: isAuthenticated && !isAuthPage,
    deps: [isAuthenticated, isAuthPage, location.pathname],
  })

  const markAsRead = async (id?: number) => {
    try {
      const url = id ? `/notifications/${id}/read/` : '/notifications/read/'
      await api.post(url)
      
      if (id) {
        setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
        setUnreadCount(prev => Math.max(0, prev - 1))
      } else {
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
        setUnreadCount(0)
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err)
    }
  }

  const handleLogout = async () => {
    const refresh = localStorage.getItem('refresh_token')
    if (refresh) {
      try {
        await logout(refresh)
      } catch (error) {
        console.error('Logout error:', error)
      }
    }
    localStorage.clear()
    navigate('/login')
  }

  if (isAuthPage || !isAuthenticated) return null

  return (
    <nav className="navbar-container">
      <div className="navbar-left">
        <Link to={homePath} className="navbar-logo-group">
          <Shield size={32} className="header-logo-icon" />
          <div className="header-brand-info">
            <h1>Fiducia Bank</h1>
            <span className="header-tagline-text">A Zero-Trust Financial Platform</span>
          </div>
        </Link>
      </div>

      {!isStaff && (
        <div className="navbar-center-links">
          <Link to="/dashboard" className={`center-nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}>
            Dashboard
          </Link>
          <Link to="/transfer" className={`center-nav-link ${location.pathname === '/transfer' ? 'active' : ''}`}>
            Transfer
          </Link>
          <Link to="/security-center" className={`center-nav-link ${location.pathname === '/security-center' ? 'active' : ''}`}>
            Security
          </Link>
          <Link to="/history" className={`center-nav-link ${location.pathname === '/history' ? 'active' : ''}`}>
            History
          </Link>
          <Link to="/profile" className={`center-nav-link ${location.pathname === '/profile' ? 'active' : ''}`}>
            Profile
          </Link>
        </div>
      )}

      <div className="navbar-right">
        <div className="notification-container" ref={dropdownRef}>
          <button 
            className="bell-btn"
            onClick={() => setShowDropdown(!showDropdown)}
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <motion.div 
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="badge"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </motion.div>
            )}
          </button>

          <AnimatePresence>
            {showDropdown && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ duration: 0.2 }}
                className="notifications-dropdown"
              >
                <div className="notif-header">
                  <h4>Notifications</h4>
                  {unreadCount > 0 && (
                    <button className="mark-read-btn" onClick={() => markAsRead()}>
                      Mark all as read
                    </button>
                  )}
                </div>
                <div className="notif-list">
                  {notifications.length === 0 ? (
                    <div className="notif-empty">No notifications yet.</div>
                  ) : (
                    notifications.map(notif => (
                      <div 
                        key={notif.id} 
                        className={`notif-item ${!notif.is_read ? 'unread' : ''}`}
                        onClick={() => !notif.is_read && markAsRead(notif.id)}
                      >
                        <p className="notif-title">{notif.title}</p>
                        <p className="notif-msg">{notif.message}</p>
                        <p className="notif-time">{new Date(notif.created_at).toLocaleString()}</p>
                      </div>
                    ))
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="nav-user-info">
          <UserIcon size={18} />
          <span>{user.email}</span>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleLogout}
          className="nav-logout-btn"
        >
          <LogOut size={16} />
          <span>Sign Out</span>
        </motion.button>
      </div>
    </nav>
  )
}
