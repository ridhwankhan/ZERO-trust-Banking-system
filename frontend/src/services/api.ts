import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

export const fetchUsers = async () => {
  const response = await api.get('/users/')
  return response.data
}

export const fetchUser = async (id: number) => {
  const response = await api.get(`/users/${id}/`)
  return response.data
}

export default api
