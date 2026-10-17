import { toast } from '@/utils/toast'

const API = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')

function token() {
  return localStorage.getItem('hipp_web_token') || ''
}

function needRelogin(msg) {
  return /重新登录|重新登陆|请先登录|请您先登录/.test(String(msg || ''))
}

async function refreshToken() {
  const rt = localStorage.getItem('hipp_web_refresh')
  if (!rt) return
  const res = await fetch(`${API}/auth/token/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rt)
  })
  const payload = await res.json().catch(() => ({}))
  if (!res.ok || payload.code !== 200 || !payload.data) return
  const next = `${payload.data.token_type} ${payload.data.access_token}`
  localStorage.setItem('hipp_web_token', next)
  if (payload.data.refresh_token) localStorage.setItem('hipp_web_refresh', payload.data.refresh_token)
}

export async function request(method, url, { data, params, form, skipToast } = {}) {
  const headers = {}
  const auth = token()
  if (auth) headers.Authorization = auth
  let body
  if (form) {
    body = form
  } else if (data !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = typeof data === 'string' ? data : JSON.stringify(data)
  }
  const q = new URLSearchParams()
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
    })
  }
  const qs = q.toString() ? `?${q}` : ''
  let res
  try {
    res = await fetch(`${API}${url}${qs}`, { method, headers, body })
  } catch (err) {
    if (!skipToast) toast('网络异常，请稍后重试')
    throw new Error('网络异常')
  }
  const refresh = res.headers.get('if-refresh')
  const text = await res.text()
  let payload = {}
  if (text) {
    try { payload = JSON.parse(text) } catch { payload = { message: text } }
  }
  const code = payload.code || (res.ok ? 200 : res.status)
  const msg = payload.message || payload.msg || '请求失败'
  if (res.status === 401 || code === 401 || ((res.status === 403 || code === 403) && needRelogin(msg))) {
    window.dispatchEvent(new Event('hipp-auth-lost'))
    throw new Error(needRelogin(msg) ? msg : '未认证，请登录')
  }
  if (code !== 200) {
    if (!skipToast) toast(msg)
    const error = new Error(msg)
    error.code = code
    throw error
  }
  if (refresh === '1') refreshToken().catch(() => {})
  return payload
}

export const http = {
  get: (url, opts) => request('GET', url, opts),
  post: (url, data, opts) => request('POST', url, { ...opts, data }),
  postForm: (url, form, opts) => request('POST', url, { ...opts, form }),
  patch: (url, data, opts) => request('PATCH', url, { ...opts, data }),
  delete: (url, opts) => request('DELETE', url, opts)
}
