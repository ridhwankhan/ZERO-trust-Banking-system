import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, PenSquare, SendHorizonal } from 'lucide-react'
import { createPost } from '../services/api'
import './CreatePost.css'

export default function CreatePost() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const getPostErrorMessage = (err: any) => {
    const data = err?.response?.data
    if (!data) return 'Failed to publish post'
    if (typeof data.error === 'string') return data.error
    if (Array.isArray(data.error) && data.error.length > 0) return String(data.error[0])
    if (typeof data.detail === 'string') return data.detail
    return 'Failed to publish post'
  }

  const handleCreatePost = async (e: React.FormEvent) => {
    e.preventDefault()
    const cleanTitle = title.trim()
    const cleanContent = content.trim()
    if (!cleanTitle || !cleanContent) {
      setError('Both title and content are required.')
      return
    }

    setLoading(true)
    setError('')
    setSuccessMessage('')
    try {
      await createPost({ title: cleanTitle, content: cleanContent })
      setSuccessMessage('Post published successfully. Redirecting to feed...')
      setTimeout(() => navigate('/posts'), 600)
    } catch (err: any) {
      setError(getPostErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="create-post-page">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="create-post-shell"
      >
        <div className="create-post-topbar">
          <button onClick={() => navigate('/posts')} className="create-post-back">
            <ArrowLeft size={16} />
            Back to Feed
          </button>
        </div>

        <div className="create-post-card">
          <h1>
            <PenSquare size={22} />
            Create Encrypted Post
          </h1>
          <p>Your title and content are RSA-encrypted before storage.</p>

          {error && <div className="create-post-error">{error}</div>}
          {successMessage && <div className="create-post-success">{successMessage}</div>}

          <form onSubmit={handleCreatePost} className="create-post-form">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Post title"
              required
            />
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write your encrypted post content..."
              rows={8}
              required
            />
            <motion.button whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} type="submit" disabled={loading}>
              <SendHorizonal size={16} />
              {loading ? 'Publishing...' : 'Publish Post'}
            </motion.button>
          </form>
        </div>
      </motion.div>
    </div>
  )
}
