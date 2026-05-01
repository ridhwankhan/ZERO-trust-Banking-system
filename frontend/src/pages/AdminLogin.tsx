import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, ArrowRight } from 'lucide-react'
import { api } from '../services/api'
import '../pages/Auth.css'

export default function AdminLogin() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await api.post('/auth/admin-login/', formData)
      localStorage.setItem('access_token', response.data.tokens.access)
      localStorage.setItem('refresh_token', response.data.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(response.data.user))
      localStorage.setItem('role', response.data.user.role)
      navigate('/admin-dashboard')
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Admin login failed. Please check your credentials.'
      setError(errorMessage)
      console.error('Admin login error:', err.response?.data || err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="auth-card"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          className="auth-logo"
        >
          <Shield size={48} className="text-primary" />
        </motion.div>

        <h1 className="auth-title">Admin Login</h1>
        <p className="auth-subtitle">Access the administration dashboard</p>

        {error && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="error-message"
          >
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="input-group">
            {/* <Mail size={20} className="input-icon" /> */}
            <input
              type="email"
              placeholder="Admin email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>

          <div className="input-group">
            {/* <Lock size={20} className="input-icon" /> */}
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1 }}
                className="spinner"
              />
            ) : (
              <>
                Admin Login <ArrowRight size={20} />
              </>
            )}
          </motion.button>
        </form>

        <p className="auth-footer">
          Looking for user login?{' '}
          <a href="/login" className="auth-link">
            Sign in here
          </a>
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="auth-info"
      >
        {/* <h3>Admin Panel Features</h3>
        <ul>
          <li>User management and account control</li>
          <li>Suspend/activate user accounts</li>
          <li>Monitor encrypted transactions</li>
          <li>View system statistics</li>
          <li>Audit transaction integrity</li>
        </ul> */}
      </motion.div>
    </div>
  )
}
