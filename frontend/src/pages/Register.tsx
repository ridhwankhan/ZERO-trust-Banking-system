import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, ArrowRight, CheckCircle, Home, Eye, EyeOff } from 'lucide-react'
import { register } from '../services/api'
import './Auth.css'

function extractErrorMessage(err: any, fallback: string): string {
  if (!err.response) {
    return 'Unable to reach backend server. Please check your internet connection or the server URL.'
  }

  const data = err.response.data
  if (!data) return fallback

  if (typeof data === 'string') {
    if (data.includes('<!doctype') || data.includes('<html') || data.includes('Server Error')) {
      return 'Server error during registration. Please try again in a moment.'
    }
    return data
  }

  if (data.password && Array.isArray(data.password)) return data.password.join(' ')
  if (data.email && Array.isArray(data.email)) return 'Email: ' + data.email.join(' ')
  if (data.username && Array.isArray(data.username)) return 'Username: ' + data.username.join(' ')
  if (data.contact_info && Array.isArray(data.contact_info)) return 'Contact: ' + data.contact_info.join(' ')
  if (data.error) return typeof data.error === 'string' ? data.error : fallback
  if (data.detail) return typeof data.detail === 'string' ? data.detail : fallback
  if (data.message) return data.message

  return fallback
}

export default function Register() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    contact_info: '',
    password: '',
    password_confirm: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (formData.password !== formData.password_confirm) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      const response = await register(formData)
      if (!response.tokens) {
        throw new Error('Registration response did not include tokens')
      }
      localStorage.setItem('access_token', response.tokens.access)
      localStorage.setItem('refresh_token', response.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(response.user))
      setSuccess(true)
      setTimeout(() => navigate('/dashboard'), 2000)
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Registration failed. Please try again.'))
      console.error('Registration error:', err.response?.data || err)
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

        <h1 className="auth-title">Create Account</h1>
        <p className="auth-subtitle">Join our secure banking platform</p>

        {success && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="success-message"
          >
            <CheckCircle size={20} />
            Account created successfully! Redirecting...
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
              placeholder="Email address"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>

          <div className="input-group">
            <input
              type="text"
              placeholder="Username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              required
            />
          </div>

          <div className="input-group">
            <input
              type="text"
              placeholder="Contact Info (Phone / Address)"
              value={formData.contact_info}
              onChange={(e) => setFormData({ ...formData, contact_info: e.target.value })}
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

          <div className="password-tips">
            <p style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Password must have: 8+ characters, mix of letters & numbers
            </p>
          </div>

          <div className="input-group">
            <input
              type={showPasswordConfirm ? 'text' : 'password'}
              placeholder="Confirm Password"
              value={formData.password_confirm}
              onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPasswordConfirm((v) => !v)}
              aria-label={showPasswordConfirm ? 'Hide password' : 'Show password'}
            >
              {showPasswordConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            className="auth-button"
            disabled={loading || success}
          >
            {loading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1 }}
                className="spinner"
              />
            ) : (
              <>
                Create Account <ArrowRight size={20} />
              </>
            )}
          </motion.button>
        </form>

        <p className="auth-footer">
          Already have an account?{' '}
          <Link to="/login" className="auth-link">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  )
}
