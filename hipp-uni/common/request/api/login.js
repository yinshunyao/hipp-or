import request from '@/common/request/request.js'

// 登录方法；method：0 密码，1 短信（password 字段传验证码）
export function login(telephone, password, method = '0') {
  const data = {
    telephone,
    password,
    method,
    platform: '1'
  }
  return request.post('/auth/login', data)
}

/** 小程序登录发码（不要求手机号已注册）。须走 `/auth/sms/send`，禁止调用 `/vadmin/system/sms/send`（管理端历史接口，要求用户已存在）。 */
export function sendLoginSms(telephone) {
  const t = (telephone || '').trim()
  return request.post(
    '/auth/sms/send',
    { telephone: t },
    { header: { 'Content-Type': 'application/json' } }
  )
}

// 获取用户详细信息
export function getInfo() {
  return request.get('/vadmin/auth/user/admin/current/info')
}

// 更新用户openid
export function setUserOpenid(code) {
  const params = { code }
  return request.put('/vadmin/auth/users/wx/server/openid', {}, { params: params })
}

// 小程序游客登录（wx.login code，无手机号）
export function mpGuestLogin(code) {
  return request.post(
    '/auth/mp/guest',
    { code, platform: '1', method: '4' },
    { custom: { skipErrorToast: true } }
  )
}

// 使用微信一键登录
export function wxCodeLogin(code, nickname = '', avatar = '') {
  const data = {
    code,
    nickname,
    avatar,
    method: '2',
    platform: '1'
  }
  return request.post('/auth/wx/login', data)
}
