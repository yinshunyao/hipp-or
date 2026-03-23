import { defineStore } from 'pinia'
import { asyncRouterMap, constantRouterMap } from '@/router'
import { generateRoutesByServer, flatMultiLevelRoutes } from '@/utils/routerHelper'
import { store } from '../index'
import { cloneDeep } from 'lodash-es'

export interface PermissionState {
  routers: AppRouteRecordRaw[]
  addRouters: AppRouteRecordRaw[]
  isAddRouters: boolean
  menuTabRouters: AppRouteRecordRaw[]
}

export const usePermissionStore = defineStore('permission', {
  state: (): PermissionState => ({
    routers: [],
    addRouters: [],
    isAddRouters: false,
    menuTabRouters: []
  }),
  getters: {
    getRouters(): AppRouteRecordRaw[] {
      return this.routers
    },
    getAddRouters(): AppRouteRecordRaw[] {
      return flatMultiLevelRoutes(cloneDeep(this.addRouters))
    },
    getIsAddRouters(): boolean {
      return this.isAddRouters
    },
    getMenuTabRouters(): AppRouteRecordRaw[] {
      return this.menuTabRouters
    }
  },
  actions: {
    generateRoutes(routers: AppCustomRouteRecordRaw[]): Promise<unknown> {
      return new Promise<void>((resolve) => {
        const asyncRoutes = cloneDeep(asyncRouterMap)
        let routerMap: AppRouteRecordRaw[] = generateRoutesByServer(
          routers as AppCustomRouteRecordRaw[]
        )
        // 智能客服 /agent：强制使用前端 asyncRouterMap（Layout + manager 子路由 + 正确 import）
        // 若仅「后台已配置同 path」则不再合并 async，而后台 component/path 配错时无法匹配子路由，
        // 请求会落到通配 /:path(.*)* → 重定向 404（hasRoute 仍因通配匹配而为 true，不会走重新登录）
        const agentFromFront = asyncRoutes.find((r) => r.path === '/agent')
        if (agentFromFront) {
          const idx = routerMap.findIndex((r) => r.path === '/agent')
          if (idx >= 0) {
            routerMap[idx] = agentFromFront
          } else {
            routerMap.push(agentFromFront)
          }
        }
        const serverRootPaths = new Set(routerMap.map((r) => r.path))
        const extraAsync = asyncRoutes.filter(
          (r) => r.path !== '/agent' && !serverRootPaths.has(r.path)
        )
        routerMap = routerMap.concat(extraAsync)
        // 动态路由，404一定要放到最后面
        this.addRouters = routerMap.concat([
          {
            path: '/:path(.*)*',
            redirect: '/404',
            name: '404Page',
            meta: {
              hidden: true,
              breadcrumb: false
            }
          }
        ])
        // 渲染菜单的所有路由
        this.routers = cloneDeep(constantRouterMap).concat(routerMap)
        resolve()
      })
    },
    setIsAddRouters(state: boolean): void {
      this.isAddRouters = state
    },
    setMenuTabRouters(routers: AppRouteRecordRaw[]): void {
      this.menuTabRouters = routers
    }
  },
  persist: {
    paths: ['routers', 'addRouters', 'menuTabRouters']
  }
})

export const usePermissionStoreWithOut = () => {
  return usePermissionStore(store)
}
