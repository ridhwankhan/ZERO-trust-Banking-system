import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  ArrowUpRight,
  ArrowDownRight,
  Shield,
  Lock,
  Eye,
  ChevronDown,
  Filter,
  RefreshCw,
  Search
} from 'lucide-react'
import { getTransactionHistory, verifyTransaction } from '../services/api'
import './TransactionHistory.css'

interface Transaction {
  id: number
  sender_email: string
  receiver_email: string
  amount: string
  privacy_level: 'standard' | 'private_metadata' | 'high_privacy'
  encrypted_payload: string | null
  decrypted_payload?: any
  metadata_visible?: any
  hmac_signature: string
  created_at: string
}

const privacyIcons = {
  standard: Eye,
  private_metadata: Lock,
  high_privacy: Shield
}

const privacyColors = {
  standard: '#48bb78',
  private_metadata: '#ed8936',
  high_privacy: '#9f7aea'
}

export default function TransactionHistory() {
  const navigate = useNavigate()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'sent' | 'received'>('all')
  const [privacyFilter, setPrivacyFilter] = useState<string>('all')
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [verifying, setVerifying] = useState<number | null>(null)
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  useEffect(() => {
    fetchTransactions()
  }, [filter, privacyFilter])

  const fetchTransactions = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (filter === 'sent') params.as_sender = true
      if (filter === 'received') params.as_receiver = true
      if (privacyFilter !== 'all') params.privacy_level = privacyFilter
      
      const response = await getTransactionHistory(params)
      setTransactions(response.transactions || [])
    } catch (error) {
      console.error('Failed to fetch transactions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async (id: number) => {
    setVerifying(id)
    try {
      await verifyTransaction(id)
      alert('Transaction verified successfully!')
    } catch (error) {
      alert('Verification failed')
    } finally {
      setVerifying(null)
    }
  }

  const isSent = (tx: Transaction) => tx.sender_email === user.email

  const filteredTransactions = transactions.filter(tx => {
    if (privacyFilter !== 'all' && tx.privacy_level !== privacyFilter) return false
    return true
  })

  return (
    <div className="history-container">
      {/* Header */}
      <motion.header
        initial={{ y: -50 }}
        animate={{ y: 0 }}
        className="history-header"
      >
        <div className="header-left">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => navigate('/dashboard')}
            className="back-btn"
          >
            <ArrowLeft size={24} />
          </motion.button>
          <h1>Transaction History</h1>
        </div>
        <motion.button
          whileHover={{ rotate: 180 }}
          transition={{ duration: 0.3 }}
          onClick={fetchTransactions}
          className="refresh-btn"
        >
          <RefreshCw size={20} />
        </motion.button>
      </motion.header>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="filters-section"
      >
        <div className="filter-tabs">
          {(['all', 'sent', 'received'] as const).map((f) => (
            <motion.button
              key={f}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setFilter(f)}
              className={`filter-tab ${filter === f ? 'active' : ''}`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </motion.button>
          ))}
        </div>

        <div className="privacy-filter">
          <Filter size={16} />
          <select
            value={privacyFilter}
            onChange={(e) => setPrivacyFilter(e.target.value)}
          >
            <option value="all">All Privacy Levels</option>
            <option value="standard">Standard</option>
            <option value="private_metadata">Private Metadata</option>
            <option value="high_privacy">High Privacy</option>
          </select>
        </div>
      </motion.div>

      {/* Transaction List */}
      <main className="history-main">
        {loading ? (
          <div className="loading-state">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1 }}
              className="spinner-large"
            />
          </div>
        ) : filteredTransactions.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="empty-state"
          >
            <Search size={64} />
            <p>No transactions found</p>
            <span>Try adjusting your filters</span>
          </motion.div>
        ) : (
          <div className="transactions-list">
            <AnimatePresence>
              {filteredTransactions.map((tx, index) => {
                const PrivacyIcon = privacyIcons[tx.privacy_level]
                const isExpanded = expandedId === tx.id
                
                return (
                  <motion.div
                    key={tx.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ delay: index * 0.05 }}
                    className={`transaction-card ${isExpanded ? 'expanded' : ''}`}
                    onClick={() => setExpandedId(isExpanded ? null : tx.id)}
                  >
                    {/* Card Header */}
                    <div className="card-header">
                      <div className={`tx-direction ${isSent(tx) ? 'sent' : 'received'}`}>
                        {isSent(tx) ? <ArrowUpRight size={20} /> : <ArrowDownRight size={20} />}
                      </div>
                      
                      <div className="tx-main-info">
                        <div className="tx-party">
                          {isSent(tx) ? (
                            <>
                              Sent to <strong>{tx.receiver_email}</strong>
                            </>
                          ) : (
                            <>
                              Received from <strong>{tx.sender_email}</strong>
                            </>
                          )}
                        </div>
                        <div className="tx-meta">
                          <span className="tx-date">
                            {new Date(tx.created_at).toLocaleDateString()}
                          </span>
                          <span 
                            className="privacy-badge"
                            style={{ background: privacyColors[tx.privacy_level] }}
                          >
                            <PrivacyIcon size={12} />
                            {tx.privacy_level.replace('_', ' ')}
                          </span>
                        </div>
                      </div>

                      <div className={`tx-amount ${isSent(tx) ? 'negative' : 'positive'}`}>
                        {isSent(tx) ? '-' : '+'}${parseFloat(tx.amount).toFixed(2)}
                      </div>

                      <motion.div
                        animate={{ rotate: isExpanded ? 180 : 0 }}
                        className="expand-icon"
                      >
                        <ChevronDown size={20} />
                      </motion.div>
                    </div>

                    {/* Expanded Details */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="card-details"
                        >
                          <div className="detail-section">
                            <h4>Transaction Details</h4>
                            <div className="detail-row">
                              <span>ID</span>
                              <code>{tx.id}</code>
                            </div>
                            <div className="detail-row">
                              <span>HMAC Signature</span>
                              <code className="signature">{tx.hmac_signature.slice(0, 16)}...</code>
                            </div>
                          </div>

                          {/* Decrypted Payload Display */}
                          {tx.decrypted_payload && (
                            <div className="detail-section payload">
                              <h4>Decrypted Information</h4>
                              {typeof tx.decrypted_payload === 'object' ? (
                                <div className="payload-data">
                                  {tx.decrypted_payload.description && (
                                    <div className="payload-item">
                                      <span>Description</span>
                                      <p>{tx.decrypted_payload.description}</p>
                                    </div>
                                  )}
                                  {tx.decrypted_payload.notes && (
                                    <div className="payload-item">
                                      <span>Notes</span>
                                      <p>{tx.decrypted_payload.notes}</p>
                                    </div>
                                  )}
                                  {tx.decrypted_payload.category && (
                                    <div className="payload-item">
                                      <span>Category</span>
                                      <p>{tx.decrypted_payload.category}</p>
                                    </div>
                                  )}
                                  {tx.decrypted_payload.access === 'locked' && (
                                    <div className="payload-locked">
                                      <Lock size={16} />
                                      <p>Private key not in session. Please login again to decrypt.</p>
                                    </div>
                                  )}
                                  {tx.decrypted_payload.access === 'denied' && (
                                    <div className="payload-denied">
                                      <Shield size={16} />
                                      <p>Only the receiver can decrypt this transaction.</p>
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <p className="payload-plaintext">{tx.decrypted_payload}</p>
                              )}
                            </div>
                          )}

                          {/* Metadata for Private Metadata level */}
                          {tx.metadata_visible && (
                            <div className="detail-section metadata">
                              <h4>Visible Metadata</h4>
                              {tx.metadata_visible.category && (
                                <div className="detail-row">
                                  <span>Category</span>
                                  <strong>{tx.metadata_visible.category}</strong>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Actions */}
                          <div className="detail-actions">
                            <motion.button
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              onClick={(e: React.MouseEvent) => {
                                e.stopPropagation()
                                handleVerify(tx.id)
                              }}
                              disabled={verifying === tx.id}
                              className="verify-btn"
                            >
                              {verifying === tx.id ? (
                                <motion.div
                                  animate={{ rotate: 360 }}
                                  transition={{ repeat: Infinity, duration: 1 }}
                                  className="spinner-small"
                                />
                              ) : (
                                <>
                                  <Shield size={16} />
                                  Verify Integrity
                                </>
                              )}
                            </motion.button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </div>
        )}
      </main>
    </div>
  )
}
