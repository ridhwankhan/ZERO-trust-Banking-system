import { useState, useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Bell, Shield, Home, Activity, Lock, User as UserIcon } from 'lucide-react'
import { api } from '../services/api'
import './Navbar.css'

export default function Navbar() {
  const [notifications, setNotifications] = useState<any[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [showDropdown, setShowDropdown] = useState(false)
  const location = useLocation()
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Don't show navbar on login/register pages
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register' || location.pathname === '/admin-login' || location.pathname === '/authority-login'
  const isAuthenticated = !!localStorage.getItem('access_token')

  useEffect(() => {
    if (isAuthenticated && !isAuthPage) {
      fetchNotifications()
      // Poll every 30 seconds for new notifications
      const interval = setInterval(fetchNotifications, 30000)
      return () => clearInterval(interval)
    }
  }, [isAuthenticated, isAuthPage, location.pathname])

  // Close dropdown when clicking outside
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

  const markAsRead = async (id?: number) => {
    try {
      const url = id ? `/notifications/${id}/read/` : '/notifications/read/'
      await api.post(url)
      
      // Optimistic UI update
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

  if (isAuthPage || !isAuthenticated) return null

  return (
    <nav className="navbar-container">
      <Link to="/dashboard" className="navbar-logo">
        <Shield size={28} color="#60a5fa" />
        <h2>Fiducia Bank</h2>
      </Link>

      <div className="navbar-links">
        <Link to="/dashboard" className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}>
          <Home size={18} /> Dashboard
        </Link>
        <Link to="/transfer" className={`nav-link ${location.pathname === '/transfer' ? 'active' : ''}`}>
          <Activity size={18} /> Transfer
        </Link>
        <Link to="/security-center" className={`nav-link ${location.pathname === '/security-center' ? 'active' : ''}`}>
          <Lock size={18} /> Security
        </Link>
      </div>

      <div className="navbar-actions">
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

        <Link to="/profile" className="profile-btn">
          <UserIcon size={16} /> Profile
        </Link>
      </div>
    </nav>
  )
}
