import { useState } from 'react'
import { motion } from 'framer-motion'
import { Send, ArrowRight, CheckCircle, AlertCircle, CreditCard, Lock, Shield, EyeOff } from 'lucide-react'
import { api } from '../services/api'
import { useAutoRefresh } from '../hooks/useAutoRefresh'
import { emitDataRefresh } from '../utils/refreshBus'
import './Transfer.css'

export default function Transfer() {
  const [receiverInput, setReceiverInput] = useState('')
  const [amount, setAmount] = useState('')
  const [privacyLevel, setPrivacyLevel] = useState('standard')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [userBalance, setUserBalance] = useState('0.00')
  const [transactionDetails, setTransactionDetails] = useState<any>(null)

  const fetchBalance = async () => {
    try {
      const response = await api.get('/transactions/balance/')
      setUserBalance(response.data.balance)
    } catch (err) {
      console.error('Failed to fetch balance:', err)
    }
  }

  useAutoRefresh(fetchBalance, { scope: 'transfer', intervalMs: 5000 })

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (!receiverInput) {
      setError('Please enter a valid Card Number or Email')
      setLoading(false)
      return
    }

    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount')
      setLoading(false)
      return
    }

    if (parseFloat(amount) > parseFloat(userBalance)) {
      setError('Insufficient balance')
      setLoading(false)
      return
    }

    // Determine if input is email or card number
    const isEmail = receiverInput.includes('@')
    const payload: any = {
      amount: parseFloat(amount),
      privacy_level: privacyLevel,
    }

    if (isEmail) {
      payload.receiver_email = receiverInput.trim()
    } else {
      payload.card_number = receiverInput.replace(/\s+/g, '').trim()
    }

    try {
      const response = await api.post('/transactions/transfer/create/', payload)
      setTransactionDetails(response.data.transaction)
      setUserBalance(response.data.sender_new_balance)
      setSuccess(true)
      emitDataRefresh('all')
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || 'Transfer failed'
      setError(errorMessage)
      console.error('Transfer error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="transfer-container">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="transfer-card"
      >
        <div className="transfer-header">
          <div className="transfer-icon-wrapper">
            <Send size={40} />
          </div>
          <h1>Secure Transfer</h1>
          <p>Send encrypted funds to another account instantly</p>
        </div>

        {success && transactionDetails ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="success-screen"
          >
            <div className="success-icon-wrapper">
              <CheckCircle size={50} />
            </div>
            <h2>Transfer Successful!</h2>
            <p>Your funds have been securely sent and verified.</p>

            <div className="receipt-card">
              <div className="receipt-row">
                <span>Transaction ID</span>
                <strong>#{transactionDetails.id}</strong>
              </div>
              <div className="receipt-row">
                <span>To</span>
                <strong>{transactionDetails.receiver}</strong>
              </div>
              <div className="receipt-row">
                <span>Amount</span>
                <strong className="amount">${transactionDetails.amount}</strong>
              </div>
              <div className="receipt-row">
                <span>Privacy Level</span>
                <strong style={{ textTransform: 'capitalize' }}>
                  {transactionDetails.privacy_level.replace('_', ' ')}
                </strong>
              </div>
              <div className="receipt-row">
                <span>Transaction Hash</span>
                <span className="hash-code">{transactionDetails.transaction_hash.substring(0, 16)}...</span>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="transfer-btn"
              onClick={() => {
                setSuccess(false)
                setAmount('')
                setReceiverInput('')
              }}
            >
              Send Another Payment
            </motion.button>
          </motion.div>
        ) : (
          <form onSubmit={handleTransfer}>
            <div className="transfer-balance-card">
              <span className="balance-label">Available Balance</span>
              <span className="transfer-balance-amount">${userBalance}</span>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="error-banner"
              >
                <AlertCircle size={20} />
                <span>{error}</span>
              </motion.div>
            )}

            <div className="form-group">
              <label>Recipient Card Number or Email</label>
              <div className="input-wrapper">
                <CreditCard className="input-icon" size={20} />
                <input
                  type="text"
                  placeholder="e.g. 4111222233334444 or user@domain.com"
                  value={receiverInput}
                  onChange={(e) => setReceiverInput(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Amount (USD)</label>
              <div className="input-wrapper amount-input">
                <span className="input-icon">$</span>
                <input
                  type="number"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  step="0.01"
                  min="0.01"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Encryption & Privacy Level</label>
              <div className="privacy-grid">
                <label className="privacy-option">
                  <input
                    type="radio"
                    name="privacy"
                    value="standard"
                    checked={privacyLevel === 'standard'}
                    onChange={(e) => setPrivacyLevel(e.target.value)}
                  />
                  <div className="privacy-content">
                    <Shield size={24} />
                    <strong>Standard</strong>
                  </div>
                </label>
                
                <label className="privacy-option">
                  <input
                    type="radio"
                    name="privacy"
                    value="private_metadata"
                    checked={privacyLevel === 'private_metadata'}
                    onChange={(e) => setPrivacyLevel(e.target.value)}
                  />
                  <div className="privacy-content">
                    <EyeOff size={24} />
                    <strong>Private Data</strong>
                  </div>
                </label>

                <label className="privacy-option">
                  <input
                    type="radio"
                    name="privacy"
                    value="high_privacy"
                    checked={privacyLevel === 'high_privacy'}
                    onChange={(e) => setPrivacyLevel(e.target.value)}
                  />
                  <div className="privacy-content">
                    <Lock size={24} />
                    <strong>Max Privacy</strong>
                  </div>
                </label>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className="transfer-btn"
              disabled={loading || !receiverInput || !amount}
            >
              {loading ? 'Processing Transfer...' : 'Send Funds Securely'}
              {!loading && <ArrowRight size={20} />}
            </motion.button>
          </form>
        )}
      </motion.div>
    </div>
  )
}
