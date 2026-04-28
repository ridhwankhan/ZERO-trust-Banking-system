import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Lock, LogIn, UserPlus, Shield, Users, TrendingUp } from 'lucide-react'
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
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="home-content"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          className="home-logo"
        >
          <Lock size={64} className="logo-icon" />
        </motion.div>

        <h1 className="home-title">ZERO Trust Banking System</h1>
        <p className="home-subtitle">Your Money, Protected and Connected </p>
        
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="home-stats"
        >
          <h2>Trusted by Thousands</h2>
          <div className="stats-grid">
            <div className="stat-item">
              <Users size={20} className="stat-icon" />
              <div className="stat-number">10K+</div>
              <div className="stat-label">Active Users</div>
            </div>
            <div className="stat-item">
              <TrendingUp size={20} className="stat-icon" />
              <div className="stat-number">$2.5M+</div>
              <div className="stat-label">Transactions</div>
            </div>
            <div className="stat-item">
              <Shield size={20} className="stat-icon" />
              <div className="stat-number">100%</div>
              <div className="stat-label">Secure</div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="home-buttons"
        >
          <button 
            onClick={() => navigate('/login')}
            className="btn btn-primary"
          >
            <LogIn size={20} />
            User Login
          </button>
          <button 
            onClick={() => navigate('/register')}
            className="btn btn-secondary"
          >
            <UserPlus size={20} />
            Register
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="home-admin-section"
        >
          <p className="admin-label">Administrative Access</p>
          <div className="admin-buttons">
            <button 
              onClick={() => navigate('/admin-login')}
              className="btn btn-admin"
            >
              Admin Login
            </button>
            <button 
              onClick={() => navigate('/authority-login')}
              className="btn btn-authority"
            >
              Authority Login
            </button>
          </div>
        </motion.div>
  
    

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.0 }}
          className="home-footer"
        >
          <p>Secure Banking Platform</p>
          {/* <p className="tech-stack">Advanced Cryptography</p> */}
        </motion.div>
      </motion.div>
    </div>
  )
}

export default Home
