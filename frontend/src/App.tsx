import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import SendMoney from './pages/SendMoney'
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

// Get user role from localStorage
const getUserRole = () => {
  return localStorage.getItem('role')
}

// Protected route wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

// Admin/Authority only route wrapper
const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  if (!isAuthenticated() || getUserRole() !== 'admin') {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

const AuthorityRoute = ({ children }: { children: React.ReactNode }) => {
  if (!isAuthenticated() || getUserRole() !== 'authority') {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <Router>
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
              <Page><SendMoney /></Page>
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
