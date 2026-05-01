import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Shield, ArrowRight, KeyRound } from 'lucide-react'
import { login, verifyTwoFactorLogin } from '../services/api'
import './Auth.css'

export default function Login() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [twoFactorStep, setTwoFactorStep] = useState(false)
  const [twoFactorCode, setTwoFactorCode] = useState('')
  const [pendingUserId, setPendingUserId] = useState<number | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await login(formData)
      if (response.user?.two_factor_enabled) {
        setPendingUserId(response.user.id)
        setTwoFactorStep(true)
        return
      }

      if (!response.tokens) {
        setError('Login response is missing tokens.')
        return
      }
      localStorage.setItem('access_token', response.tokens.access)
      localStorage.setItem('refresh_token', response.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(response.user))
      navigate('/dashboard')
    } catch (err: any) {
      let errorMessage = 'Login failed. Please check your credentials.'
      if (!err.response) {
        errorMessage = 'Unable to reach backend server. Make sure the Django API is running at http://localhost:8000'
      } else if (err.response.data) {
        errorMessage = err.response.data.detail || err.response.data.message || err.response.data.error || errorMessage
      }
      setError(errorMessage)
      console.error('Login error:', err.response?.data || err)
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyTwoFactor = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!pendingUserId) {
      setError('Missing 2FA session. Please login again.')
      setTwoFactorStep(false)
      return
    }

    setLoading(true)
    setError('')
    try {
      const response = await verifyTwoFactorLogin({
        user_id: pendingUserId,
        token: twoFactorCode,
      })
      if (!response.tokens) {
        setError('2FA verification did not return tokens.')
        return
      }
      localStorage.setItem('access_token', response.tokens.access)
      localStorage.setItem('refresh_token', response.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(response.user))
      navigate('/dashboard')
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Invalid authenticator code. Try again.'
      setError(errorMessage)
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

        <h1 className="auth-title">{twoFactorStep ? 'Two-Factor Verification' : 'Welcome Back'}</h1>
        <p className="auth-subtitle">
          {twoFactorStep ? 'Enter your 6-digit authenticator code to continue' : 'Sign in to your secure account'}
        </p>

        {error && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="error-message"
          >
            {error}
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          {!twoFactorStep ? (
            <motion.form
              key="login-form"
              initial={{ opacity: 0, x: -14 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 14 }}
              onSubmit={handleSubmit}
              className="auth-form"
            >
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
                    Sign In <ArrowRight size={20} />
                  </>
                )}
              </motion.button>
            </motion.form>
          ) : (
            <motion.form
              key="twofa-form"
              initial={{ opacity: 0, x: 14 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -14 }}
              onSubmit={handleVerifyTwoFactor}
              className="auth-form"
            >
              <div className="input-group">
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: 4,
                    color: '#667eea',
                  }}
                >
                  <KeyRound size={20} />
                </div>
                <input
                  type="text"
                  placeholder="6-digit Authenticator Code"
                  value={twoFactorCode}
                  onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, ''))}
                  maxLength={6}
                  pattern="\d{6}"
                  required
                />
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                className="auth-button"
                disabled={loading || twoFactorCode.length !== 6}
              >
                {loading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1 }}
                    className="spinner"
                  />
                ) : (
                  <>
                    Verify & Continue <ArrowRight size={20} />
                  </>
                )}
              </motion.button>

              <button
                type="button"
                onClick={() => {
                  setTwoFactorStep(false)
                  setTwoFactorCode('')
                  setPendingUserId(null)
                  setError('')
                }}
                className="auth-button"
                style={{ background: '#334155' }}
              >
                Back
              </button>
            </motion.form>
          )}
        </AnimatePresence>

        {!twoFactorStep && (
          <p className="auth-footer">
            Don't have an account?{' '}
            <Link to="/register" className="auth-link">
              Create one
            </Link>
          </p>
        )}
      </motion.div>
    </div>
  )
}
