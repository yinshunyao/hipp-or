import request from '@/config/axios'

export const getSessionFeeGlobalApi = (): Promise<IResponse> => {
  return request.get({ url: '/vadmin/billing/session-fee/global' })
}

export const putSessionFeeGlobalApi = (amount: number): Promise<IResponse> => {
  return request.put({ url: '/vadmin/billing/session-fee/global', data: { amount } })
}

export const getSessionFeeUsersApi = (params: {
  q?: string
  page?: number
  limit?: number
}): Promise<IResponse> => {
  return request.get({ url: '/vadmin/billing/session-fee/users', params })
}

export const putUserSessionFeeApi = (userId: number, amount: number): Promise<IResponse> => {
  return request.put({ url: `/vadmin/billing/session-fee/users/${userId}`, data: { amount } })
}

export const deleteUserSessionFeeApi = (userId: number): Promise<IResponse> => {
  return request.delete({ url: `/vadmin/billing/session-fee/users/${userId}` })
}
