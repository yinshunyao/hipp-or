import type { RouteRecordRaw } from 'vue-router'
import type { Router } from 'vue-router'
import { getRoleMenusApi } from '@/api/login'
import { usePermissionStoreWithOut } from '@/store/modules/permission'

/**
 * 拉取后端菜单并注册动态路由。若接口未返回成功数据（业务失败、网络等），仍生成前端合并后的路由表并置位 isAddRouters，返回 false 以便跳转无权限说明页。
 */
export async function loadDynamicMenuRoutes(
  router: Router,
  permissionStore: ReturnType<typeof usePermissionStoreWithOut>
): Promise<boolean> {
  const res = await getRoleMenusApi()
  const routers = res?.data ?? []
  await permissionStore.generateRoutes(routers).catch(() => {})
  permissionStore.getAddRouters.forEach((route) => {
    router.addRoute(route as RouteRecordRaw)
  })
  permissionStore.setIsAddRouters(true)
  return !!res
}
