import { useState, useEffect } from 'react'
import { X, Check, ShieldAlert, Fingerprint } from 'lucide-react'
import { startRegistration } from '@simplewebauthn/browser'
import { api } from '../services/api'
import './BiometricScannerModal.css'

interface BiometricScannerModalProps {
  isOpen: boolean
  onClose: () => void
  onScanSuccess: (signatureHash: string) => void
  title?: string
}

export default function BiometricScannerModal({
  isOpen,
  onClose,
  onScanSuccess,
  title = "Register Passkey / Biometrics"
}: BiometricScannerModalProps) {
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<'ready' | 'scanning' | 'success'>('ready')

  useEffect(() => {
    if (isOpen) {
      setStatus('ready')
      setError(null)
    }
  }, [isOpen])

  const startScan = async () => {
    setStatus('scanning')
    setError(null)
    
    try {
      // 1. Get registration options from the server
      const resp = await api.get('/security/webauthn/register/generate-options/')
      const options = resp.data

      // 2. Pass options to the browser to trigger native biometric prompt (Windows Hello, FaceID, TouchID)
      // @simplewebauthn/browser v13+ expects { optionsJSON }
      const attResp = await startRegistration({ optionsJSON: options })

      // 3. Send the response back to the server for verification
      await api.post('/security/webauthn/register/verify/', attResp)
      
      setStatus('success')
      setTimeout(() => {
        onScanSuccess("webauthn_enrolled")
        onClose()
      }, 2000)
      
    } catch (err: any) {
      console.error("Biometric registration failed:", err)
      
      // Handle known WebAuthn errors
      if (err.name === 'NotAllowedError') {
        setError('Biometric mismatch or request cancelled. Please try again with proper Face/Fingerprint.')
      } else if (err.name === 'InvalidStateError') {
        setError('A passkey is already registered on this device.')
      } else {
        setError(err.response?.data?.error || err.message || 'Biometric enrollment failed.')
      }
      setStatus('ready')
    }
  }

  if (!isOpen) return null

  return (
    <div className="bs-overlay">
      <div className="bs-modal" style={{ maxWidth: '400px', height: 'auto', minHeight: '350px' }}>
        <div className="bs-header">
          <h3>{title}</h3>
          <button className="bs-close" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="bs-viewport-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
          {error ? (
            <div className="bs-error" style={{ textAlign: 'center', color: '#ef4444' }}>
              <ShieldAlert size={48} className="bs-error-icon" style={{ margin: '0 auto 1rem' }} />
              <p>{error}</p>
              <button 
                onClick={() => setError(null)} 
                className="bs-action-btn"
                style={{ marginTop: '1rem', background: 'transparent', border: '1px solid #ef4444', color: '#ef4444' }}
              >
                Try Again
              </button>
            </div>
          ) : (
            <div className="bs-viewport" style={{ textAlign: 'center' }}>
              
              {status === 'ready' && (
                <div className="bs-prompt">
                  <Fingerprint size={64} style={{ color: '#60a5fa', marginBottom: '1.5rem' }} />
                  <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '2rem' }}>
                    Secure your account with industry-standard Passkeys. Use your device's built-in Face ID, Touch ID, or Windows Hello.
                  </p>
                  <button className="bs-action-btn" onClick={startScan} style={{ width: '100%', padding: '12px', background: '#3b82f6', color: 'white', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: 600 }}>
                    Register Biometrics
                  </button>
                </div>
              )}

              {status === 'scanning' && (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div className="spinner" style={{ width: '48px', height: '48px', border: '4px solid #1e293b', borderTopColor: '#3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '1.5rem' }}></div>
                  <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
                  <p style={{ color: '#e2e8f0', fontWeight: 500 }}>Follow the prompts on your device...</p>
                  <p style={{ color: '#94a3b8', fontSize: '13px', marginTop: '0.5rem' }}>Waiting for Face ID, Touch ID, or PIN.</p>
                </div>
              )}

              {status === 'success' && (
                <div className="bs-success-overlay" style={{ background: 'transparent', position: 'static' }}>
                  <Check size={64} className="bs-success-icon" style={{ color: '#22c55e', marginBottom: '1rem' }} />
                  <h3 style={{ color: '#22c55e', margin: 0 }}>Passkey Enrolled</h3>
                  <p style={{ color: '#94a3b8', fontSize: '14px', marginTop: '0.5rem' }}>You can now login securely without a password.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
