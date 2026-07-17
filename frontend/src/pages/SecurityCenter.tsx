import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Shield,
  Monitor,
  MapPin,
  AlertTriangle,
  Clock,
  ChevronLeft,
  Trash2,
  Flag,
  UserPlus,
  RefreshCw,
  Fingerprint,
  CheckCircle2,
} from 'lucide-react'
import { api } from '../services/api'
import { useAutoRefresh } from '../hooks/useAutoRefresh'
import { emitDataRefresh } from '../utils/refreshBus'
import BiometricScannerModal from '../components/BiometricScannerModal'
import './SecurityCenter.css'

interface LoginEvent {
  id: number
  ip_address: string
  browser: string
  os: string
  country: string
  city: string
  risk_score: number
  risk_level: string
  face_biometric_verified: boolean
  is_successful: boolean
  created_at: string
}

interface TrustedDevice {
  id: number
  browser: string
  os: string
  name: string
  has_face_biometric: boolean
  trust_status: string
  last_used: string
}

interface SecurityAlertItem {
  id: number
  alert_type: string
  severity: string
  message: string
  is_resolved: boolean
  created_at: string
}

interface PasskeyStatus {
  enrolled: boolean
  count: number
  credentials: Array<{
    id: number
    device_name: string
    created_at: string
    last_used_at: string
    credential_id_preview: string
  }>
}

