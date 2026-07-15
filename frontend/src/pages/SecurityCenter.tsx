import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, Monitor, MapPin, AlertTriangle, Clock, ChevronLeft, Trash2, Flag, UserPlus } from 'lucide-react'
import { api } from '../services/api'
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

export default function SecurityCenter() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<'logins' | 'devices' | 'alerts'>('logins')
  const [logins, setLogins] = useState<LoginEvent[]>([])
  const [devices, setDevices] = useState<TrustedDevice[]>([])
  const [alerts, setAlerts] = useState<SecurityAlertItem[]>([])
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')
  const [showScanner, setShowScanner] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    setErrorMsg('')
    try {
      const [loginsRes, devicesRes, alertsRes] = await Promise.all([
        api.get('/security/me/login-history/'),
        api.get('/security/me/devices/'),
        api.get('/security/me/alerts/'),
      ])
      setLogins(loginsRes.data.results || loginsRes.data || [])
      setDevices(devicesRes.data.results || devicesRes.data || [])
      setAlerts(alertsRes.data.results || alertsRes.data || [])
    } catch (err: any) {
      console.error('Failed to load security data', err)
      setErrorMsg(err.message || 'Failed to connect to backend server.')
    } finally {
      setLoading(false)
    }
  }

  const removeDevice = async (deviceId: number) => {
    try {
      await api.post(`/security/me/devices/${deviceId}/remove/`)
      setDevices(prev => prev.filter(d => d.id !== deviceId))
    } catch (err) {
      console.error('Failed to remove device', err)
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

  const handleEnrollFace = async (hash: string) => {
    try {
      await api.post('/security/me/devices/enroll-face/', { face_signature_hash: hash })
      alert('Face biometric profile successfully enrolled on this device!')
      fetchData() // refresh to show enrolled status
    } catch (err) {
      console.error('Failed to enroll face', err)
      alert('Failed to enroll face biometric.')
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
          <h1><Shield size={28} /> Security Center</h1>
          <p className="sc-subtitle">Monitor your account security, devices, and login activity</p>
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
          <div className="sc-loading" style={{ color: '#ef4444' }}>{errorMsg}</div>
        ) : (
          <div className="sc-content">
            {tab === 'logins' && (
              <div className="sc-list">
                {logins.length === 0 && <p className="sc-empty">No login events recorded yet.</p>}
                {logins.map(login => (
                  <div key={login.id} className={`sc-login-item ${login.is_successful ? '' : 'failed'}`}>
                    <div className="sc-login-main">
                      <div className="sc-login-info">
                        <span className="sc-browser">{login.browser} / {login.os}</span>
                        <span className="sc-ip"><MapPin size={12} /> {login.city}, {login.country} • {login.ip_address}</span>
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
                {devices.length === 0 && <p className="sc-empty">No trusted devices.</p>}
                
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
                  <button 
                    className="sc-report-btn" 
                    style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa', borderColor: 'rgba(59,130,246,0.2)' }}
                    onClick={() => setShowScanner(true)}
                  >
                    <UserPlus size={14} /> Enroll Face on Current Device
                  </button>
                </div>

                {devices.map(device => (
                  <div key={device.id} className="sc-device-item">
                    <div className="sc-device-info">
                      <Monitor size={20} />
                      <div>
                        <span className="sc-device-name">{device.name}</span>
                        <span className="sc-device-detail">{device.browser} / {device.os}</span>
                        <span className="sc-device-last">Last used: {new Date(device.last_used).toLocaleDateString()}</span>
                        {device.has_face_biometric && <span className="sc-face-badge">🔐 Face enrolled</span>}
                      </div>
                    </div>
                    <button className="sc-remove-btn" onClick={() => removeDevice(device.id)}>
                      <Trash2 size={14} /> Remove
                    </button>
                  </div>
                ))}
              </div>
            )}

            {tab === 'alerts' && (
              <div className="sc-list">
                {alerts.length === 0 && <p className="sc-empty">No security alerts.</p>}
                {alerts.map(a => (
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
        onScanSuccess={handleEnrollFace} 
        title="Enroll Face Biometric" 
      />
    </div>
  )
}
