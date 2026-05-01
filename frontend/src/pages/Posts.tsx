import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Plus, Pencil, Trash2, ShieldCheck, Clock3 } from 'lucide-react'
import { deletePost, getPosts, Post, updatePost } from '../services/api'
import './Posts.css'

export default function Posts() {
  const navigate = useNavigate()
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingPost, setEditingPost] = useState<Post | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [updating, setUpdating] = useState(false)

  const fetchPosts = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getPosts()
      setPosts(data)
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Unable to load posts feed.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPosts()
  }, [])

  const openEdit = (post: Post) => {
    setEditingPost(post)
    setEditTitle(post.title)
    setEditContent(post.content)
  }

  const handleUpdatePost = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingPost) return
    setUpdating(true)
    try {
      const updated = await updatePost(editingPost.id, { title: editTitle, content: editContent })
      setPosts((prev) => prev.map((p) => (p.id === editingPost.id ? updated : p)))
      setEditingPost(null)
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to update post.')
    } finally {
      setUpdating(false)
    }
  }

  const handleDeletePost = async (postId: number) => {
    try {
      await deletePost(postId)
      setPosts((prev) => prev.filter((p) => p.id !== postId))
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to delete post.')
    }
  }

  return (
    <div className="posts-page">
      <div className="posts-shell">
        <motion.div initial={{ opacity: 0, y: -14 }} animate={{ opacity: 1, y: 0 }} className="posts-topbar">
          <div>
            <h1>Encrypted Social Feed</h1>
            <p>Premium private posts, end-to-end protected at rest.</p>
          </div>
          <button className="posts-create-btn" onClick={() => navigate('/posts/new')}>
            <Plus size={16} />
            Create Post
          </button>
        </motion.div>

        {error && <div className="posts-error">{error}</div>}

        {loading ? (
          <div className="posts-loading">Loading secure feed...</div>
        ) : posts.length === 0 ? (
          <div className="posts-empty">
            <p>No posts yet.</p>
            <button onClick={() => navigate('/posts/new')}>Write the first one</button>
          </div>
        ) : (
          <div className="posts-grid">
            {posts.map((post, index) => (
              <motion.article
                key={post.id}
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="post-card"
              >
                <div className="post-head">
                  <div className="post-author">
                    <ShieldCheck size={16} />
                    <span>{post.author_email}</span>
                  </div>
                  <div className="post-date">
                    <Clock3 size={14} />
                    {new Date(post.created_at).toLocaleString()}
                  </div>
                </div>

                <h3>{post.title}</h3>
                <p>{post.content}</p>

                {post.is_author && (
                  <div className="post-controls">
                    <button onClick={() => openEdit(post)}>
                      <Pencil size={14} />
                      Edit
                    </button>
                    <button className="danger" onClick={() => handleDeletePost(post.id)}>
                      <Trash2 size={14} />
                      Delete
                    </button>
                  </div>
                )}
              </motion.article>
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {editingPost && (
          <motion.div className="post-edit-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.form
              onSubmit={handleUpdatePost}
              className="post-edit-card"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 20, opacity: 0 }}
            >
              <h2>Edit Post</h2>
              <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} required />
              <textarea value={editContent} onChange={(e) => setEditContent(e.target.value)} rows={6} required />
              <div className="post-edit-actions">
                <button type="button" onClick={() => setEditingPost(null)}>
                  Cancel
                </button>
                <button type="submit" disabled={updating}>
                  {updating ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </motion.form>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
