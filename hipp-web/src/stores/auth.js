import { defineStore } from 'pinia'
import { getInfo, login as loginApi, ssoExchange } from '@/api/auth'
import { assetUrl } from '@/utils/asset'
import {
  broadcastLogout,
  getManagerToken,
  markLogin,
  setManagerToken,
  shouldClearLocal
} from '@/utils/sso'

const TOKEN = 'hipp_web_token'
const REFRESH = 'hipp_web_refresh'
const PRODUCT = 'or'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN) || '',
    name: '',
    nickname: '',
    gender: '',
    telephone: localStorage.getItem('hipp_web_phone') || '',
    avatar: '',
    roles: [],
    userType: 'system',
    mustSetPasswordWithoutOld: false,
    ready: false
  }),
  getters: {
    loggedIn: (s) => !!s.token,
    displayName: (s) => {
      if (s.nickname && String(s.nickname).trim()) return s.nickname
      if (s.name && String(s.name).trim()) return s.name
      return '我的'
    },
    isEntitlement: (s) => s.userType === 'entitlement',
    isStaff: (s) => Array.isArray(s.roles) && s.roles.includes('人工客服'),
    avatarSrc: (s) => assetUrl(s.avatar)
  },
  actions: {
    applyToken(data, telephone) {
      const token = `${data.token_type} ${data.access_token}`
      this.token = token
      localStorage.setItem(TOKEN, token)
      markLogin(PRODUCT)
      if (data.refresh_token) localStorage.setItem(REFRESH, data.refresh_token)
      if (data.manager_token) setManagerToken(data.manager_token)
      if (telephone) {
        this.telephone = telephone
        localStorage.setItem('hipp_web_phone', telephone)
      }
      this.userType = data.user_type || 'system'
      this.mustSetPasswordWithoutOld = !!data.must_set_password_without_old
      this.ready = false
    },
    syncSso() {
      if (shouldClearLocal(PRODUCT) && this.token) {
        this.clear({ broadcast: false })
      }
    },
    async trySso() {
      if (this.token || !getManagerToken()) return false
      try {
        const res = await ssoExchange()
        this.applyToken(res.data || {})
        await this.fetchInfo()
        return true
      } catch {
        setManagerToken(null)
        return false
      }
    },
    async loginWith(telephone, secret, method) {
      const res = await loginApi(telephone.trim(), secret, method)
      this.applyToken(res.data || {}, telephone.trim())
      await this.fetchInfo()
      return res
    },
    login(telephone, password) {
      return this.loginWith(telephone, password, '0')
    },
    smsLogin(telephone, code) {
      return this.loginWith(telephone, code, '1')
    },
    async fetchInfo() {
      const res = await getInfo()
      const user = res.data || {}
      this.name = user.name || ''
      this.nickname = user.nickname || ''
      this.gender = user.gender || ''
      this.telephone = user.telephone || this.telephone
      this.avatar = user.avatar || ''
      this.userType = user.user_type || 'system'
      this.roles = Array.isArray(user.roles) ? user.roles.map((item) => item.name || item) : []
      if (user.must_set_password_without_old != null) {
        this.mustSetPasswordWithoutOld = !!user.must_set_password_without_old
      }
      if (this.telephone) localStorage.setItem('hipp_web_phone', this.telephone)
      this.ready = true
      return user
    },
    patchProfile(user) {
      this.name = user.name || ''
      this.nickname = user.nickname || ''
      this.gender = user.gender || ''
      this.telephone = user.telephone || this.telephone
      if (user.avatar) this.avatar = user.avatar
    },
    clear(opts = {}) {
      const broadcast = opts.broadcast !== false
      const clearManager = opts.clearManager !== false
      this.token = ''
      this.name = ''
      this.nickname = ''
      this.gender = ''
      this.avatar = ''
      this.roles = []
      this.userType = 'system'
      this.mustSetPasswordWithoutOld = false
      this.ready = false
      localStorage.removeItem(TOKEN)
      localStorage.removeItem(REFRESH)
      if (clearManager) setManagerToken(null)
      if (broadcast) broadcastLogout()
    }
  }
})
