import request from '@/config/axios'
import type { UserLoginType } from './types'

export const loginApi = (data: UserLoginType): Promise<IResponse> => {
  return request.post({ url: '/auth/login', data })
}

export const getRoleMenusApi = (): Promise<IResponse<AppCustomRouteRecordRaw[]>> => {
  return request.get({ url: '/auth/getMenuList' })
}

/** 登录发码：与小程序共用 `POST /auth/sms/send`（JSON body），勿走 `/vadmin/system/sms/send`（该接口要求手机号已注册且历史为 query 传参） */
export const postSMSCodeApi = (data: { telephone: string }): Promise<IResponse> => {
  return request.post({ url: '/auth/sms/send', data })
}
