import { useState, useEffect } from 'react'
import { X, Check, ShieldAlert, Fingerprint } from 'lucide-react'
import { startAuthentication, startRegistration } from '@simplewebauthn/browser'
import { api } from '../services/api'
import './BiometricScannerModal.css'

interface BiometricScannerModalProps {
  isOpen: boolean
  onClose: () => void
  onScanSuccess: (signatureHash: string) => void
  title?: string
  /** Clear existing passkeys and enroll a new one */
  overwrite?: boolean
  /** Only verify an existing passkey (no login tokens) */
  mode?: 'enroll' | 'verify'
}

export default function BiometricScannerModal({
  isOpen,
  onClose,
  onScanSuccess,
  title = 'Register Passkey / Biometrics',
  overwrite = false,
  mode = 'enroll',
}: BiometricScannerModalProps) {
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<'ready' | 'scanning' | 'success'>('ready')

  useEffect(() => {
    if (isOpen) {
      setStatus('ready')
      setError(null)
    }
  }, [isOpen, mode, overwrite])

  const startScan = async () => {
    setStatus('scanning')
    setError(null)

    try {
      if (mode === 'verify') {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        const resp = await api.post('/security/webauthn/authenticate/generate-options/', {
          email: user.email,
        })
        const asseResp = await startAuthentication({ optionsJSON: resp.data })
        await api.post('/security/webauthn/authenticate/verify/', {
          email: user.email,
          credential: asseResp,
          verify_only: true,
        })
      } else {
        if (overwrite) {
          try {
            await api.delete('/security/webauthn/clear/')
          } catch {
            // Continue — generate-options?overwrite=true also clears server-side
          }
        }

        const resp = await api.get('/security/webauthn/register/generate-options/', {
          params: overwrite ? { overwrite: 'true' } : undefined,
        })
        const attResp = await startRegistration({ optionsJSON: resp.data })
        await api.post(
          `/security/webauthn/register/verify/${overwrite ? '?overwrite=true' : ''}`,
          { ...attResp, overwrite }
        )
      }

      setStatus('success')
      setTimeout(() => {
        onScanSuccess(mode === 'verify' ? 'webauthn_verified' : 'webauthn_enrolled')
        onClose()
      }, 1600)
    } catch (err: any) {
      console.error('Biometric flow failed:', err)
      if (err.name === 'NotAllowedError') {
        setError('Biometric cancelled or mismatch. Try again with Face ID / fingerprint / Windows Hello.')
      } else if (err.name === 'InvalidStateError') {
        setError('A passkey already exists on this device. Use “Replace Passkey” to overwrite it.')
      } else {
        const data = err.response?.data
        setError(
          (typeof data?.error === 'string' && data.error) ||
            (typeof data?.detail === 'string' && data.detail) ||
            err.message ||
            'Biometric operation failed.'
        )
      }
      setStatus('ready')
    }
  }

  if (!isOpen) return null

  const actionLabel =
    mode === 'verify'
      ? 'Verify Biometrics'
      : overwrite
        ? 'Replace Passkey'
        : 'Register Biometrics'

  const helpText =
    mode === 'verify'
      ? 'Confirm your enrolled Face ID / Touch ID / Windows Hello works for this account.'
      : overwrite
        ? 'This removes your existing passkey and enrolls a new one on this device.'
        : 'Secure your account with industry-standard Passkeys. Use Face ID, Touch ID, or Windows Hello.'

  return (
    <div className="bs-overlay">
      <div className="bs-modal" style={{ maxWidth: '400px', height: 'auto', minHeight: '350px' }}>
        <div className="bs-header">
          <h3>{title}</h3>
          <button className="bs-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div
          className="bs-viewport-container"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
          }}
        >
          {error ? (
            <div className="bs-error" style={{ textAlign: 'center', color: '#ef4444' }}>
              <ShieldAlert size={48} className="bs-error-icon" style={{ margin: '0 auto 1rem' }} />
              <p>{error}</p>
              <button
                onClick={() => setError(null)}
                className="bs-action-btn"
                style={{
                  marginTop: '1rem',
                  background: 'transparent',
                  border: '1px solid #ef4444',
                  color: '#ef4444',
                }}
              >
                Try Again
              </button>
            </div>
          ) : (
            <div className="bs-viewport" style={{ textAlign: 'center' }}>
              {status === 'ready' && (
                <div className="bs-prompt">
                  <Fingerprint size={64} style={{ color: '#60a5fa', marginBottom: '1.5rem' }} />
                  <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '2rem' }}>{helpText}</p>
                  <button
                    className="bs-action-btn"
                    onClick={startScan}
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: '#3b82f6',
                      color: 'white',
                      borderRadius: '8px',
                      border: 'none',
                      cursor: 'pointer',
                      fontWeight: 600,
                    }}
                  >
                    {actionLabel}
                  </button>
                </div>
              )}

              {status === 'scanning' && (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div
                    className="spinner"
                    style={{
                      width: '48px',
                      height: '48px',
                      border: '4px solid #1e293b',
                      borderTopColor: '#3b82f6',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite',
                      marginBottom: '1.5rem',
                    }}
                  />
                  <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
                  <p style={{ color: '#e2e8f0', fontWeight: 500 }}>Follow the prompts on your device...</p>
                  <p style={{ color: '#94a3b8', fontSize: '13px', marginTop: '0.5rem' }}>
                    Waiting for Face ID, Touch ID, or PIN.
                  </p>
                </div>
              )}

              {status === 'success' && (
                <div className="bs-success-overlay" style={{ background: 'transparent', position: 'static' }}>
                  <Check size={64} className="bs-success-icon" style={{ color: '#22c55e', marginBottom: '1rem' }} />
                  <h3 style={{ color: '#22c55e', margin: 0 }}>
                    {mode === 'verify' ? 'Biometric Verified' : 'Passkey Enrolled'}
                  </h3>
                  <p style={{ color: '#94a3b8', fontSize: '14px', marginTop: '0.5rem' }}>
                    {mode === 'verify'
                      ? 'Your passkey works correctly for this account.'
                      : 'You can now log in with Passkey / Face ID.'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
