import { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import TransactionHistory from './pages/TransactionHistory'
import Deposit from './pages/Deposit'
import Transfer from './pages/Transfer'
import Profile from './pages/Profile'
import Posts from './pages/Posts'
import CreatePost from './pages/CreatePost'
import AdminLogin from './pages/AdminLogin'
import AuthorityLogin from './pages/AuthorityLogin'
import AdminDashboard from './pages/AdminDashboard'
import AuthorityDashboard from './pages/AuthorityDashboard'
import SecurityCenter from './pages/SecurityCenter'
import AdminSecurityDashboard from './pages/AdminSecurityDashboard'
import './App.css'

// Simple auth check
const isAuthenticated = () => {
  return !!localStorage.getItem('access_token')
}

// Get user role from localStorage (falls back to the stored user object)
const getUserRole = (): string => {
  const explicit = localStorage.getItem('role')
  if (explicit) return explicit
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user?.role || 'user'
  } catch {
    return 'user'
  }
}

// Where a logged-in account belongs, based on its role
const homeForRole = (role: string) => {
  if (role === 'admin') return '/admin-dashboard'
  if (role === 'authority') return '/authority-dashboard'
  return '/dashboard'
}

// Protected route for regular banking users ONLY.
// - Not logged in  -> login page (with "please sign in" notice)
// - Admin/Authority -> bounced back to their own dashboard (cannot roam the bank app)
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login?authRequired=1" replace />
  }
  const role = getUserRole()
  if (role === 'admin' || role === 'authority') {
    return <Navigate to={homeForRole(role)} replace />
  }
  return <>{children}</>
}

// Admin-only route wrapper
const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/admin-login?authRequired=1" replace />
  }
  if (getUserRole() !== 'admin') {
    return <Navigate to={homeForRole(getUserRole())} replace />
  }
  return <>{children}</>
}

// Authority-only route wrapper
const AuthorityRoute = ({ children }: { children: React.ReactNode }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/authority-login?authRequired=1" replace />
  }
  if (getUserRole() !== 'authority') {
    return <Navigate to={homeForRole(getUserRole())} replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <Router>
      <Navbar />
      <AnimatedRoutes />
    </Router>
  )
}

const pageTransition = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -14 },
}

const Page = ({ children }: { children: React.ReactNode }) => (
  <motion.div
    variants={pageTransition}
    initial="initial"
    animate="animate"
    exit="exit"
    transition={{ duration: 0.3, ease: 'easeOut' }}
  >
    {children}
  </motion.div>
)

function AnimatedRoutes() {
  const location = useLocation()
  
  // Auto-Privacy Mode (Anti-Screen Capture & Spyware)
  useEffect(() => {
    const handleBlur = () => document.body.classList.add('privacy-mode')
    const handleFocus = () => document.body.classList.remove('privacy-mode')
    
    // Visibility API is faster than window blur for tab switching
    const handleVisibility = () => {
      if (document.hidden) {
        document.body.classList.add('privacy-mode')
      } else {
        document.body.classList.remove('privacy-mode')
      }
    }

    // Intercept PrintScreen key to instantly blur and clear clipboard
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'PrintScreen') {
        document.body.classList.add('privacy-mode')
        navigator.clipboard.writeText('') // Clear clipboard to prevent copying screenshot if possible
        setTimeout(() => document.body.classList.remove('privacy-mode'), 2000) // Unblur after 2 seconds
      }
    }
    
    window.addEventListener('blur', handleBlur)
    window.addEventListener('focus', handleFocus)
    document.addEventListener('visibilitychange', handleVisibility)
    document.addEventListener('keyup', handleKeyUp)
    
    return () => {
      window.removeEventListener('blur', handleBlur)
      window.removeEventListener('focus', handleFocus)
      document.removeEventListener('visibilitychange', handleVisibility)
      document.removeEventListener('keyup', handleKeyUp)
    }
  }, [])

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* Public Home Route */}
        <Route path="/" element={<Page><Home /></Page>} />
        
        {/* Public Authentication Routes */}
        <Route path="/login" element={<Page><Login /></Page>} />
        <Route path="/register" element={<Page><Register /></Page>} />
        <Route path="/admin-login" element={<Page><AdminLogin /></Page>} />
        <Route path="/authority-login" element={<Page><AuthorityLogin /></Page>} />
        
        {/* User Protected Routes */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Page><Dashboard /></Page>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/send" 
          element={
            <ProtectedRoute>
              <Page><Transfer /></Page>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/history" 
          element={
            <ProtectedRoute>
              <Page><TransactionHistory /></Page>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/deposit" 
          element={
            <ProtectedRoute>
              <Page><Deposit /></Page>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <Page><Profile /></Page>
            </ProtectedRoute>
          } 
        />
        <Route
          path="/posts"
          element={
            <ProtectedRoute>
              <Page><Posts /></Page>
            </ProtectedRoute>
          }
        />
        <Route
          path="/posts/new"
          element={
            <ProtectedRoute>
              <Page><CreatePost /></Page>
            </ProtectedRoute>
          }
        />
        <Route 
          path="/transfer" 
          element={
            <ProtectedRoute>
              <Page><Transfer /></Page>
            </ProtectedRoute>
          } 
        />
        <Route
          path="/security-center"
          element={
            <ProtectedRoute>
              <Page><SecurityCenter /></Page>
            </ProtectedRoute>
          }
        />
        
        {/* Admin Protected Routes */}
        <Route 
          path="/admin-dashboard" 
          element={
            <AdminRoute>
              <Page><AdminDashboard /></Page>
            </AdminRoute>
          } 
        />
        <Route
          path="/admin/security-dashboard"
          element={
            <AdminRoute>
              <Page><AdminSecurityDashboard /></Page>
            </AdminRoute>
          }
        />
        
        {/* Authority Protected Routes */}
        <Route 
          path="/authority-dashboard" 
          element={
            <AuthorityRoute>
              <Page><AuthorityDashboard /></Page>
            </AuthorityRoute>
          } 
        />
        
        {/* Redirect unknown routes */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  )
}

export default App
