import { createRouter, createWebHashHistory } from 'vue-router'
import type {
  Router,
  RouteLocationNormalized,
  RouteRecordNormalized,
  RouteRecordRaw
} from 'vue-router'
import { isUrl } from '@/utils/is'
import { omit, cloneDeep } from 'lodash-es'

const modules = import.meta.glob('../views/**/*.{vue,tsx}')

/* Layout */
export const Layout = () => import('@/layout/Layout.vue')

export const getParentLayout = () => {
  return () =>
    new Promise((resolve) => {
      resolve({
        name: 'ParentLayout'
      })
    })
}

export const getRawRoute = (route: RouteLocationNormalized): RouteLocationNormalized => {
  if (!route) return route
  const { matched, ...opt } = route
  return {
    ...opt,
    matched: (matched
      ? matched.map((item) => ({
          meta: item.meta,
          name: item.name,
          path: item.path
        }))
      : undefined) as RouteRecordNormalized[]
  }
}

// 前端控制路由生成
export const generateRoutesByFrontEnd = (
  routes: AppRouteRecordRaw[],
  keys: string[],
  basePath = '/'
): AppRouteRecordRaw[] => {
  const res: AppRouteRecordRaw[] = []

  for (const route of routes) {
    const meta = route.meta ?? {}
    // skip some route
    if (meta.hidden && !meta.canTo) {
      continue
    }

    let data: Nullable<AppRouteRecordRaw> = null

    let onlyOneChild: Nullable<string> = null
    if (route.children && route.children.length === 1 && !meta.alwaysShow) {
      onlyOneChild = (
        isUrl(route.children[0].path)
          ? route.children[0].path
          : pathResolve(pathResolve(basePath, route.path), route.children[0].path)
      ) as string
    }

    // 开发者可以根据实际情况进行扩展
    for (const item of keys) {
      // 通过路径去匹配
      if (isUrl(item) && (onlyOneChild === item || route.path === item)) {
        data = Object.assign({}, route)
      } else {
        const routePath = (onlyOneChild ?? pathResolve(basePath, route.path)).trim()
        if (routePath === item || meta.followRoute === item) {
          data = Object.assign({}, route)
        }
      }
    }

    // recursive child routes
    if (route.children && data) {
      data.children = generateRoutesByFrontEnd(
        route.children,
        keys,
        pathResolve(basePath, data.path)
      )
    }
    if (data) {
      res.push(data as AppRouteRecordRaw)
    }
  }
  return res
}

/** 顶层路由 path 须以 / 开头（Vue Router 4）；后端菜单可能漏写前导 / */
function normalizeRootRoutePath(path: string): string {
  if (!path || isUrl(path)) return path
  const p = path.trim()
  if (!p) return p
  const withSlash = p.startsWith('/') ? p : `/${p}`
  // 库内常见误拼：与前端 asyncRouterMap 的 /agent 对齐
  if (withSlash === '/ageent') return '/agent'
  if (withSlash.startsWith('/ageent/')) return `/agent${withSlash.slice('/ageent'.length)}`
  return withSlash
}

function normalizeRootRedirect(redirect: string | undefined): string | undefined {
  if (redirect === undefined || redirect === null) return redirect
  if (!redirect || redirect === 'noredirect') return redirect
  if (isUrl(redirect)) return redirect
  const r = redirect.trim()
  if (!r) return r
  const withSlash = r.startsWith('/') ? r : `/${r}`
  if (withSlash === '/ageent') return '/agent'
  if (withSlash.startsWith('/ageent/')) return `/agent${withSlash.slice('/ageent'.length)}`
  return withSlash
}

const routeComponentFallbackMap: Record<string, string> = {
  agentManager: 'views/Vadmin/AgentManager/AgentManager',
  '/system/agentManager': 'views/Vadmin/AgentManager/AgentManager',
  /** 菜单误填为目录路径（无 .vue 文件名）时回退到同目录下页面 */
  'views/Vadmin/AgentManager': 'views/Vadmin/AgentManager/AgentManager'
}

