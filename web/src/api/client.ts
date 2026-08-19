import axios from 'axios'

const TOKEN_KEY = 'ledger_token'

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? ''
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export const api = axios.create({ baseURL: '/api/v1', timeout: 15000 })

api.interceptors.request.use((config) => {
  const t = getToken()
  if (t) config.headers.Authorization = `Bearer ${t}`
  return config
})

let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn
}

let onError: ((msg: string) => void) | null = null
export function setErrorHandler(fn: (msg: string) => void) {
  onError = fn
}

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response?.status === 401) {
      console.error('401 未授权，要求重新输入 token')
      clearToken()
      onUnauthorized?.()
    } else {
      const detail = error.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : `请求失败（${error.response?.status ?? '网络错误'}）`
      console.error('API 错误:', error.response?.data ?? error.message)
      onError?.(msg)
    }
    return Promise.reject(error)
  },
)
