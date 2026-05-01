import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Users, Eye, Shield, Activity, LogOut } from 'lucide-react'
import { api } from '../services/api'
import './AdminDashboard.css'

interface AdminUser {
  id: number
  email_encrypted: string
  username_encrypted: string
  role: string
  balance: number
  kyc_status: string
  is_verified: boolean
  is_active: boolean
  created_at: string
}

interface Transaction {
  id: number
  type: string
  status: string
  sender: string
  receiver: string
  amount: string
  privacy_level: string
  hmac_valid?: boolean
  created_at: string
}

export default function AdminDashboard() {
  const [statistics, setStatistics] = useState<any>(null)
  const [users, setUsers] = useState<AdminUser[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTab, setSelectedTab] = useState('overview')
  const [suspending, setSuspending] = useState<number | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [statsRes, usersRes, txRes] = await Promise.all([
          api.get('/transactions/admin/dashboard/'),
          api.get('/transactions/admin/users/'),
          api.get('/transactions/admin/transactions/'),
        ])

        setStatistics(statsRes.data)
        setUsers(usersRes.data.users)
        setTransactions(txRes.data.transactions)
      } catch (err) {
        console.error('Failed to load admin data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const handleSuspendUser = async (userId: number, currentStatus: boolean) => {
    setSuspending(userId)
    try {
      await api.post(`/transactions/admin/users/${userId}/suspend/`, {
        action: currentStatus ? 'suspend' : 'activate',
        reason: 'Admin action',
      })
      // Refresh users list
      const res = await api.get('/transactions/admin/users/')
      setUsers(res.data.users)
    } catch (err) {
      console.error('Failed to suspend user:', err)
    } finally {
      setSuspending(null)
    }
  }

  const handleLogout = () => {
    localStorage.clear()
    window.location.href = '/admin-login'
  }

  if (loading) {
    return (
      <div className="admin-container">
        <div className="loading">
          <div className="spinner"></div>
          Loading admin panel...
        </div>
      </div>
    )
  }

  return (
    <div className="admin-container">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="admin-header"
      >
        <div className="header-content">
          <h1>Admin Dashboard</h1>
          <p>Banking System Administration</p>
        </div>
        <button className="logout-btn" onClick={handleLogout}>
          <LogOut size={20} />
          Logout
        </button>
      </motion.div>

      <div className="admin-content">
        {/* Statistics Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="statistics-grid"
        >
          <div className="stat-card">
            <div className="stat-icon users">
              <Users size={32} />
            </div>
            <div className="stat-info">
              <h3>Total Users</h3>
              <p className="stat-value">{statistics?.total_users || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon active">
              <Shield size={32} />
            </div>
            <div className="stat-info">
              <h3>Active Users</h3>
              <p className="stat-value">{statistics?.active_users || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon suspended">
              <Eye size={32} />
            </div>
            <div className="stat-info">
              <h3>Suspended</h3>
              <p className="stat-value">{statistics?.suspended_users || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon transactions">
              <Activity size={32} />
            </div>
            <div className="stat-info">
              <h3>Transactions</h3>
              <p className="stat-value">{statistics?.total_transactions || 0}</p>
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="admin-tabs"
        >
          <div className="tab-buttons">
            <button
              className={`tab-btn ${selectedTab === 'overview' ? 'active' : ''}`}
              onClick={() => setSelectedTab('overview')}
            >
              Overview
            </button>
            <button
              className={`tab-btn ${selectedTab === 'users' ? 'active' : ''}`}
              onClick={() => setSelectedTab('users')}
            >
              User Management
            </button>
            <button
              className={`tab-btn ${selectedTab === 'transactions' ? 'active' : ''}`}
              onClick={() => setSelectedTab('transactions')}
            >
              Transaction Monitoring
            </button>
          </div>

          {/* Overview Tab */}
          {selectedTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="tab-content"
            >
              <div className="overview-grid">
                <div className="info-card">
                  <h3>Volume Statistics</h3>
                  <div className="info-item">
                    <span>Total Volume:</span>
                    <strong>${statistics?.total_volume || '0.00'}</strong>
                  </div>
                </div>

                <div className="info-card">
                  <h3>System Status</h3>
                  <div className="status-badge active">
                    <span>● All Systems Operational</span>
                  </div>
                  <div className="info-item">
                    <span>Encryption:</span>
                    <strong>RSA + ECC</strong>
                  </div>
                  <div className="info-item">
                    <span>Integrity:</span>
                    <strong>HMAC + Hash Chain</strong>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* User Management Tab */}
          {selectedTab === 'users' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="tab-content"
            >
              <div className="users-table-wrapper">
                <table className="users-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Email</th>
                      <th>Username</th>
                      <th>Balance</th>
                      <th>KYC Status</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td>#{user.id}</td>
                        <td>
                          <code className="encrypted">{user.email_encrypted.substring(0, 20)}...</code>
                        </td>
                        <td>
                          <code className="encrypted">{user.username_encrypted.substring(0, 20)}...</code>
                        </td>
                        <td className="amount">${user.balance.toFixed(2)}</td>
                        <td>
                          <span className={`badge kyc-${user.kyc_status}`}>
                            {user.kyc_status}
                          </span>
                        </td>
                        <td>
                          <span className={`badge status-${user.is_active ? 'active' : 'suspended'}`}>
                            {user.is_active ? 'Active' : 'Suspended'}
                          </span>
                        </td>
                        <td className="date">
                          {new Date(user.created_at).toLocaleDateString()}
                        </td>
                        <td>
                          <button
                            className={`action-btn ${user.is_active ? 'suspend' : 'activate'}`}
                            onClick={() => handleSuspendUser(user.id, user.is_active)}
                            disabled={suspending === user.id}
                          >
                            {suspending === user.id
                              ? 'Processing...'
                              : user.is_active
                              ? 'Suspend'
                              : 'Activate'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* Transaction Monitoring Tab */}
          {selectedTab === 'transactions' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="tab-content"
            >
              <div className="transactions-table-wrapper">
                <table className="transactions-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Type</th>
                      <th>Sender</th>
                      <th>Receiver</th>
                      <th>Amount</th>
                      <th>Privacy</th>
                      <th>HMAC Valid</th>
                      <th>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr key={tx.id}>
                        <td>#{tx.id}</td>
                        <td>
                          <span className={`type-badge ${tx.type}`}>
                            {tx.type.toUpperCase()}
                          </span>
                        </td>
                        <td className="email">{tx.sender}</td>
                        <td className="email">{tx.receiver}</td>
                        <td className="amount">${tx.amount}</td>
                        <td>
                          <span className={`privacy-badge ${tx.privacy_level}`}>
                            {tx.privacy_level}
                          </span>
                        </td>
                        <td>
                          <span className={`integrity-badge ${tx.hmac_valid ? 'valid' : 'invalid'}`}>
                            {tx.hmac_valid ? '✓ Valid' : '✗ Invalid'}
                          </span>
                        </td>
                        <td className="date">
                          {new Date(tx.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
