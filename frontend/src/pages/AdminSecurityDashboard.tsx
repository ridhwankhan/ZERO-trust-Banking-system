import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Shield, Activity, Search, FileCheck, AlertTriangle,
  ChevronLeft, Play, RefreshCw, CheckCircle, XCircle, Eye
} from 'lucide-react'
import { api } from '../services/api'
import './AdminSecurityDashboard.css'

interface DashboardData {
  recent_logins: any[]
  high_risk_users: any[]
  alerts: any[]
  latest_scan: any | null
  latest_integrity: any | null
  device_stats: { total_devices: number; removed_devices: number }
  auth_stats: {
    total_logins: number
    successful_logins: number
    failed_logins: number
    face_biometric_logins: number
    impossible_travel_events: number
  }
}

export default function AdminSecurityDashboard() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<'overview' | 'threats' | 'scanner' | 'integrity'>('overview')
  const [data, setData] = useState<DashboardData | null>(null)
  const [scanHistory, setScanHistory] = useState<any[]>([])
  const [integrityHistory, setIntegrityHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    setLoading(true)
    try {
      const [dashRes, scanRes, intRes] = await Promise.all([
        api.get('/security/admin/dashboard/'),
        api.get('/security/admin/scan/history/'),
        api.get('/security/admin/integrity/history/'),
      ])
      setData(dashRes.data)
      setScanHistory(scanRes.data.results || scanRes.data || [])
      setIntegrityHistory(intRes.data.results || intRes.data || [])
    } catch (err) {
      console.error('Failed to load security dashboard', err)
    } finally {
      setLoading(false)
    }
  }

  const runScan = async () => {
    setScanning(true)
    try {
      await api.post('/security/admin/scan/run/')
      await fetchDashboard()
    } catch (err) {
      console.error('Scan failed', err)
    } finally {
      setScanning(false)
    }
  }

  const runIntegrityCheck = async () => {
    setChecking(true)
    try {
      await api.post('/security/admin/integrity/run/')
      await fetchDashboard()
    } catch (err) {
      console.error('Integrity check failed', err)
    } finally {
      setChecking(false)
    }
  }

  const resolveAlert = async (alertId: number) => {
    try {
      await api.post(`/security/admin/alerts/${alertId}/resolve/`)
      await fetchDashboard()
    } catch (err) {
      console.error('Failed to resolve alert', err)
    }
  }

  const riskColor = (level: string) => {
    if (level === 'high') return '#ef4444'
    if (level === 'medium') return '#f59e0b'
    return '#22c55e'
  }

  if (loading) {
    return (
      <div className="asd-container">
        <div className="asd-loading">Loading Security Dashboard...</div>
      </div>
    )
  }

  const stats = data?.auth_stats

  return (
    <div className="asd-container">
      <motion.div
        className="asd-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="asd-header">
          <button className="asd-back" onClick={() => navigate('/admin-dashboard')}>
            <ChevronLeft size={20} /> Admin Panel
          </button>
          <h1><Shield size={28} /> Security Command Center</h1>
          <p className="asd-subtitle">Zero Trust monitoring, threat detection, scans, and ledger integrity</p>
        </div>

        {/* Stats bar */}
        <div className="asd-stats">
          <div className="stat-box">
            <span className="stat-value">{stats?.total_logins ?? 0}</span>
            <span className="stat-label">Total Logins</span>
          </div>
          <div className="stat-box">
            <span className="stat-value" style={{ color: '#ef4444' }}>{stats?.failed_logins ?? 0}</span>
            <span className="stat-label">Failed Logins</span>
          </div>
          <div className="stat-box">
            <span className="stat-value" style={{ color: '#60a5fa' }}>{stats?.face_biometric_logins ?? 0}</span>
            <span className="stat-label">Face Biometric</span>
          </div>
          <div className="stat-box">
            <span className="stat-value" style={{ color: '#f59e0b' }}>{stats?.impossible_travel_events ?? 0}</span>
            <span className="stat-label">Impossible Travel</span>
          </div>
          <div className="stat-box">
            <span className="stat-value">{data?.device_stats.total_devices ?? 0}</span>
            <span className="stat-label">Trusted Devices</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="asd-tabs">
          <button className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}>
            <Eye size={16} /> Overview
          </button>
          <button className={tab === 'threats' ? 'active' : ''} onClick={() => setTab('threats')}>
            <Activity size={16} /> Threats
          </button>
          <button className={tab === 'scanner' ? 'active' : ''} onClick={() => setTab('scanner')}>
            <Search size={16} /> Scanner
          </button>
          <button className={tab === 'integrity' ? 'active' : ''} onClick={() => setTab('integrity')}>
            <FileCheck size={16} /> Integrity
          </button>
        </div>

        <div className="asd-content">
          {/* OVERVIEW */}
          {tab === 'overview' && (
            <div className="asd-overview">
              <h3>Recent Login Activity</h3>
              <div className="asd-table">
                <div className="asd-table-head">
                  <span>User</span><span>IP</span><span>Location</span>
                  <span>Risk</span><span>Status</span><span>Time</span>
                </div>
                {data?.recent_logins.map((l: any) => (
                  <div key={l.id} className="asd-table-row">
                    <span>{l.user_email || l.email_entered}</span>
                    <span>{l.ip_address}</span>
                    <span>{l.city}, {l.country}</span>
                    <span style={{ color: riskColor(l.risk_level) }}>
                      {l.risk_level.toUpperCase()} ({l.risk_score})
                    </span>
                    <span>{l.is_successful ? '✅' : '❌'}</span>
                    <span>{new Date(l.created_at).toLocaleString()}</span>
                  </div>
                ))}
              </div>

              <h3 style={{ marginTop: '1.5rem' }}>High Risk Users</h3>
              {data?.high_risk_users.length === 0 ? (
                <p className="asd-empty">No high-risk users detected.</p>
              ) : (
                <div className="asd-risk-users">
                  {data?.high_risk_users.map((u: any, i: number) => (
                    <div key={i} className="asd-risk-user">
                      <AlertTriangle size={16} style={{ color: '#ef4444' }} />
                      <span>{u.user__email}</span>
                      <span className="risk-count">{u.count} high-risk events</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* THREATS / ALERTS */}
          {tab === 'threats' && (
            <div className="asd-threats">
              <h3>Active Security Alerts</h3>
              {data?.alerts.length === 0 && <p className="asd-empty">No active alerts.</p>}
              {data?.alerts.map((a: any) => (
                <div key={a.id} className={`asd-alert severity-${a.severity}`}>
                  <AlertTriangle size={16} />
                  <div className="asd-alert-body">
                    <span className="asd-alert-type">{a.alert_type.replace(/_/g, ' ')}</span>
                    <span className="asd-alert-msg">{a.message}</span>
                    <span className="asd-alert-time">{new Date(a.created_at).toLocaleString()}</span>
                  </div>
                  <button className="asd-resolve-btn" onClick={() => resolveAlert(a.id)}>
                    <CheckCircle size={14} /> Resolve
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* SCANNER */}
          {tab === 'scanner' && (
            <div className="asd-scanner">
              <div className="asd-scanner-header">
                <h3>OWASP Security Regression Scanner</h3>
                <button className="asd-action-btn" onClick={runScan} disabled={scanning}>
                  {scanning ? <RefreshCw size={16} className="spinning" /> : <Play size={16} />}
                  {scanning ? 'Scanning...' : 'Run Scan'}
                </button>
              </div>

              {data?.latest_scan && (
                <div className={`asd-scan-result ${data.latest_scan.status}`}>
                  <div className="asd-scan-summary">
                    <span className="asd-scan-status">
                      {data.latest_scan.status === 'pass' ? <CheckCircle size={20} /> : <XCircle size={20} />}
                      {data.latest_scan.status.toUpperCase()}
                    </span>
                    <span>Passed: {data.latest_scan.passed_tests_count}</span>
                    <span>Failed: {data.latest_scan.failed_tests_count}</span>
                    <span>Date: {new Date(data.latest_scan.scan_date).toLocaleString()}</span>
                  </div>
                  <div className="asd-scan-details">
                    {data.latest_scan.details?.map((d: any, i: number) => (
                      <div key={i} className={`asd-scan-test ${d.status}`}>
                        <span>{d.status === 'pass' ? '✅' : '❌'} {d.test_name}</span>
                        <span className="severity-tag">{d.severity}</span>
                        {d.status === 'fail' && <span className="recommendation">{d.recommendation}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <h4 style={{ marginTop: '1.5rem' }}>Scan History</h4>
              {scanHistory.map((s: any) => (
                <div key={s.id} className={`asd-scan-hist ${s.status}`}>
                  <span>{new Date(s.scan_date).toLocaleString()}</span>
                  <span>{s.status.toUpperCase()}</span>
                  <span>P:{s.passed_tests_count} F:{s.failed_tests_count}</span>
                </div>
              ))}
            </div>
          )}

          {/* INTEGRITY */}
          {tab === 'integrity' && (
            <div className="asd-integrity">
              <div className="asd-integrity-header">
                <h3>Ledger Integrity Verification</h3>
                <button className="asd-action-btn" onClick={runIntegrityCheck} disabled={checking}>
                  {checking ? <RefreshCw size={16} className="spinning" /> : <FileCheck size={16} />}
                  {checking ? 'Checking...' : 'Run Check'}
                </button>
              </div>

              {data?.latest_integrity && (
                <div className={`asd-integrity-result ${data.latest_integrity.status}`}>
                  <div className="asd-integrity-summary">
                    <span className={`status-badge ${data.latest_integrity.status}`}>
                      {data.latest_integrity.status === 'secure' ? <CheckCircle size={20} /> : <XCircle size={20} />}
                      {data.latest_integrity.status.toUpperCase()}
                    </span>
                    <span>Verified: {data.latest_integrity.verified_count} transactions</span>
                    <span>Last check: {new Date(data.latest_integrity.check_date).toLocaleString()}</span>
                  </div>
                  {data.latest_integrity.tampered_details?.length > 0 && (
                    <div className="asd-tampered">
                      <h4 style={{ color: '#ef4444' }}>⚠️ Tampered Records</h4>
                      {data.latest_integrity.tampered_details.map((t: any, i: number) => (
                        <div key={i} className="tampered-row">
                          TX #{t.transaction_id}: expected {t.expected_hash?.slice(0, 16)}…, got {t.actual_hash?.slice(0, 16)}…
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <h4 style={{ marginTop: '1.5rem' }}>Check History</h4>
              {integrityHistory.map((r: any) => (
                <div key={r.id} className={`asd-integrity-hist ${r.status}`}>
                  <span>{new Date(r.check_date).toLocaleString()}</span>
                  <span>{r.status.toUpperCase()}</span>
                  <span>{r.verified_count} txns</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}
