import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Lock, LogIn, UserPlus, Shield, Database, Fingerprint, Sparkles } from 'lucide-react'
import './Home.css'

function Home() {
  const navigate = useNavigate()
  
  useEffect(() => {
    // If user is already authenticated, redirect to dashboard
    const token = localStorage.getItem('access_token')
    if (token) {
      navigate('/dashboard')
    }
  }, [navigate])
  
  return (
    <div className="home-container">
      <div className="home-glow home-glow-one" />
      <div className="home-glow home-glow-two" />
      <div className="home-grid-overlay" />

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="home-content">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="hero-section"
        >
          <div className="hero-pill">
            <Sparkles size={14} />
            Zero-Trust Encrypted Banking
          </div>

          <h1 className="home-title">Banking security engineered like a modern cryptographic cloud startup.</h1>
          <p className="home-subtitle">
            Protect every account action with layered encryption, role-aware controls, and integrity verification built for
            high-stakes financial systems.
          </p>

          <div className="home-buttons">
            <button onClick={() => navigate('/login')} className="btn btn-primary">
              <LogIn size={18} />
              User Login
            </button>
            <button onClick={() => navigate('/register')} className="btn btn-secondary">
              <UserPlus size={18} />
              Create Account
            </button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="feature-grid"
        >
          <article className="feature-card">
            <Lock size={18} />
            <h3>Zero-Trust Sessions</h3>
            <p>JWT sessions hardened with optional 2FA challenge and role-aware authorization paths.</p>
          </article>
          <article className="feature-card">
            <Database size={18} />
            <h3>Encrypted Data at Rest</h3>
            <p>Profile and post fields are encrypted before persistence to simulate production-grade secure storage.</p>
          </article>
          <article className="feature-card">
            <Shield size={18} />
            <h3>Integrity Assurance</h3>
            <p>HMAC-backed transaction verification and audit-ready cryptographic checks for trustable records.</p>
          </article>
          <article className="feature-card">
            <Fingerprint size={18} />
            <h3>Compliance Friendly</h3>
            <p>Admin and Authority workspaces support KYC, monitoring, and visibility over security operations.</p>
          </article>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }} className="home-admin-section">
          <p className="admin-label">Administrative Access</p>
          <div className="admin-buttons">
            <button onClick={() => navigate('/admin-login')} className="btn btn-admin">Admin Login</button>
            <button onClick={() => navigate('/authority-login')} className="btn btn-authority">Authority Login</button>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default Home
