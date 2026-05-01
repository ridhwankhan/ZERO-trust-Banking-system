import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowLeft, Save, Shield, User, Mail, Phone, KeyRound, QrCode, CheckCircle2 } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import { enableTwoFactor, getProfile, setupTwoFactor, updateProfile } from '../services/api'
import './Profile.css'

export default function Profile() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false)
  const [setupLoading, setSetupLoading] = useState(false)
  const [setupMode, setSetupMode] = useState(false)
  const [qrValue, setQrValue] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [verificationCode, setVerificationCode] = useState('')
  const [verifying2FA, setVerifying2FA] = useState(false)
  const [twoFactorMessage, setTwoFactorMessage] = useState('')
  const [twoFactorError, setTwoFactorError] = useState('')
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    contact_info: '',
  })

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true)
      setError('')
      try {
        const profile = await getProfile()
        setFormData({
          email: profile.email || '',
          username: profile.username || '',
          contact_info: profile.contact_info || '',
        })
        setTwoFactorEnabled(Boolean(profile.two_factor_enabled))
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to load profile.')
      } finally {
        setLoading(false)
      }
    }

    fetchProfile()
  }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setMessage('')
    try {
      const updated = await updateProfile(formData)
      setFormData({
        email: updated.email || '',
        username: updated.username || '',
        contact_info: updated.contact_info || '',
      })

      const localUser = JSON.parse(localStorage.getItem('user') || '{}')
      localStorage.setItem(
        'user',
        JSON.stringify({
          ...localUser,
          email: updated.email,
          username: updated.username,
          contact_info: updated.contact_info,
        })
      )

      setMessage('Profile updated and securely re-encrypted.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update profile.')
    } finally {
      setSaving(false)
    }
  }

  const handleBeginTwoFactorSetup = async () => {
    setSetupLoading(true)
    setTwoFactorError('')
    setTwoFactorMessage('')
    try {
      const setup = await setupTwoFactor()
      setQrValue(setup.provisioning_uri)
      setBackupCodes(setup.backup_codes || [])
      setSetupMode(true)
      setTwoFactorMessage('Scan the QR and enter your 6-digit code to complete setup.')
    } catch (err: any) {
      setTwoFactorError(err?.response?.data?.error || 'Failed to initialize 2FA setup.')
    } finally {
      setSetupLoading(false)
    }
  }

  const handleEnableTwoFactor = async (e: React.FormEvent) => {
    e.preventDefault()
    setVerifying2FA(true)
    setTwoFactorError('')
    setTwoFactorMessage('')
    try {
      await enableTwoFactor(verificationCode)
      setTwoFactorEnabled(true)
      setSetupMode(false)
      setVerificationCode('')
      setTwoFactorMessage('Two-factor authentication is now active on your account.')
    } catch (err: any) {
      setTwoFactorError(err?.response?.data?.error || 'Invalid verification code.')
    } finally {
      setVerifying2FA(false)
    }
  }

  return (
    <div className="profile-page">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="profile-shell"
      >
        <div className="profile-topbar">
          <button onClick={() => navigate('/dashboard')} className="profile-back-btn">
            <ArrowLeft size={16} />
            Dashboard
          </button>
          <div className="profile-security-pill">
            <Shield size={16} />
            End-to-End Protected Profile
          </div>
        </div>

        <div className="profile-card">
          <div className="profile-card-header">
            <h1>My Profile</h1>
            <p>Manage your identity details with secure encryption at rest.</p>
          </div>

          {message && <div className="profile-alert success">{message}</div>}
          {error && <div className="profile-alert error">{error}</div>}

          {loading ? (
            <div className="profile-loading">Loading your encrypted profile...</div>
          ) : (
            <form onSubmit={handleSave} className="profile-form">
              <label>
                <span>
                  <Mail size={14} />
                  Email
                </span>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </label>

              <label>
                <span>
                  <User size={14} />
                  Username
                </span>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
              </label>

              <label>
                <span>
                  <Phone size={14} />
                  Contact Info (Phone / Address)
                </span>
                <textarea
                  value={formData.contact_info}
                  onChange={(e) => setFormData({ ...formData, contact_info: e.target.value })}
                  rows={4}
                  required
                />
              </label>

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                type="submit"
                className="profile-save-btn"
                disabled={saving}
              >
                <Save size={16} />
                {saving ? 'Saving...' : 'Save Secure Changes'}
              </motion.button>
            </form>
          )}
        </div>

        <div className="profile-card security-card">
          <div className="profile-card-header">
            <h2>Security Settings</h2>
            <p>Add an extra layer of account protection with authenticator-based 2FA.</p>
          </div>

          {twoFactorMessage && <div className="profile-alert success">{twoFactorMessage}</div>}
          {twoFactorError && <div className="profile-alert error">{twoFactorError}</div>}

          {!twoFactorEnabled && !setupMode && (
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className="profile-2fa-btn"
              onClick={handleBeginTwoFactorSetup}
              disabled={setupLoading}
            >
              <KeyRound size={16} />
              {setupLoading ? 'Preparing secure setup...' : 'Enable 2FA'}
            </motion.button>
          )}

          {twoFactorEnabled && (
            <div className="twofa-enabled-pill">
              <CheckCircle2 size={16} />
              Two-factor authentication is enabled
            </div>
          )}

          <AnimatePresence mode="wait">
            {setupMode && (
              <motion.div
                key="twofa-setup"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="twofa-setup-shell"
              >
                <div className="twofa-qr-card">
                  <div className="twofa-title-row">
                    <QrCode size={16} />
                    <span>Scan this QR code with Google Authenticator or Authy</span>
                  </div>
                  {qrValue && (
                    <div className="twofa-qr-box">
                      <QRCodeSVG value={qrValue} size={180} />
                    </div>
                  )}
                </div>

                <div className="twofa-backup-card">
                  <h3>Backup Codes</h3>
                  <p>Save these one-time recovery codes securely.</p>
                  <div className="twofa-backup-grid">
                    {backupCodes.map((code) => (
                      <span key={code}>{code}</span>
                    ))}
                  </div>
                </div>

                <form className="twofa-verify-form" onSubmit={handleEnableTwoFactor}>
                  <label htmlFor="verify-2fa">Enter 6-digit authenticator code</label>
                  <input
                    id="verify-2fa"
                    type="text"
                    maxLength={6}
                    pattern="\d{6}"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="123456"
                    required
                  />
                  <button type="submit" disabled={verifying2FA || verificationCode.length !== 6}>
                    {verifying2FA ? 'Verifying...' : 'Verify & Enable 2FA'}
                  </button>
                </form>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  )
}
