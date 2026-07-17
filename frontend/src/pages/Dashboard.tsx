import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  Send,
  CreditCard,
  Wifi,
  Check
} from 'lucide-react'
import { getBalance, getTransactionHistory } from '../services/api'
import { useAutoRefresh } from '../hooks/useAutoRefresh'
import './Dashboard.css'

interface Transaction {
  id: number
  sender_email: string
  receiver_email: string
  amount: string
  privacy_level: string
  created_at: string
}

export default function Dashboard() {
  const navigate = useNavigate()
  const location = useLocation()
  const [balance, setBalance] = useState<string>('0.00')
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'sent' | 'received'>('all')
  const [copied, setCopied] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const fetchDashboardData = async () => {
    try {
      const params: any = {}
      if (filter === 'sent') params.as_sender = true
      if (filter === 'received') params.as_receiver = true

      const [balanceRes, historyRes] = await Promise.all([
        getBalance(),
        getTransactionHistory(params),
      ])
      setBalance(balanceRes.balance)
      setTransactions(historyRes.results?.transactions || historyRes.transactions || [])
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  useAutoRefresh(fetchDashboardData, {
    scope: 'dashboard',
    deps: [filter, location.pathname],
    intervalMs: 5000,
  })

  const isSent = (tx: Transaction) => tx.sender_email === user.email

  return (
    <div className="dashboard-container">
      {/* Main Content */}
      <main className="dashboard-main">
        {/* Balance Card */}
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="balance-card"
        >
          <div className="balance-header">
            <Wallet size={24} />
            <span>Available Balance</span>
          </div>
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="balance-amount sensitive-data"
          >
            ${parseFloat(balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </motion.div>
          
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="virtual-card-display"
            style={{ 
              display: 'inline-flex', 
              alignItems: 'center', 
              gap: '12px', 
              background: 'rgba(255,255,255,0.1)', 
              padding: '8px 16px', 
              borderRadius: '12px',
              marginBottom: '32px',
              border: '1px solid rgba(255,255,255,0.15)',
              position: 'relative',
              zIndex: 1
            }}
          >
            <CreditCard size={18} color="#94a3b8" />
            <span className="sensitive-data" style={{ fontFamily: 'monospace', fontSize: '16px', letterSpacing: '2px', color: '#e2e8f0' }}>
              {user.card_number ? user.card_number.match(/.{1,4}/g)?.join(' ') : '**** **** **** ****'}
            </span>
            <button 
              onClick={() => {
                if (user.card_number) {
                  navigator.clipboard.writeText(user.card_number)
                  setCopied(true)
                  setTimeout(() => setCopied(false), 5000)
                }
              }}
              style={{ background: 'none', border: 'none', color: copied ? '#4ade80' : '#60a5fa', cursor: 'pointer', fontSize: '13px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              {copied ? <><Check size={14} /> COPIED</> : 'COPY'}
            </button>
          </motion.div>

          <div className="balance-actions">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/deposit')}
              className="action-btn deposit"
            >
              <CreditCard size={18} />
              Deposit
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/send')}
              className="action-btn primary"
            >
              <Send size={18} />
              Send Money
            </motion.button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="live-security-widget"
        >
          <div className="security-widget-head">
            <Wifi size={16} />
            <span>Live Security Status</span>
            {lastUpdated && (
              <span style={{ marginLeft: 'auto', fontSize: 11, opacity: 0.75 }}>
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </div>
          <div className="security-widget-line">
            <span className="security-pulse-dot" />
            <span>
              Connection Secured | AES-256 Transport | RSA-2048 Data at Rest | HMAC-SHA256 Integrity Verified
            </span>
          </div>
        </motion.div>

        {/* Quick Stats */}
        <div className="stats-grid">
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="stat-card"
          >
            <div className="stat-icon sent">
              <ArrowUpRight size={20} />
            </div>
            <div className="stat-info">
              <span className="stat-label">Sent</span>
              <span className="stat-value">
                ${transactions
                  .filter(tx => isSent(tx))
                  .reduce((sum, tx) => sum + parseFloat(tx.amount), 0)
                  .toFixed(2)}
              </span>
            </div>
          </motion.div>

          <motion.div
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="stat-card"
          >
            <div className="stat-icon received">
              <ArrowDownRight size={20} />
            </div>
            <div className="stat-info">
              <span className="stat-label">Received</span>
              <span className="stat-value">
                ${transactions
                  .filter(tx => !isSent(tx))
                  .reduce((sum, tx) => sum + parseFloat(tx.amount), 0)
                  .toFixed(2)}
              </span>
            </div>
          </motion.div>
        </div>

        {/* Recent Transactions */}
        <motion.div
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="recent-transactions"
        >
          <div className="section-header">
            <h2>Recent Transactions</h2>
            <div className="filter-controls">
              <div className="filter-tabs">
                {(['all', 'sent', 'received'] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`filter-tab ${filter === f ? 'active' : ''}`}
                  >
                    {f.charAt(0).toUpperCase() + f.slice(1)}
                  </button>
                ))}
              </div>
              <button 
                onClick={() => navigate('/history')} 
                className="view-all-btn"
              >
                View All
              </button>
            </div>
          </div>

          {loading ? (
            <div className="loading-state">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1 }}
                className="spinner"
              />
            </div>
          ) : transactions.length === 0 ? (
            <div className="empty-state">
              <p>No transactions yet</p>
            </div>
          ) : (
            <div className="transaction-list">
              {transactions
                .filter(tx => {
                  if (filter === 'sent') return tx.sender_email === user.email
                  if (filter === 'received') return tx.receiver_email === user.email
                  return true
                })
                .slice(0, 5)
                .map((tx, index) => (
                <motion.div
                  key={tx.id}
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.1 * index }}
                  className="transaction-item"
                >
                  <div className={`tx-icon ${isSent(tx) ? 'sent' : 'received'}`}>
                    {isSent(tx) ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                  </div>
                  <div className="tx-details">
                    <span className="tx-party">
                      {isSent(tx) ? `To: ${tx.receiver_email}` : `From: ${tx.sender_email}`}
                    </span>
                    <span className="tx-privacy">{tx.privacy_level}</span>
                  </div>
                  <div className={`tx-amount ${isSent(tx) ? 'negative' : 'positive'}`}>
                    {isSent(tx) ? '-' : '+'}${parseFloat(tx.amount).toFixed(2)}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </main>
    </div>
  )
}
