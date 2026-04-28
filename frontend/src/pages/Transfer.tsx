import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Send, Users, ArrowRight, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import './Transfer.css'

export default function Transfer() {
  const [users, setUsers] = useState<any[]>([])
  const [receiverId, setReceiverId] = useState('')
  const [amount, setAmount] = useState('')
  const [privacyLevel, setPrivacyLevel] = useState('standard')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [userBalance, setUserBalance] = useState('0.00')
  const [transactionDetails, setTransactionDetails] = useState<any>(null)

  useEffect(() => {
    // Fetch user's balance
    const fetchBalance = async () => {
      try {
        const response = await api.get('/transactions/balance/')
        setUserBalance(response.data.balance)
      } catch (err) {
        console.error('Failed to fetch balance:', err)
      }
    }

    // Fetch list of users for receiver selection
    const fetchUsers = async () => {
      try {
        const response = await api.get('/users/')
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
        const otherUsers = response.data.filter((u: any) => u.id !== currentUser.id)
        setUsers(otherUsers)
      } catch (err) {
        console.error('Failed to fetch users:', err)
      }
    }

    fetchBalance()
    fetchUsers()
  }, [])

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (!receiverId) {
      setError('Please select a receiver')
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

    try {
      const response = await api.post('/transactions/transfer/create/', {
        receiver_id: parseInt(receiverId),
        amount: parseFloat(amount),
        privacy_level: privacyLevel,
      })

      setTransactionDetails(response.data.transaction)
      setUserBalance(response.data.sender_new_balance)
      setSuccess(true)
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
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="transfer-card"
      >
        <div className="transfer-header">
          <Send size={40} className="transfer-icon" />
          <h1>Transfer Funds</h1>
          <p>Send encrypted funds to another secure account</p>
        </div>

        {success && transactionDetails ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="success-section"
          >
            <CheckCircle size={60} className="success-icon" />
            <h2>Transfer Successful!</h2>
            <p>Your funds have been securely transferred</p>

            <div className="transfer-details">
              <div className="detail-row">
                <span>Transaction ID:</span>
                <strong>#{transactionDetails.id}</strong>
              </div>
              <div className="detail-row">
                <span>To:</span>
                <strong>{transactionDetails.receiver}</strong>
              </div>
              <div className="detail-row">
                <span>Amount:</span>
                <strong className="amount-green">${transactionDetails.amount}</strong>
              </div>
              <div className="detail-row">
                <span>Privacy Level:</span>
                <strong>{transactionDetails.privacy_level}</strong>
              </div>
              <div className="detail-row">
                <span>Your New Balance:</span>
                <strong className="amount-green">${userBalance}</strong>
              </div>
              <div className="detail-row">
                <span>Transaction Hash:</span>
                <code className="hash">{transactionDetails.transaction_hash.substring(0, 32)}...</code>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="transfer-button"
              onClick={() => {
                setSuccess(false)
                setAmount('')
                setReceiverId('')
              }}
            >
              Make Another Transfer
            </motion.button>
          </motion.div>
        ) : (
          <motion.form
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            onSubmit={handleTransfer}
            className="transfer-form"
          >
            <div className="balance-section">
              <p>Available Balance: <strong>${userBalance}</strong></p>
            </div>

            <div className="form-group">
              <label>Send To</label>
              <div className="select-wrapper">
                <Users size={20} />
                <select
                  value={receiverId}
                  onChange={(e) => setReceiverId(e.target.value)}
                  required
                >
                  <option value="">Select recipient...</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.email} ({user.username})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Amount</label>
              <div className="amount-input">
                <span className="currency">$</span>
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
              <label>Privacy Level</label>
              <div className="privacy-options">
                <label className="privacy-option">
                  <input
                    type="radio"
                    name="privacy"
                    value="standard"
                    checked={privacyLevel === 'standard'}
                    onChange={(e) => setPrivacyLevel(e.target.value)}
                  />
                  <span>
                    <strong>Standard</strong>
                    <small>Basic transaction</small>
                  </span>
                </label>
                <label className="privacy-option">
                  <input
                    type="radio"
                    name="privacy"
                    value="private_metadata"
                    checked={privacyLevel === 'private_metadata'}
                    onChange={(e) => setPrivacyLevel(e.target.value)}
                  />
                  <span>
                    <strong>Private Metadata</strong>
                    <small>Metadata encrypted</small>
                  </span>
                </label>
                <label className="privacy-option">
                  <input
                    type="radio"
                    name="privacy"
                    value="high_privacy"
                    checked={privacyLevel === 'high_privacy'}
                    onChange={(e) => setPrivacyLevel(e.target.value)}
                  />
                  <span>
                    <strong>High Privacy</strong>
                    <small>Full encryption</small>
                  </span>
                </label>
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
              className="transfer-button"
              disabled={loading || !receiverId || !amount}
            >
              {loading ? 'Processing Transfer...' : 'Send Funds'}
              <ArrowRight size={20} />
            </motion.button>
          </motion.form>
        )}
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="transfer-info"
      >
        <h3>Security Features</h3>
        <ul>
          <li><strong>RSA Encryption:</strong> Recipient's public key used for encryption</li>
          <li><strong>ECC Signatures:</strong> Digital signatures for transaction authentication</li>
          <li><strong>HMAC Verification:</strong> Integrity check to detect tampering</li>
          <li><strong>Transaction Hash:</strong> Tamper-proof record in blockchain-style chain</li>
          <li><strong>Privacy Levels:</strong> Choose your encryption level for each transfer</li>
        </ul>
      </motion.div>
    </div>
  )
}
