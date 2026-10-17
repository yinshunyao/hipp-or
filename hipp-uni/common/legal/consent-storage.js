/** 登录页协议「已阅读确认」本地缓存（与业务 token 无关，单独 key） */
export const LEGAL_STORAGE_KEYS = {
  privacy: 'hipp_login_legal_privacy_v1',
  agreement: 'hipp_login_legal_agreement_v1'
}

export function isLegalConfirmed(kind) {
  return !!uni.getStorageSync(LEGAL_STORAGE_KEYS[kind])
}

export function setLegalConfirmed(kind) {
  uni.setStorageSync(LEGAL_STORAGE_KEYS[kind], true)
}

export function isBothLegalConfirmed() {
  return isLegalConfirmed('privacy') && isLegalConfirmed('agreement')
}
