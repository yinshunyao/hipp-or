import { http } from './http'

export function fetchSessionFee() {
  return http.get('/wallet/session-fee').then((r) => r.data || {})
}

export function fetchBalance() {
  return http.get('/wallet/balance').then((r) => r.data || {})
}

export function fetchPresets() {
  return http.get('/wallet/presets').then((r) => r.data || { items: [] })
}

export function fetchPayChannels() {
  return http.get('/wallet/pay-channels').then((r) => r.data || { items: [] })
}

export function createRecharge(amount, channel) {
  const body = { amount, product: 'or' }
  if (channel) body.channel = channel
  return http.post('/wallet/recharge', body).then((r) => r.data || {})
}

export function getRecharge(orderId) {
  return http
    .get(`/wallet/recharge/${orderId}`, { skipToast: true })
    .then((r) => r.data || {})
}

export function devPay(orderId) {
  return http.post(`/wallet/recharge/${orderId}/dev-pay`, {}).then((r) => r.data || {})
}

export function fetchRechargeOrders(page = 1, pageSize = 20, product = 'or') {
  return http
    .get('/wallet/recharge/orders', {
      params: { page, page_size: pageSize, product: product || 'or' }
    })
    .then((r) => r.data || { items: [], total: 0 })
}

export function fetchTransactions(page = 1, pageSize = 20, product = 'or') {
  return http
    .get('/wallet/transactions', {
      params: { page, page_size: pageSize, product: product || 'or' }
    })
    .then((r) => r.data || { items: [], total: 0 })
}

export function fetchBills() {
  return http.get('/wallet/bills').then((r) => r.data || { items: [] })
}
