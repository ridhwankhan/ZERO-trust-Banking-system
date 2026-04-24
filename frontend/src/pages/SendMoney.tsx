import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  Send,
  Shield,
  Lock,
  Eye,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { createTransaction } from '../services/api'
import './SendMoney.css'

const privacyLevels = [
  {
    id: 'standard',
    name: 'Standard',
    description: 'All transaction details visible',
    icon: Eye,
    color: '#48bb78'
  },
  {
    id: 'private_metadata',
    name: 'Private Metadata',
    description: 'Encrypt description and notes',
    icon: Lock,
    color: '#ed8936'
  },
  {
    id: 'high_privacy',
    name: 'High Privacy',
    description: 'Encrypt all transaction details',
    icon: Shield,
    color: '#9f7aea'
  }
]

export default function SendMoney() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  
  const [formData, setFormData] = useState({
    receiver_email: '',
    amount: '',
    privacy_level: 'standard',
    description: '',
    notes: '',
    category: ''
  })

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      // In a real app, we'd look up receiver_id by email
      // For now, using a placeholder
      await createTransaction({
        receiver_id: 1, // This should be looked up from email
        amount: formData.amount,
        privacy_level: formData.privacy_level as any,
        description: formData.description,
        notes: formData.notes,
        category: formData.category
      })
      
      setSuccess(true)
      setTimeout(() => navigate('/dashboard'), 2000)
    } catch (err: any) {
      setError(err.response?.data?.error || 'Transaction failed')
      setLoading(false)
    }
  }

  const selectedPrivacy = privacyLevels.find(p => p.id === formData.privacy_level)

  return (
    <div className="send-money-container">
      {/* Header */}
      <motion.header
        initial={{ y: -50 }}
        animate={{ y: 0 }}
        className="send-header"
      >
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => navigate('/dashboard')}
          className="back-btn"
        >
          <ArrowLeft size={24} />
        </motion.button>
        <h1>Send Money</h1>
        <div style={{ width: 40 }} />
      </motion.header>

      {/* Progress Steps */}
      <div className="progress-steps">
        {[1, 2, 3].map((s) => (
          <motion.div
            key={s}
            className={`step ${s === step ? 'active' : ''} ${s < step ? 'completed' : ''}`}
            animate={{
              scale: s === step ? 1.1 : 1,
              backgroundColor: s <= step ? '#667eea' : '#e2e8f0'
            }}
          >
            {s < step ? <CheckCircle size={16} /> : s}
          </motion.div>
        ))}
      </div>

      {/* Main Content */}
      <main className="send-main">
        <AnimatePresence mode="wait">
          {success ? (
            <motion.div
              key="success"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="success-card"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200 }}
                className="success-icon"
              >
                <CheckCircle size={64} />
              </motion.div>
              <h2>Transaction Sent!</h2>
              <p>Your money is on its way securely.</p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/dashboard')}
                className="primary-btn"
              >
                Back to Dashboard
              </motion.button>
            </motion.div>
          ) : (
            <motion.form
              key="form"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              onSubmit={step === 3 ? handleSubmit : (e) => { e.preventDefault(); setStep(step + 1) }}
              className="send-form"
            >
              {/* Step 1: Amount & Recipient */}
              {step === 1 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="form-step"
                >
                  <h2>Who are you sending to?</h2>
                  
                  <div className="input-group large">
                    <label>Recipient Email</label>
                    <input
                      type="email"
                      placeholder="email@example.com"
                      value={formData.receiver_email}
                      onChange={(e) => setFormData({ ...formData, receiver_email: e.target.value })}
                      required
                    />
                  </div>

                  <div className="input-group large">
                    <label>Amount</label>
                    <div className="amount-input">
                      <span className="currency">$</span>
                      <input
                        type="number"
                        placeholder="0.00"
                        value={formData.amount}
                        onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                        required
                        min="0.01"
                        step="0.01"
                      />
                    </div>
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="submit"
                    className="primary-btn"
                    disabled={!formData.receiver_email || !formData.amount}
                  >
                    Continue
                  </motion.button>
                </motion.div>
              )}

              {/* Step 2: Privacy Level */}
              {step === 2 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="form-step"
                >
                  <h2>Choose Privacy Level</h2>
                  <p className="subtitle">How would you like to protect this transaction?</p>

                  <div className="privacy-options">
                    {privacyLevels.map((level) => (
                      <motion.div
                        key={level.id}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => setFormData({ ...formData, privacy_level: level.id })}
                        className={`privacy-card ${formData.privacy_level === level.id ? 'selected' : ''}`}
                        style={{ borderColor: formData.privacy_level === level.id ? level.color : undefined }}
                      >
                        <div className="privacy-icon" style={{ background: level.color }}>
                          <level.icon size={24} />
                        </div>
                        <div className="privacy-info">
                          <h3>{level.name}</h3>
                          <p>{level.description}</p>
                        </div>
                        {formData.privacy_level === level.id && (
                          <motion.div
                            layoutId="check"
                            className="selected-indicator"
                          >
                            <CheckCircle size={20} style={{ color: level.color }} />
                          </motion.div>
                        )}
                      </motion.div>
                    ))}
                  </div>

                  <div className="button-group">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      type="button"
                      onClick={() => setStep(1)}
                      className="secondary-btn"
                    >
                      Back
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      type="submit"
                      className="primary-btn"
                    >
                      Continue
                    </motion.button>
                  </div>
                </motion.div>
              )}

              {/* Step 3: Details & Confirm */}
              {step === 3 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="form-step"
                >
                  <h2>Add Details</h2>

                  {(formData.privacy_level === 'standard' || formData.privacy_level === 'private_metadata') && (
                    <div className="input-group">
                      <label>Description (Optional)</label>
                      <input
                        type="text"
                        placeholder="What's this for?"
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      />
                    </div>
                  )}

                  {formData.privacy_level === 'standard' && (
                    <div className="input-group">
                      <label>Notes (Optional)</label>
                      <textarea
                        placeholder="Add any additional notes..."
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        rows={3}
                      />
                    </div>
                  )}

                  <div className="input-group">
                    <label>Category</label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    >
                      <option value="">Select a category</option>
                      <option value="transfer">Transfer</option>
                      <option value="payment">Payment</option>
                      <option value="gift">Gift</option>
                      <option value="business">Business</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  {/* Summary Card */}
                  <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="summary-card"
                  >
                    <h3>Transaction Summary</h3>
                    <div className="summary-row">
                      <span>To</span>
                      <strong>{formData.receiver_email}</strong>
                    </div>
                    <div className="summary-row">
                      <span>Amount</span>
                      <strong>${parseFloat(formData.amount).toFixed(2)}</strong>
                    </div>
                    <div className="summary-row">
                      <span>Privacy</span>
                      <span className="privacy-badge" style={{ background: selectedPrivacy?.color }}>
                        {selectedPrivacy?.name}
                      </span>
                    </div>
                  </motion.div>

                  {error && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="error-banner"
                    >
                      <AlertCircle size={20} />
                      {error}
                    </motion.div>
                  )}

                  <div className="button-group">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      type="button"
                      onClick={() => setStep(2)}
                      className="secondary-btn"
                    >
                      Back
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      type="submit"
                      className="primary-btn"
                      disabled={loading}
                    >
                      {loading ? (
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ repeat: Infinity, duration: 1 }}
                          className="spinner-small"
                        />
                      ) : (
                        <>
                          <Send size={18} />
                          Send Money
                        </>
                      )}
                    </motion.button>
                  </div>
                </motion.div>
              )}
            </motion.form>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}