export default function SecurityCenter() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<'logins' | 'devices' | 'alerts'>('logins')
  const [logins, setLogins] = useState<LoginEvent[]>([])
  const [devices, setDevices] = useState<TrustedDevice[]>([])
  const [alerts, setAlerts] = useState<SecurityAlertItem[]>([])
  const [transactionFrozen, setTransactionFrozen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')
  const [showScanner, setShowScanner] = useState(false)
  const [scannerMode, setScannerMode] = useState<'enroll' | 'verify'>('enroll')
  const [scannerOverwrite, setScannerOverwrite] = useState(false)
  const [scannerTitle, setScannerTitle] = useState('Enroll Passkey')
  const [passkeyStatus, setPasskeyStatus] = useState<PasskeyStatus | null>(null)
  const [passkeyMsg, setPasskeyMsg] = useState('')
  const [deviceMsg, setDeviceMsg] = useState('')
  const [removingDeviceId, setRemovingDeviceId] = useState<number | null>(null)

  const fetchData = async () => {
    setErrorMsg('')
    try {
      const [loginsRes, devicesRes, alertsRes, statusRes, passkeyRes] = await Promise.all([
        api.get('/security/me/login-history/'),
        api.get('/security/me/devices/'),
        api.get('/security/me/alerts/'),
        api.get('/auth/profile/'),
        api.get('/security/webauthn/status/').catch(() => ({ data: null })),
      ])
      setLogins(loginsRes.data.results || loginsRes.data || [])
      setDevices(devicesRes.data.results || devicesRes.data || [])
      setAlerts(alertsRes.data.results || alertsRes.data || [])
      setTransactionFrozen(statusRes.data.transaction_frozen || false)
      setPasskeyStatus(passkeyRes.data)
    } catch (err: any) {
      console.error('Failed to load security data', err)
      setErrorMsg(err.message || 'Failed to connect to backend server.')
    } finally {
      setLoading(false)
    }
  }

  useAutoRefresh(fetchData, { scope: 'security', intervalMs: 5000 })

  const openEnroll = (overwrite = false) => {
    setScannerMode('enroll')
    setScannerOverwrite(overwrite)
    setScannerTitle(overwrite ? 'Replace / Update Passkey' : 'Enroll Passkey')
    setShowScanner(true)
  }

  const openVerify = () => {
    setScannerMode('verify')
    setScannerOverwrite(false)
    setScannerTitle('Verify Biometrics')
    setShowScanner(true)
  }

  const removePasskeys = async () => {
    if (!confirm('Remove all enrolled passkeys for this account?')) return
    try {
      await api.delete('/security/webauthn/clear/')
      setPasskeyMsg('All passkeys removed. You can enroll a new one.')
      emitDataRefresh('security')
      fetchData()
    } catch (err: any) {
      setPasskeyMsg(err.response?.data?.error || 'Failed to remove passkeys.')
    }
  }

  const removeDevice = async (deviceId: number, deviceName: string) => {
    if (
      !confirm(
        `Remove "${deviceName}" from trusted devices?\n\nAny active session on that device will be signed out immediately.`
      )
    ) {
      return
    }

    setRemovingDeviceId(deviceId)
    setDeviceMsg('')
    try {
      const res = await api.post(`/security/me/devices/${deviceId}/remove/`)
      setDeviceMsg(res.data.message || 'Device removed successfully.')
      emitDataRefresh('all')

      if (res.data.revoked_current_device) {
        localStorage.clear()
        window.location.href = '/login?revoked=1'
        return
      }

      setDevices((prev) => prev.filter((d) => d.id !== deviceId))
      fetchData()
    } catch (err: any) {
      setDeviceMsg(
        err.response?.data?.error ||
          err.response?.data?.detail ||
          'Failed to remove device. Please try again.'
      )
    } finally {
      setRemovingDeviceId(null)
    }
  }

  const reportNotMe = async (loginId: number) => {
    try {
      await api.post(`/security/me/report-not-me/${loginId}/`)
      alert('Report submitted. Our security team will review it.')
    } catch (err) {
      console.error('Failed to report', err)
    }
  }

  const handleScannerSuccess = async (result: string) => {
    if (result === 'webauthn_verified') {
      setPasskeyMsg('Biometric verification succeeded — your passkey works.')
    } else {
      setPasskeyMsg('Passkey enrolled. You can now use Passkey / Face ID on the login page.')
    }
    emitDataRefresh('security')
    fetchData()
  }

  const handleToggleFreeze = async () => {
    try {
      const action = transactionFrozen ? 'unfreeze' : 'freeze'
      const res = await api.post('/users/profile/freeze/', { action })
      setTransactionFrozen(res.data.is_frozen)
      emitDataRefresh('all')
      alert(res.data.message)
    } catch (err) {
      console.error('Failed to toggle freeze:', err)
      alert('Failed to update account freeze status.')
    }
  }

  const riskColor = (level: string) => {
    if (level === 'high') return '#ef4444'
    if (level === 'medium') return '#f59e0b'
    return '#22c55e'
  }

  return (
    <div className="sc-container">
      <motion.div
        className="sc-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="sc-header">
          <button className="sc-back" onClick={() => navigate('/dashboard')}>
            <ChevronLeft size={20} /> Back
          </button>
          <h1>
            <Shield size={28} /> Security Center
          </h1>
          <p className="sc-subtitle">Monitor your account security, devices, and login activity</p>
        </div>

        <div
          className="emergency-lockdown-card"
          style={{
            margin: '0 32px 24px 32px',
            padding: '16px',
            background: transactionFrozen ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${transactionFrozen ? '#10b981' : '#ef4444'}`,
            borderRadius: '12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <h3
              style={{
                margin: '0 0 4px 0',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                color: transactionFrozen ? '#10b981' : '#ef4444',
              }}
            >
              <AlertTriangle size={20} /> Emergency Lockdown
            </h3>
            <p style={{ margin: 0, fontSize: '14px', color: '#94a3b8' }}>
              {transactionFrozen
                ? 'Your account transactions are currently frozen.'
                : 'Instantly freeze your account to block all outgoing transactions.'}
            </p>
          </div>
          <button
            onClick={handleToggleFreeze}
            style={{
              padding: '8px 16px',
              background: transactionFrozen ? '#10b981' : '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            {transactionFrozen ? 'Unfreeze Account' : 'Freeze Account'}
          </button>
        </div>

        <div
          style={{
            margin: '0 32px 24px 32px',
            padding: '16px',
            background: 'rgba(59,130,246,0.08)',
            border: '1px solid rgba(59,130,246,0.25)',
            borderRadius: '12px',
          }}
        >
          <h3 style={{ margin: '0 0 8px 0', display: 'flex', alignItems: 'center', gap: 8, color: '#60a5fa' }}>
            <Fingerprint size={20} /> Passkey / Face ID
          </h3>
          <p style={{ margin: '0 0 12px 0', fontSize: 14, color: '#94a3b8' }}>
            {passkeyStatus?.enrolled
              ? `${passkeyStatus.count} passkey(s) enrolled. Use Verify to confirm it works, or Replace to overwrite.`
              : 'No passkey enrolled yet. Enroll once, then you can log in with Passkey / Face ID.'}
          </p>
          {passkeyMsg && (
            <p style={{ margin: '0 0 12px 0', fontSize: 13, color: '#86efac', display: 'flex', gap: 6, alignItems: 'center' }}>
              <CheckCircle2 size={14} /> {passkeyMsg}
            </p>
          )}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <button className="sc-report-btn" style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa' }} onClick={() => openEnroll(false)}>
              <UserPlus size={14} /> Enroll Passkey
            </button>
            <button className="sc-report-btn" style={{ background: 'rgba(245,158,11,0.15)', color: '#fbbf24' }} onClick={() => openEnroll(true)}>
              <RefreshCw size={14} /> Replace / Update
            </button>
            <button
              className="sc-report-btn"
              style={{ background: 'rgba(34,197,94,0.15)', color: '#4ade80' }}
              onClick={openVerify}
              disabled={!passkeyStatus?.enrolled}
            >
              <Fingerprint size={14} /> Verify Biometrics
            </button>
            <button
              className="sc-report-btn"
              style={{ background: 'rgba(239,68,68,0.12)', color: '#f87171' }}
              onClick={removePasskeys}
              disabled={!passkeyStatus?.enrolled}
            >
              <Trash2 size={14} /> Remove Passkeys
            </button>
          </div>
        </div>

        <div className="sc-tabs">
          <button className={tab === 'logins' ? 'active' : ''} onClick={() => setTab('logins')}>
            <Clock size={16} /> Login History
          </button>
          <button className={tab === 'devices' ? 'active' : ''} onClick={() => setTab('devices')}>
            <Monitor size={16} /> Devices
          </button>
          <button className={tab === 'alerts' ? 'active' : ''} onClick={() => setTab('alerts')}>
            <AlertTriangle size={16} /> Alerts
          </button>
        </div>

        {loading ? (
          <div className="sc-loading">Loading security data...</div>
        ) : errorMsg ? (
          <div className="sc-loading" style={{ color: '#ef4444' }}>
            {errorMsg}
          </div>
        ) : (
          <div className="sc-content">
            {tab === 'logins' && (
              <div className="sc-list">
                {logins.length === 0 && <p className="sc-empty">No login events recorded yet.</p>}
                {logins.map((login) => (
                  <div key={login.id} className={`sc-login-item ${login.is_successful ? '' : 'failed'}`}>
                    <div className="sc-login-main">
                      <div className="sc-login-info">
                        <span className="sc-browser">
                          {login.browser} / {login.os}
                        </span>
                        <span className="sc-ip">
                          <MapPin size={12} /> {login.city}, {login.country} • {login.ip_address}
                        </span>
                        <span className="sc-time">{new Date(login.created_at).toLocaleString()}</span>
                      </div>
                      <div className="sc-login-risk">
                        <span className="sc-risk-badge" style={{ background: riskColor(login.risk_level) }}>
                          {login.risk_level.toUpperCase()} ({login.risk_score})
                        </span>
                        {login.face_biometric_verified && <span className="sc-face-badge">🔐 Face</span>}
                        {!login.is_successful && <span className="sc-fail-badge">FAILED</span>}
                      </div>
                    </div>
                    {login.is_successful && (
                      <button className="sc-report-btn" onClick={() => reportNotMe(login.id)}>
                        <Flag size={14} /> Not me
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {tab === 'devices' && (
              <div className="sc-list">
                {deviceMsg && (
                  <p style={{ margin: '0 0 12px 0', fontSize: 13, color: '#86efac' }}>
                    {deviceMsg}
                  </p>
                )}
                {devices.length === 0 && <p className="sc-empty">No trusted devices.</p>}
                {devices.map((device) => (
                  <div key={device.id} className="sc-device-item">
                    <div className="sc-device-info">
                      <Monitor size={20} />
                      <div>
                        <span className="sc-device-name">{device.name}</span>
                        <span className="sc-device-detail">
                          {device.browser} / {device.os}
                        </span>
                        <span className="sc-device-last">
                          Last used: {new Date(device.last_used).toLocaleDateString()}
                        </span>
                        {device.has_face_biometric && <span className="sc-face-badge">🔐 Face enrolled</span>}
                      </div>
                    </div>
                    <button
                      className="sc-remove-btn"
                      onClick={() => removeDevice(device.id, device.name)}
                      disabled={removingDeviceId === device.id}
                    >
                      <Trash2 size={14} /> {removingDeviceId === device.id ? 'Removing...' : 'Remove'}
                    </button>
                  </div>
                ))}
              </div>
            )}

            {tab === 'alerts' && (
              <div className="sc-list">
                {alerts.length === 0 && <p className="sc-empty">No security alerts.</p>}
                {alerts.map((a) => (
                  <div key={a.id} className={`sc-alert-item severity-${a.severity}`}>
                    <AlertTriangle size={16} />
                    <div className="sc-alert-body">
                      <span className="sc-alert-type">{a.alert_type.replace(/_/g, ' ')}</span>
                      <span className="sc-alert-msg">{a.message}</span>
                      <span className="sc-alert-time">{new Date(a.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </motion.div>

      <BiometricScannerModal
        isOpen={showScanner}
        onClose={() => setShowScanner(false)}
        onScanSuccess={handleScannerSuccess}
        title={scannerTitle}
        mode={scannerMode}
        overwrite={scannerOverwrite}
      />
    </div>
  )
}
