import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// Create axios instance
export const api = axios.create({
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
  contact_info?: string
  role: 'user' | 'admin'
  is_admin: boolean
  two_factor_enabled?: boolean
  created_at: string
  crypto_status?: {
    rsa: { has_public_key: boolean; has_encrypted_private_key: boolean }
    ecc: { has_public_key: boolean; has_encrypted_private_key: boolean }
  }
}

export interface AuthResponse {
  tokens?: {
    access: string
    refresh: string
  }
  user: User
  message?: string
}

export interface TwoFactorSetupResponse {
  secret: string
  provisioning_uri: string
  backup_codes: string[]
  instructions: {
    step1: string
    step2: string
    step3: string
    step4: string
  }
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
  hmac_valid?: boolean
  transaction_hash?: string
  previous_hash?: string
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

export interface Post {
  id: number
  author: number
  author_email: string
  title: string
  content: string
  is_author: boolean
  created_at: string
  updated_at: string
}

// Auth API
export const register = async (data: {
  email: string
  username: string
  contact_info: string
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

export const setupTwoFactor = async (): Promise<TwoFactorSetupResponse> => {
  const response = await api.get('/auth/2fa/setup/')
  return response.data
}

export const enableTwoFactor = async (token: string): Promise<{ message: string }> => {
  const response = await api.post('/auth/2fa/setup/', { token })
  return response.data
}

export const verifyTwoFactorLogin = async (data: {
  user_id: number
  token: string
}): Promise<AuthResponse> => {
  const response = await api.post('/auth/2fa/verify/', data)
  return response.data
}

export const logout = async (refresh: string): Promise<void> => {
  await api.post('/auth/logout/', { refresh })
}

export const getProfile = async (): Promise<User> => {
  const response = await api.get('/auth/profile/')
  return response.data
}

export const updateProfile = async (data: {
  email?: string
  username?: string
  contact_info?: string
}): Promise<User> => {
  const response = await api.patch('/auth/profile/', data)
  return response.data
}

export const getPosts = async (): Promise<Post[]> => {
  const response = await api.get('/posts/')
  return response.data
}

export const createPost = async (data: {
  title: string
  content: string
}): Promise<Post> => {
  const response = await api.post('/posts/', data)
  return response.data
}

export const updatePost = async (
  id: number,
  data: { title: string; content: string }
): Promise<Post> => {
  const response = await api.put(`/posts/${id}/`, data)
  return response.data
}

export const deletePost = async (id: number): Promise<void> => {
  await api.delete(`/posts/${id}/`)
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
