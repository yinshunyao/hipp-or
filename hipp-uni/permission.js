import { getToken } from '@/common/utils/auth'
import store from '@/store'
import { RouterMount, createRouter } from 'uni-simple-router'

// uni-simple-router 官方文档：https://www.hhyang.cn/v2/start/cross/codeRoute.html

// 登录页面
const loginPage = '/pages/login/login'
// 默认进入首页（企业宣传）
const indexPage = '/pages/home/index'

const router = createRouter({
  platform: process.env.VUE_APP_PLATFORM,
  detectBeforeLock: (router, to, navType) => {
    if (navType === 'replaceAll' && (to.path === loginPage || to.path === indexPage)) {
      router.$lockStatus = false // 取消跳转锁
    }
  },
  routes: [...ROUTES] // ROUTES是通过webpack的defaultPlugin编译成全局变量
})

//全局路由前置守卫
router.beforeEach(async (to, from, next) => {
  if (to.meta.loginAuth) {
    if (getToken()) {
      if (!store.state.auth.isUser) {
        try {
          await store.dispatch('auth/GetInfo')
        } catch (e) {}
      }
      // 游客持有 JWT，但须允许进入登录页绑定手机号；仅正式登录态才从登录页踢回首页
      if (to.path === loginPage && store.state.auth.userType !== 'mp_guest') {
        next({
          path: indexPage,
          NAVTYPE: 'replaceAll'
        })
        return
      }
      next()
      return
    }
    try {
      await store.dispatch('auth/EnsureGuestToken')
    } catch (e) {}
    if (getToken()) {
      if (!store.state.auth.isUser) {
        try {
          await store.dispatch('auth/GetInfo')
        } catch (e) {}
      }
      next()
      return
    }
    next({
      path: loginPage,
      NAVTYPE: 'replaceAll'
    })
  } else if (to.path === loginPage && getToken() && store.state.auth.userType !== 'mp_guest') {
    next({
      path: indexPage,
      NAVTYPE: 'replaceAll'
    })
  } else {
    next()
  }
})

// 全局路由后置守卫
router.afterEach((to, from) => {
  // console.log('跳转结束')
})

export { router, RouterMount }
