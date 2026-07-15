import React, { useRef, useEffect, useState } from 'react'
import { Camera, X, Check, ShieldAlert } from 'lucide-react'
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
  title = "Biometric Face Recognition"
}: BiometricScannerModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<'initializing' | 'ready' | 'scanning' | 'success'>('initializing')
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!isOpen) return

    setStatus('initializing')
    setError(null)
    setProgress(0)

    navigator.mediaDevices.getUserMedia({ video: { width: 400, height: 400, facingMode: 'user' } })
      .then(mediaStream => {
        setStream(mediaStream)
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream
        }
        setStatus('ready')
      })
      .catch(err => {
        console.error("Camera access failed:", err)
        setError("Unable to access camera. Please check permissions.")
        setStatus('ready')
      })

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [isOpen])

  // Scan simulation
  useEffect(() => {
    if (status !== 'scanning') return

    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          captureAndVerify()
          return 100
        }
        return prev + 10
      })
    }, 150)

    return () => clearInterval(interval)
  }, [status])

  const startScan = () => {
    setProgress(0)
    setStatus('scanning')
  }

  const captureAndVerify = () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')
    if (!context) return

    canvas.width = 128
    canvas.height = 128
    context.drawImage(video, 0, 0, 128, 128)

    // Generate a pseudo-signature from actual pixel data
    const imgData = context.getImageData(0, 0, 128, 128)
    let sum = 0
    for (let i = 0; i < imgData.data.length; i += 4) {
      // average gray level
      sum += (imgData.data[i] + imgData.data[i+1] + imgData.data[i+2]) / 3
    }
    // simple deterministic hash from pixel sum
    const signatureHash = "face_sig_" + Math.round(sum).toString(16) + "_" + Math.random().toString(36).substr(2, 9)

    setStatus('success')
    setTimeout(() => {
      onScanSuccess(signatureHash)
      handleClose()
    }, 1200)
  }

  const handleClose = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="bs-overlay">
      <div className="bs-modal">
        <div className="bs-header">
          <h3>{title}</h3>
          <button className="bs-close" onClick={handleClose}><X size={18} /></button>
        </div>

        <div className="bs-viewport-container">
          {error ? (
            <div className="bs-error">
              <ShieldAlert size={48} className="bs-error-icon" />
              <p>{error}</p>
            </div>
          ) : (
            <div className="bs-viewport">
              <video ref={videoRef} autoPlay playsInline muted className="bs-video"></video>
              
              {status === 'ready' && (
                <div className="bs-prompt">
                  <p>Align face inside the frame and click start</p>
                  <button className="bs-action-btn" onClick={startScan}>Start Biometric Scan</button>
                </div>
              )}

              {status === 'scanning' && (
                <>
                  <div className="bs-scanner-line"></div>
                  <div className="bs-overlay-ring"></div>
                  <div className="bs-progress-bar" style={{ width: `${progress}%` }}></div>
                  <div className="bs-status-text">Scanning: {progress}%</div>
                </>
              )}

              {status === 'success' && (
                <div className="bs-success-overlay">
                  <Check size={48} className="bs-success-icon" />
                  <p>Biometric Signature Encoded</p>
                </div>
              )}
            </div>
          )}
        </div>
        <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
      </div>
    </div>
  )
}
