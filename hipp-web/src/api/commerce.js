import { http } from './http'

export function previewAccess(token) {
  return http.get(`/commerce/access/${encodeURIComponent(token)}`, { skipToast: true })
}

export function redeemAccess(token) {
  return http.post(`/commerce/access/${encodeURIComponent(token)}/redeem`, {}, { skipToast: true })
}
