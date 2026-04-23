import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  History,
  Send,
  LogOut,
  Shield,
  User
} from 'lucide-react'
import { getBalance, getTransactionHistory, logout } from '../services/api'
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
  const [balance, setBalance] = useState<string>('0.00')
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [balanceRes, historyRes] = await Promise.all([
        getBalance(),
        getTransactionHistory()
      ])
      setBalance(balanceRes.balance)
      setTransactions(historyRes.transactions || [])
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    const refresh = localStorage.getItem('refresh_token')
    if (refresh) {
      try {
        await logout(refresh)
      } catch (error) {
        console.error('Logout error:', error)
      }
    }
    localStorage.clear()
    navigate('/login')
  }

  const isSent = (tx: Transaction) => tx.sender_email === user.email

  return (
    <div className="dashboard-container">
      {/* Header */}
      <motion.header
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="dashboard-header"
      >
        <div className="header-left">
          <Shield size={32} className="header-logo" />
          <h1>ZeroTrust Bank</h1>
        </div>
        <div className="header-right">
          <div className="user-info">
            <User size={20} />
            <span>{user.email}</span>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleLogout}
            className="logout-btn"
          >
            <LogOut size={18} />
          </motion.button>
        </div>
      </motion.header>

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
            className="balance-amount"
          >
            ${parseFloat(balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </motion.div>
          <div className="balance-actions">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/send')}
              className="action-btn primary"
            >
              <Send size={18} />
              Send Money
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/history')}
              className="action-btn secondary"
            >
              <History size={18} />
              History
            </motion.button>
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
            <button onClick={() => navigate('/history')} className="view-all">
              View All
            </button>
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
              {transactions.slice(0, 5).map((tx, index) => (
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
