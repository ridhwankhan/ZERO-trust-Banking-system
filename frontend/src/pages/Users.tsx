import { useEffect, useState } from 'react'
import { fetchUsers } from '../services/api'
import './Users.css'

interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  created_at: string
}

function Users() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const data = await fetchUsers()
        setUsers(data.results || [])
      } catch (err) {
        setError('Failed to load users')
      } finally {
        setLoading(false)
      }
    }
    loadUsers()
  }, [])

  if (loading) return <div className="container"><p>Loading...</p></div>
  if (error) return <div className="container"><p className="error">{error}</p></div>

  return (
    <div className="container">
      <div className="users">
        <h1>Users</h1>
        <div className="user-list">
          {users.length === 0 ? (
            <p>No users found. Add some users via Django admin.</p>
          ) : (
            users.map(user => (
              <div key={user.id} className="user-card">
                <h3>{user.username}</h3>
                <p>{user.email}</p>
                <span className={`status ${user.is_active ? 'active' : 'inactive'}`}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default Users
