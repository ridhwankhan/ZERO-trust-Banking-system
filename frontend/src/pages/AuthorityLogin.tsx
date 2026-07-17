import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, ArrowRight, Home, Eye, EyeOff } from 'lucide-react'
import { api } from '../services/api'
import '../pages/Auth.css'

export default function AuthorityLogin() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const authRequired = searchParams.get('authRequired') === '1'
  const [formData, setFormData] = useState({
    email: 'authority@fiducia.bd',
    password: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await api.post('/auth/authority-login/', formData)
      localStorage.setItem('access_token', response.data.tokens.access)
      localStorage.setItem('refresh_token', response.data.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(response.data.user))
      localStorage.setItem('role', response.data.user.role)
      navigate('/authority-dashboard')
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Authority login failed. Please check your credentials.'
      setError(errorMessage)
      console.error('Authority login error:', err.response?.data || err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <Link to="/" className="auth-home-link">
        <Home size={18} />
        <span>Fiducia Bank</span>
      </Link>

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

        <h1 className="auth-title">Central Authority Login</h1>
        <p className="auth-subtitle">Verify users and manage KYC</p>

        <div className="demo-creds">
          Demo: <strong>authority@fiducia.bd</strong> / <strong>authority123</strong>
        </div>

        {authRequired && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="error-message"
            style={{ background: 'rgba(59, 130, 246, 0.12)', borderColor: '#3b82f6', color: '#93c5fd' }}
          >
            You need to log in first to access the authority dashboard.
          </motion.div>
        )}

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
            <input
              type="email"
              placeholder="Authority email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>

          <div className="input-group">
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
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
                Authority Login <ArrowRight size={20} />
              </>
            )}
          </motion.button>
        </form>

        <p className="auth-footer">
          Looking for user login?{' '}
          <Link to="/login" className="auth-link">
            Sign in here
          </Link>
        </p>
      </motion.div>
    </div>
  )
}
