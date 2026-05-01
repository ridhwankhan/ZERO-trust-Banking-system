import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CreditCard, DollarSign, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import './Deposit.css'

export default function Deposit() {
  const [step, setStep] = useState(1) // 1: amount, 2: payment, 3: success
  const [amount, setAmount] = useState('')
  const [cardNumber, setCardNumber] = useState('')
  const [cardExpiry, setCardExpiry] = useState('')
  const [cardCVV, setCardCVV] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [newBalance, setNewBalance] = useState('')
  const [transactionId, setTransactionId] = useState('')
  const navigate = useNavigate()

  const handleInitiateDeposit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount')
      setLoading(false)
      return
    }

    try {
      await api.post('/transactions/deposit/initiate/', {
        amount: parseFloat(amount),
      })
      setStep(2)
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || 'Failed to initiate deposit'
      setError(errorMessage)
      console.error('Deposit initiation error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleProcessPayment = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (!cardNumber || cardNumber.length < 13) {
      setError('Please enter a valid card number')
      setLoading(false)
      return
    }

    try {
      const response = await api.post('/transactions/deposit/process/', {
        amount: parseFloat(amount),
        card_number: cardNumber,
      })

      setNewBalance(response.data.new_balance)
      setTransactionId(response.data.transaction.id)
      setSuccess(true)
      setStep(3)
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || err.response?.data?.message || 'Payment failed'
      setError(errorMessage)
      console.error('Payment error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="deposit-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="deposit-card"
      >
        <div className="deposit-header">
          <DollarSign size={40} className="deposit-icon" />
          <h1>Deposit Funds</h1>
          <p>Add money to your secure banking account</p>
        </div>

        {/* Step 1: Amount Entry */}
        {step === 1 && (
          <motion.form
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            onSubmit={handleInitiateDeposit}
            className="deposit-form"
          >
            <div className="form-group">
              <label>Deposit Amount (USD)</label>
              <div className="amount-input">
                <span className="currency">$</span>
                <input
                  type="number"
                  placeholder="100.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  step="0.01"
                  min="1"
                  required
                />
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="error-message"
              >
                <AlertCircle size={20} />
                {error}
              </motion.div>
            )}

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className="deposit-button"
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Continue to Payment'}
            </motion.button>
          </motion.form>
        )}

        {/* Step 2: Card Payment */}
        {step === 2 && (
          <motion.form
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            onSubmit={handleProcessPayment}
            className="deposit-form"
          >
            <div className="amount-display">
              <p>Deposit Amount: <strong>${amount}</strong></p>
            </div>

            <div className="form-group">
              <label>Card Number (Test: 4111-1111-1111-1111 = Success, 4444-4444-4444-4444 = Decline)</label>
              <div className="card-input">
                <CreditCard size={20} />
                <input
                  type="text"
                  placeholder="4111-1111-1111-1111"
                  value={cardNumber}
                  onChange={(e) => setCardNumber(e.target.value.replace(/\s/g, ''))}
                  maxLength={19}
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Expiry (MM/YY)</label>
                <input
                  type="text"
                  placeholder="12/25"
                  value={cardExpiry}
                  onChange={(e) => setCardExpiry(e.target.value)}
                  maxLength={5}
                  required
                />
              </div>
              <div className="form-group">
                <label>CVV</label>
                <input
                  type="text"
                  placeholder="123"
                  value={cardCVV}
                  onChange={(e) => setCardCVV(e.target.value)}
                  maxLength={4}
                  required
                />
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="error-message"
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
                className="secondary-button"
                onClick={() => setStep(1)}
                disabled={loading}
              >
                Back
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                className="deposit-button"
                disabled={loading}
              >
                {loading ? 'Processing Payment...' : 'Complete Payment'}
              </motion.button>
            </div>
          </motion.form>
        )}

        {/* Step 3: Success */}
        {step === 3 && success && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="success-section"
          >
            <CheckCircle size={60} className="success-icon" />
            <h2>Deposit Successful!</h2>
            <p>Your funds have been added to your account</p>

            <div className="success-details">
              <div className="detail-row">
                <span>Transaction ID:</span>
                <strong>#{transactionId}</strong>
              </div>
              <div className="detail-row">
                <span>Amount Deposited:</span>
                <strong className="amount-green">${amount}</strong>
              </div>
              <div className="detail-row">
                <span>New Balance:</span>
                <strong className="amount-green">${newBalance}</strong>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="deposit-button"
              onClick={() => navigate('/dashboard')}
            >
              Return to Dashboard
            </motion.button>
          </motion.div>
        )}
      </motion.div>

      {/* Info Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="deposit-info"
      >
        <h3>Test Card Numbers</h3>
        {/* <div className="test-cards">
          <div className="test-card success">
            <h4>✓ Success</h4>
            <p>4111-1111-1111-1111</p>
          </div>
          <div className="test-card decline">
            <h4>✗ Decline</h4>
            <p>4444-4444-4444-4444</p>
          </div>
        </div> */}
        <p className="info-text">
          This is a simulated payment gateway. Use test card numbers above to see success/failure scenarios.
          All data is encrypted before storage.
        </p>
      </motion.div>
    </div>
  )
}
