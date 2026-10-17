import { http } from './http'
import { getManagerToken } from '@/utils/sso'

const API = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')

export function login(telephone, password, method = '0') {
  return http.post('/auth/login', {
    telephone,
    password,
    method,
    platform: '1'
  })
}

/** 用同源 hipp_manager_token 换发本产品会话。 */
export async function ssoExchange() {
  const managerToken = getManagerToken()
  if (!managerToken) throw new Error('无共享登录态')
  const res = await fetch(`${API}/auth/sso`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${managerToken}`
    }
  })
  const payload = await res.json().catch(() => ({}))
  const code = payload.code || (res.ok ? 200 : res.status)
  if (code !== 200 || !payload.data) {
    throw new Error(payload.message || payload.msg || 'SSO 换票失败')
  }
  return payload
}

export function sendLoginSms(telephone) {
  return http.post('/auth/sms/send', { telephone: (telephone || '').trim() })
}

export async function getInfo() {
  try {
    return await http.get('/vadmin/auth/user/admin/current/info', { skipToast: true })
  } catch {
    // 次卡等非管理端用户走 /auth/me
    return http.get('/auth/me', { skipToast: true })
  }
}

export function updateCurrentUser(data) {
  return http.post('/vadmin/auth/user/current/update/info', data)
}

export function resetPassword(data) {
  return http.post('/vadmin/auth/user/current/reset/password', data)
}

export function uploadAvatar(file) {
  const form = new FormData()
  form.append('file', file)
  return http.post('/vadmin/auth/user/current/update/avatar', undefined, { form })
}

export function getBaseConfig() {
  return http.get('/vadmin/system/settings/base/config', { skipToast: true })
}

export function getDictDetails(types) {
  return http.post('/vadmin/system/dict/types/details', types, { skipToast: true })
}
