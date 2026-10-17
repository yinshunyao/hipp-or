/** 同站（hipp.site）产品间登录态联动：or / cert / mgr 共用这些键。 */
export const SSO_LOGOUT_AT = 'hipp.sso.logout_at'
export const SSO_LOGIN_AT_PREFIX = 'hipp.sso.login_at.'
/** 任一产品登录成功时刷新；用于避免旧 logout_at 清掉其它产品刚写入的共享会话。 */
export const SSO_SESSION_AT = 'hipp.sso.session_at'
/** 共享的 hipp-manager 会话令牌（账户页与其它产品换票共用）。 */
export const MANAGER_TOKEN_KEY = 'hipp_manager_token'

export function getManagerToken() {
  return localStorage.getItem(MANAGER_TOKEN_KEY)
}

export function setManagerToken(token) {
  if (token) localStorage.setItem(MANAGER_TOKEN_KEY, token)
  else localStorage.removeItem(MANAGER_TOKEN_KEY)
}

export function markLogin(product) {
  const now = String(Date.now())
  localStorage.setItem(`${SSO_LOGIN_AT_PREFIX}${product}`, now)
  localStorage.setItem(SSO_SESSION_AT, now)
}

export function broadcastLogout() {
  localStorage.setItem(SSO_LOGOUT_AT, String(Date.now()))
}

export function shouldClearLocal(product) {
  const logoutAt = Number(localStorage.getItem(SSO_LOGOUT_AT) || 0)
  if (!logoutAt) return false
  const sessionAt = Number(localStorage.getItem(SSO_SESSION_AT) || 0)
  const loginAt = Number(localStorage.getItem(`${SSO_LOGIN_AT_PREFIX}${product}`) || 0)
  const effectiveLogin = Math.max(sessionAt, loginAt)
  if (!effectiveLogin) return false
  return logoutAt >= effectiveLogin
}

export function onRemoteLogout(handler) {
  const onStorage = (e) => {
    if (e.key === SSO_LOGOUT_AT && e.newValue) handler()
  }
  window.addEventListener('storage', onStorage)
  return () => window.removeEventListener('storage', onStorage)
}
