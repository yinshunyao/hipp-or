import request from '@/config/axios'

export const getChannelOrdersApi = (params: {
  q?: string
  status?: string
  page?: number
  limit?: number
}): Promise<IResponse> => {
  return request.get({ url: '/vadmin/commerce/orders', params })
}

export const refundChannelOrderApi = (
  orderId: number,
  data?: { remark?: string }
): Promise<IResponse> => {
  return request.post({ url: `/vadmin/commerce/orders/${orderId}/refund`, data: data || {} })
}

/** 线下出链：生成 1 次需求分析短链（已支付订单） */
export const createOfflineOrderApi = (data?: {
  remark?: string
  expires_days?: number | null
  external_order_id?: string
}): Promise<IResponse> => {
  return request.post({ url: '/vadmin/commerce/orders/offline', data: data || {} })
}

export const getEntitlementsApi = (params: {
  q?: string
  page?: number
  limit?: number
}): Promise<IResponse> => {
  return request.get({ url: '/vadmin/commerce/entitlements', params })
}

export const createEntitlementsApi = (data: {
  channel?: string
  external_order_id?: string
  expires_days?: number | null
  remark?: string
  count?: number
}): Promise<IResponse> => {
  return request.post({ url: '/vadmin/commerce/entitlements', data })
}

export const voidEntitlementApi = (id: number): Promise<IResponse> => {
  return request.post({ url: `/vadmin/commerce/entitlements/${id}/void` })
}
