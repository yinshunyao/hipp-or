/**
 * 部署在子路径（Vite base / Vue Router history base）时：
 * - 登录页 URL 的 redirect 查询参数使用「浏览器地址栏可见的完整路径」（含 /manager 前缀），便于与网关日志、人工核对一致
 * - router.push / next({ path }) 必须使用不含 base 的 Vue Router path，故跳转前需归一化
 */

export function joinPublicPathForLoginRedirect(routerPath: string): string {
  const base = (import.meta.env.BASE_URL || '/').replace(/\/$/, '')
  const path = routerPath.startsWith('/') ? routerPath : `/${routerPath}`
  if (!base) return path
  return `${base}${path}`
}

export function normalizeLoginRedirectToRouterPath(raw: string | undefined | null): string {
  if (raw == null || raw === '') return ''
  let s = String(raw).trim()
  try {
    s = decodeURIComponent(s)
  } catch {
    // ignore
  }
  if (!s) return ''
  const base = (import.meta.env.BASE_URL || '/').replace(/\/$/, '')
  if (base && (s === base || s.startsWith(`${base}/`))) {
    const rest = s === base ? '/' : s.slice(base.length)
    return rest.startsWith('/') ? rest : `/${rest}`
  }
  if (s.startsWith('/')) return s
  return `/${s}`
}
