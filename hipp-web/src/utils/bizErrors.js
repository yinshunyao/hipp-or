/**
 * hipp-or mp_chat 业务错误码（与 hipp-api apps/mp_chat/biz_codes.py 对齐）。
 * 可行动逻辑只认 code；message 优先用服务端，空则用本表兜底。
 */
import router from '@/router'

export const BizCode = {
  AGENT_UNAVAILABLE: 46001,
  TOPIC_CLOSED: 46002,
  SCENE_AGENT_UNAVAILABLE: 46003,
  GUEST_TRIAL_EXHAUSTED: 46004,
  BALANCE_INSUFFICIENT: 46005,
  SESSION_FEE_CHECK_FAILED: 46006
}

const FALLBACK_MSG = {
  [BizCode.AGENT_UNAVAILABLE]: '智能体已下架或删除，暂不支持继续对话',
  [BizCode.TOPIC_CLOSED]: '话题已结束，请开启新话题后再发送',
  [BizCode.SCENE_AGENT_UNAVAILABLE]: '当前场景暂不可用',
  [BizCode.GUEST_TRIAL_EXHAUSTED]:
    '本场景免费体验次数已用完。请打开底部「我的」Tab，进入登录页完成登录后再继续使用。',
  [BizCode.BALANCE_INSUFFICIENT]: '余额不足，请先前往账户充值后再发起咨询',
  [BizCode.SESSION_FEE_CHECK_FAILED]: '无法校验余额，请稍后重试'
}

const TRANSIENT = /^(no stream|连接中断|响应超时|网络异常|发送失败)$/i

/**
 * @returns {{ code: number|null, message: string, action: 'wallet'|null }}
 */
export function resolveBizError(err) {
  const codeRaw = err && err.code != null ? Number(err.code) : NaN
  const code = Number.isFinite(codeRaw) ? codeRaw : null
  const serverMsg = String((err && err.message) || '').trim()
  if (code != null && FALLBACK_MSG[code]) {
    return {
      code,
      message: serverMsg || FALLBACK_MSG[code],
      action: code === BizCode.BALANCE_INSUFFICIENT ? 'wallet' : null
    }
  }
  if (!serverMsg || TRANSIENT.test(serverMsg)) {
    return { code, message: '发送失败，请稍后重试。', action: null }
  }
  return {
    code,
    message: serverMsg.length > 240 ? `${serverMsg.slice(0, 239)}…` : serverMsg,
    action: null
  }
}

/** 按 code 执行侧效应（如跳转钱包）。HTTP 层若已 toast，调用方勿再 toast。 */
export function applyBizErrorAction(err) {
  const resolved = resolveBizError(err)
  if (resolved.action === 'wallet') {
    router.push({ path: '/wallet' }).catch(() => {})
  }
  return resolved
}
