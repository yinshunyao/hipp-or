import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import type { App } from 'vue'
import { Layout } from '@/utils/routerHelper'
import { useI18n } from '@/hooks/web/useI18n'

const { t } = useI18n()

export const constantRouterMap: AppRouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    // 落地页与 asyncRouterMap 中实际存在的 workplace 对齐；analysis 已不在常量路由中
    redirect: '/dashboard/workplace',
    name: 'Root',
    meta: {
      hidden: true
    },
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/Home/Home.vue'),
        meta: {
          affix: false,
          alwaysShow: true,
          breadcrumb: true,
          canTo: true,
          hidden: true,
          noCache: true,
          noTagsView: false,
          title: '个人主页'
        }
      }
    ]
  },
  {
    path: '/redirect',
    component: Layout,
    name: 'Redirect',
    children: [
      {
        path: '/redirect/:path(.*)',
        name: 'Redirect',
        component: () => import('@/views/Redirect/Redirect.vue'),
        meta: {}
      }
    ],
    meta: {
      hidden: true,
      noTagsView: true
    }
  },
  {
    path: '/login',
    component: () => import('@/views/Login/Login.vue'),
    name: 'Login',
    meta: {
      hidden: true,
      title: t('router.login'),
      noTagsView: true
    }
  },
  {
    path: '/reset/password',
    component: () => import('@/views/Reset/Reset.vue'),
    name: 'ResetPassword',
    meta: {
      hidden: true,
      title: '重置密码',
      noTagsView: true
    }
  },
  {
    path: '/docs',
    name: 'Docs',
    meta: {
      hidden: true,
      title: '在线文档',
      noTagsView: true
    },
    children: [
      {
        path: 'privacy',
        name: 'Privacy',
        component: () => import('@/views/Vadmin/Docs/Privacy.vue'),
        meta: {
          hidden: true,
          title: '隐私政策',
          noTagsView: true
        }
      },
      {
        path: 'agreement',
        name: 'Agreement',
        component: () => import('@/views/Vadmin/Docs/Agreement.vue'),
        meta: {
          hidden: true,
          title: '用户协议',
          noTagsView: true
        }
      }
    ]
  },
  {
    path: '/404',
    component: () => import('@/views/Error/404.vue'),
    name: 'NoFind',
    meta: {
      hidden: true,
      title: '404',
      noTagsView: true
    }
  },
  {
    path: '/no-access',
    component: () => import('@/views/Error/NoAccess.vue'),
    name: 'NoAccess',
    meta: {
      hidden: true,
      title: '无访问权限',
      noTagsView: true
    }
  }
]

export const asyncRouterMap: AppRouteRecordRaw[] = [
  {
    path: '/dashboard',
    component: Layout,
    redirect: '/dashboard/workplace',
    name: 'Dashboard',
    meta: {
      title: t('router.dashboard'),
      icon: 'ant-design:dashboard-filled',
      alwaysShow: true
    },
    children: [
      {
        path: 'workplace',
        component: () => import('@/views/Dashboard/Workplace.vue'),
        name: 'Workplace',
        meta: {
          title: t('router.workplace'),
          noCache: true
        }
      }
    ]
  },
  {
    path: '/agent',
    component: Layout,
    name: 'Agent',
    meta: {
      title: '智能客服',
      icon: 'ep:chat-dot-round',
      alwaysShow: true
    },
    children: [
      {
        path: 'manager',
        component: () => import('@/views/Vadmin/AgentManager/AgentManager.vue'),
        name: 'AgentManager',
        meta: {
          title: '智能客服管理'
        }
      }
    ]
  },
  {
    path: '/mp-staff',
    component: Layout,
    name: 'MpStaff',
    meta: {
      title: '人工客服',
      icon: 'ant-design:customer-service-outlined',
      alwaysShow: true
    },
    children: [
      {
        path: 'chat-workbench',
        component: () => import('@/views/MpStaff/ChatWorkbench.vue'),
        name: 'MpStaffChatWorkbench',
        meta: {
          title: '客服工作台',
          noCache: true
        }
      }
    ]
  },
  {
    path: '/billing',
    component: Layout,
    redirect: '/billing/session-fee',
    name: 'Billing',
    meta: {
      title: '计费配置',
      icon: 'ant-design:pay-circle-outlined',
      alwaysShow: true
    },
    children: [
      {
        path: 'session-fee',
        component: () => import('@/views/Vadmin/Billing/SessionFee.vue'),
        name: 'BillingSessionFee',
        meta: {
          title: '会话咨询费用',
          noCache: true
        }
      }
    ]
  },
  {
    path: '/commerce',
    component: Layout,
    redirect: '/commerce/orders',
    name: 'Commerce',
    meta: {
      title: '电商履约',
      icon: 'ant-design:shop-outlined',
      alwaysShow: true
    },
    children: [
      {
        path: 'orders',
        component: () => import('@/views/Vadmin/Commerce/ChannelOrders.vue'),
        name: 'CommerceChannelOrders',
        meta: {
          title: '渠道订单',
          noCache: true
        }
      },
      {
        path: 'entitlements',
        component: () => import('@/views/Vadmin/Commerce/Entitlements.vue'),
        name: 'CommerceEntitlements',
        meta: {
          title: '次卡短链',
          noCache: true
        }
      }
    ]
  }
]

const router = createRouter({
  // 与 vite.config base（VITE_BASE_PATH）一致，否则部署在子路径（如 /manager/）时会跳到 /login 而非 /manager/login
  history: createWebHistory(import.meta.env.BASE_URL),
  strict: true,
  routes: constantRouterMap as RouteRecordRaw[],
  scrollBehavior: () => ({ left: 0, top: 0 })
})

export const resetRouter = (): void => {
  const resetWhiteNameList = [
    'Login',
    'NoFind',
    'NoAccess',
    'Root',
    'ResetPassword',
    'Redirect',
    'Home',
    'Docs',
    'Privacy',
    'Agreement'
  ]
  router.getRoutes().forEach((route) => {
    const { name } = route
    if (name && !resetWhiteNameList.includes(name as string)) {
      router.hasRoute(name) && router.removeRoute(name)
    }
  })
}

// 判断是否已经有某个路径的路由配置
export const hasRoute = (path: string): boolean => {
  const resolvedRoute = router.resolve(path)
  return resolvedRoute.matched.length > 0
}

export const setupRouter = (app: App<Element>) => {
  app.use(router)
}

export default router
