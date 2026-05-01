import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, ArrowRight, CheckCircle } from 'lucide-react'
import { register } from '../services/api'
import './Auth.css'

export default function Register() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    contact_info: '',
    password: '',
    password_confirm: '',
  })
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
      let errorMessage = 'Registration failed. Please try again.'
      
      if (!err.response) {
        errorMessage = 'Unable to reach backend server. Make sure the Django API is running at http://localhost:8000'
      } else if (err.response.data) {
        const data = err.response.data
        
        if (data.password && Array.isArray(data.password)) {
          errorMessage = data.password.join(' ')
        } else if (data.email && Array.isArray(data.email)) {
          errorMessage = 'Email: ' + data.email.join(' ')
        } else if (data.username && Array.isArray(data.username)) {
          errorMessage = 'Username: ' + data.username.join(' ')
        } else if (data.detail) {
          errorMessage = data.detail
        } else if (data.message) {
          errorMessage = data.message
        } else if (data.error) {
          errorMessage = data.error
        } else if (typeof data === 'string') {
          errorMessage = data
        }
      }
      
      setError(errorMessage)
      console.error('Registration error:', err.response?.data || err)
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
            {/* <Mail size={20} className="input-icon" /> */}
            <input
              type="email"
              placeholder="Email address"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>

          <div className="input-group">
            {/* <User size={20} className="input-icon" /> */}
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
            {/* <Lock size={20} className="input-icon" /> */}
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />
          </div>
          
          <div className="password-tips">
            <p style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Password must have: 8+ characters, mix of letters & numbers
            </p>
          </div>

          <div className="input-group">
            {/* <Lock size={20} className="input-icon" /> */}
            <input
              type="password"
              placeholder="Confirm Password"
              value={formData.password_confirm}
              onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
              required
            />
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
