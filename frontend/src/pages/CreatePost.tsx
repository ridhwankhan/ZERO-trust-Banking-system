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

  const handleCreatePost = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await createPost({ title, content })
      navigate('/posts')
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to publish post')
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
