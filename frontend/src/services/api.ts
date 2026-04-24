import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Types
export interface User {
  id: number
  email: string
  username: string
  role: 'user' | 'admin'
  is_admin: boolean
  created_at: string
  crypto_status?: {
    rsa: { has_public_key: boolean; has_encrypted_private_key: boolean }
    ecc: { has_public_key: boolean; has_encrypted_private_key: boolean }
  }
}

export interface AuthResponse {
  access: string
  refresh: string
  user: User
}

export interface Transaction {
  id: number
  sender_email: string
  receiver_email: string
  amount: string
  privacy_level: 'standard' | 'private_metadata' | 'high_privacy'
  encrypted_payload: string | null
  decrypted_payload?: any
  metadata_visible?: any
  hmac_signature: string
  created_at: string
}

export interface Ledger {
  balance: string
  last_updated: string
}

export interface CreateTransactionData {
  receiver_id: number
  amount: string
  privacy_level: 'standard' | 'private_metadata' | 'high_privacy'
  description?: string
  notes?: string
  category?: string
}

// Auth API
export const register = async (data: {
  email: string
  username: string
  password: string
  password_confirm: string
}): Promise<AuthResponse> => {
  const response = await api.post('/auth/register/', data)
  return response.data
}

export const login = async (data: {
  email: string
  password: string
}): Promise<AuthResponse> => {
  const response = await api.post('/auth/login/', data)
  return response.data
}

export const logout = async (refresh: string): Promise<void> => {
  await api.post('/auth/logout/', { refresh })
}

export const getProfile = async (): Promise<User> => {
  const response = await api.get('/auth/profile/')
  return response.data
}

// Transaction API
export const getBalance = async (): Promise<Ledger> => {
  const response = await api.get('/transactions/balance/')
  return response.data
}

export const createTransaction = async (data: CreateTransactionData) => {
  const response = await api.post('/transactions/create/', data)
  return response.data
}

export const getTransactionHistory = async (params?: {
  privacy_level?: string
  as_sender?: boolean
  as_receiver?: boolean
}) => {
  const response = await api.get('/transactions/history/', { params })
  return response.data
}

export const getTransactionDetail = async (id: number) => {
  const response = await api.get(`/transactions/${id}/`)
  return response.data
}

export const verifyTransaction = async (id: number) => {
  const response = await api.post(`/transactions/${id}/verify/`)
  return response.data
}

// Admin API (for admins)
export const getAllTransactions = async () => {
  const response = await api.get('/transactions/admin/all/')
  return response.data
}

export const getAuditLogs = async () => {
  const response = await api.get('/audit/logs/')
  return response.data
}

// Legacy exports
export const fetchUsers = async () => {
  const response = await api.get('/users/')
  return response.data
}

export const fetchUser = async (id: number) => {
  const response = await api.get(`/users/${id}/`)
  return response.data
}

export default api
