import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Users, CheckCircle, XCircle, Clock, LogOut } from 'lucide-react'
import { api } from '../services/api'
import './AuthorityDashboard.css'

interface KYCRequest {
  id: number
  user_id: number
  email: string
  username: string
  status: string
  created_at: string
}

export default function AuthorityDashboard() {
  const [statistics, setStatistics] = useState<any>(null)
  const [kycRequests, setKycRequests] = useState<KYCRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState<number | null>(null)
  const [reason, setReason] = useState('')
  const [selectedRequest, setSelectedRequest] = useState<number | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [statsRes, kycRes] = await Promise.all([
          api.get('/transactions/authority/dashboard/'),
          api.get('/transactions/authority/kyc/'),
        ])

        setStatistics(statsRes.data)
        setKycRequests(kycRes.data.kyc_requests)
      } catch (err) {
        console.error('Failed to load authority data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const handleApproveKYC = async (kycId: number) => {
    setProcessing(kycId)
    try {
      await api.post(`/transactions/authority/kyc/${kycId}/approve/`, {
        action: 'approve',
        reason: reason || 'Approved by authority',
      })
      // Refresh KYC list
      const res = await api.get('/transactions/authority/kyc/')
      setKycRequests(res.data.kyc_requests)
      setReason('')
      setSelectedRequest(null)
    } catch (err) {
      console.error('Failed to approve KYC:', err)
    } finally {
      setProcessing(null)
    }
  }

  const handleRejectKYC = async (kycId: number) => {
    setProcessing(kycId)
    try {
      await api.post(`/transactions/authority/kyc/${kycId}/approve/`, {
        action: 'reject',
        reason: reason || 'Rejected by authority',
      })
      // Refresh KYC list
      const res = await api.get('/transactions/authority/kyc/')
      setKycRequests(res.data.kyc_requests)
      setReason('')
      setSelectedRequest(null)
    } catch (err) {
      console.error('Failed to reject KYC:', err)
    } finally {
      setProcessing(null)
    }
  }

  const handleLogout = () => {
    localStorage.clear()
    window.location.href = '/authority-login'
  }

  if (loading) {
    return (
      <div className="authority-container">
        <div className="loading">
          <div className="spinner"></div>
          Loading authority panel...
        </div>
      </div>
    )
  }

  return (
    <div className="authority-container">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="authority-header"
      >
        <div className="header-content">
          <h1>Central Authority Dashboard</h1>
          <p>User Verification & Key Management</p>
        </div>
        <button className="logout-btn" onClick={handleLogout}>
          <LogOut size={20} />
          Logout
        </button>
      </motion.div>

      <div className="authority-content">
        {/* Statistics Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="stat-grid"
        >
          <div className="stat-card">
            <Users size={32} color="#4facfe" />
            <div className="stat-info">
              <h3>Total Users</h3>
              <p className="stat-value">{statistics?.total_users || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <CheckCircle size={32} color="#34d399" />
            <div className="stat-info">
              <h3>Verified Users</h3>
              <p className="stat-value">{statistics?.verified_users || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <Clock size={32} color="#fbbf24" />
            <div className="stat-info">
              <h3>Pending KYC</h3>
              <p className="stat-value">{statistics?.pending_kyc_requests || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <XCircle size={32} color="#ef4444" />
            <div className="stat-info">
              <h3>Rejection Rate</h3>
              <p className="stat-value">{statistics?.rejection_rate || '0%'}</p>
            </div>
          </div>
        </motion.div>

        {/* KYC Management */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="kyc-section"
        >
          <h2>KYC Requests Management</h2>

          {kycRequests.length === 0 ? (
            <div className="empty-state">
              <CheckCircle size={48} />
              <p>No pending KYC requests</p>
              <small>All users have been processed</small>
            </div>
          ) : (
            <div className="kyc-grid">
              {kycRequests.map((request) => (
                <motion.div
                  key={request.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className={`kyc-card ${selectedRequest === request.id ? 'expanded' : ''}`}
                >
                  <div className="kyc-header">
                    <div className="kyc-info">
                      <h3>{request.email}</h3>
                      <p>@{request.username}</p>
                      <small>ID: {request.user_id}</small>
                    </div>
                    <span className="status-badge pending">
                      <Clock size={16} />
                      Pending
                    </span>
                  </div>

                  <div className="kyc-date">
                    Submitted: {new Date(request.created_at).toLocaleDateString()}
                  </div>

                  {selectedRequest === request.id && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="kyc-actions"
                    >
                      <textarea
                        placeholder="Enter approval/rejection reason (optional)"
                        value={selectedRequest === request.id ? reason : ''}
                        onChange={(e) => setReason(e.target.value)}
                        className="reason-input"
                      />

                      <div className="action-buttons">
                        <button
                          className="btn-approve"
                          onClick={() => handleApproveKYC(request.id)}
                          disabled={processing === request.id}
                        >
                          <CheckCircle size={18} />
                          {processing === request.id ? 'Processing...' : 'Approve'}
                        </button>
                        <button
                          className="btn-reject"
                          onClick={() => handleRejectKYC(request.id)}
                          disabled={processing === request.id}
                        >
                          <XCircle size={18} />
                          {processing === request.id ? 'Processing...' : 'Reject'}
                        </button>
                        <button
                          className="btn-cancel"
                          onClick={() => {
                            setSelectedRequest(null)
                            setReason('')
                          }}
                          disabled={processing === request.id}
                        >
                          Cancel
                        </button>
                      </div>
                    </motion.div>
                  )}

                  {selectedRequest !== request.id && (
                    <button
                      className="expand-btn"
                      onClick={() => setSelectedRequest(request.id)}
                    >
                      Review
                    </button>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}