/** 菜单里把「…/AgentManager」与「views/…」拼在一起少了一个 /，会出现 AgentManagerviews */
function sanitizeGluedViewsPath(s: string): string {
  if (!s || s.includes('#')) return s
  return s.replace(/([^/])views\//g, '$1/views/').replace(/([^/])views$/g, '$1/views')
}

/** 纠错后若包含完整 views 路径，优先按该路径解析（避免重复片段干扰） */
const preferredViewPathsForResolve: string[] = ['views/Vadmin/AgentManager/AgentManager']

function resolveByPreferredViewPath(sanitized: string) {
  for (const vp of preferredViewPathsForResolve) {
    if (sanitized.includes(vp)) {
      const m = modules[`../${vp}.vue`] || modules[`../${vp}.tsx`]
      if (m) return m
    }
  }
  return undefined
}

const resolveServerRouteComponent = (
  component: string | undefined,
  routePath: string | undefined
) => {
  const candidateKeys: string[] = []
  const c = (component || '').trim()
  if (c) candidateKeys.push(c)
  const p = (routePath || '').trim()
  if (p) candidateKeys.push(p)

  for (const raw of candidateKeys) {
    if (raw === '#') return Layout
    if (raw.includes('##')) return getParentLayout()

    const sanitized = sanitizeGluedViewsPath(raw)
    const preferred = resolveByPreferredViewPath(sanitized)
    if (preferred) return preferred

    const normalized = sanitized
      .replace(/^\//, '')
      .replace(/^@\//, '')
      .replace(/^src\//, '')
      .replace(/\.(vue|tsx)$/, '')
    const withViews = normalized.startsWith('views/') ? normalized : `views/${normalized}`
    const comModule = modules[`../${withViews}.vue`] || modules[`../${withViews}.tsx`]
    if (comModule) return comModule

    const fallback = routeComponentFallbackMap[raw] ?? routeComponentFallbackMap[sanitized]
    if (fallback) {
      const fallbackModule = modules[`../${fallback}.vue`] || modules[`../${fallback}.tsx`]
      if (fallbackModule) return fallbackModule
    }
  }
  return undefined
}

// 后端控制路由生成（仅顶层 path 补全 /；子路由保持相对 path 如 manager）
export const generateRoutesByServer = (
  routes: AppCustomRouteRecordRaw[],
  isRootLevel = true
): AppRouteRecordRaw[] => {
  const res: AppRouteRecordRaw[] = []

  for (const route of routes) {
    const data: AppRouteRecordRaw = {
      path: isRootLevel ? normalizeRootRoutePath(route.path) : route.path,
      name: route.name,
      redirect: isRootLevel ? normalizeRootRedirect(route.redirect) : route.redirect,
      meta: route.meta
    }
    const resolvedComponent = resolveServerRouteComponent(route.component as string, route.path)
    if (resolvedComponent) {
      data.component = resolvedComponent
    } else if (route.component) {
      console.error(
        `未找到组件：${route.component}（需为 views/ 下路径，如 views/Vadmin/AgentManager/AgentManager），请检查菜单 component 配置`
      )
    }
    // recursive child routes
    if (route.children) {
      data.children = generateRoutesByServer(route.children, false)
    }
    if (!data.component && (!data.children || data.children.length === 0)) {
      console.warn(`跳过无组件且无子路由的菜单：${route.path}`)
      continue
    }
    res.push(data as AppRouteRecordRaw)
  }
  return res
}

export const pathResolve = (parentPath: string, path: string) => {
  if (isUrl(path)) return path
  const childPath = path.startsWith('/') || !path ? path : `/${path}`
  return `${parentPath}${childPath}`.replace(/\/\//g, '/').trim()
}

// 路由降级
export const flatMultiLevelRoutes = (routes: AppRouteRecordRaw[]) => {
  const modules: AppRouteRecordRaw[] = cloneDeep(routes)
  for (let index = 0; index < modules.length; index++) {
    const route = modules[index]
    if (!isMultipleRoute(route)) {
      continue
    }
    promoteRouteLevel(route)
  }
  return modules
}

// 层级是否大于2
const isMultipleRoute = (route: AppRouteRecordRaw) => {
  if (!route || !Reflect.has(route, 'children') || !route.children?.length) {
    return false
  }

  const children = route.children

  let flag = false
  for (let index = 0; index < children.length; index++) {
    const child = children[index]
    if (child.children?.length) {
      flag = true
      break
    }
  }
  return flag
}

// 生成二级路由
const promoteRouteLevel = (route: AppRouteRecordRaw) => {
  let router: Router | null = createRouter({
    routes: [route as RouteRecordRaw],
    history: createWebHashHistory()
  })

  const routes = router.getRoutes()
  addToChildren(routes, route.children || [], route)
  router = null

  route.children = route.children?.map((item) => omit(item, 'children'))
}

// 添加所有子菜单
const addToChildren = (
  routes: RouteRecordNormalized[],
  children: AppRouteRecordRaw[],
  routeModule: AppRouteRecordRaw
) => {
  for (let index = 0; index < children.length; index++) {
    const child = children[index]
    const route = routes.find((item) => item.name === child.name)
    if (!route) {
      continue
    }
    routeModule.children = routeModule.children || []
    if (!routeModule.children.find((item) => item.name === route.name)) {
      routeModule.children?.push(route as unknown as AppRouteRecordRaw)
    }
    if (child.children?.length) {
      addToChildren(routes, child.children, routeModule)
    }
  }
}
