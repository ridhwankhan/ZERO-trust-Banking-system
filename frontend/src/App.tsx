import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import SendMoney from './pages/SendMoney'
import TransactionHistory from './pages/TransactionHistory'
import Deposit from './pages/Deposit'
import Transfer from './pages/Transfer'
import AdminLogin from './pages/AdminLogin'
import AuthorityLogin from './pages/AuthorityLogin'
import AdminDashboard from './pages/AdminDashboard'
import AuthorityDashboard from './pages/AuthorityDashboard'
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
      <Routes>
        {/* Public Home Route */}
        <Route path="/" element={<Home />} />
        
        {/* Public Authentication Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/admin-login" element={<AdminLogin />} />
        <Route path="/authority-login" element={<AuthorityLogin />} />
        
        {/* User Protected Routes */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/send" 
          element={
            <ProtectedRoute>
              <SendMoney />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/history" 
          element={
            <ProtectedRoute>
              <TransactionHistory />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/deposit" 
          element={
            <ProtectedRoute>
              <Deposit />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/transfer" 
          element={
            <ProtectedRoute>
              <Transfer />
            </ProtectedRoute>
          } 
        />
        
        {/* Admin Protected Routes */}
        <Route 
          path="/admin-dashboard" 
          element={
            <AdminRoute>
              <AdminDashboard />
            </AdminRoute>
          } 
        />
        
        {/* Authority Protected Routes */}
        <Route 
          path="/authority-dashboard" 
          element={
            <AuthorityRoute>
              <AuthorityDashboard />
            </AuthorityRoute>
          } 
        />
        
        {/* Redirect unknown routes */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App
