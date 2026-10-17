import { createRouter, createWebHistory } from 'vue-router'
import { SHOW_BUSINESS_SCENE } from '@/config/features'
import { useAuthStore } from '@/stores/auth'

const businessRoute = SHOW_BUSINESS_SCENE
  ? { path: '/business', name: 'business', meta: { auth: true, shell: true }, component: () => import('@/views/SceneView.vue'), props: { scene: 'business' } }
  : { path: '/business', redirect: '/requirement' }

const routes = [
  { path: '/', name: 'entry', component: { render: () => null } },
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
  { path: '/share/:token', name: 'share', component: () => import('@/views/ShareView.vue') },
  { path: '/a/:token', name: 'access', component: () => import('@/views/AccessView.vue') },
  { path: '/legal/:kind', name: 'legal', component: () => import('@/views/LegalView.vue') },
  { path: '/topics', redirect: '/requirement' },
  { path: '/chat/:id', name: 'chat', meta: { auth: true, shell: true }, component: () => import('@/views/ChatView.vue') },
  { path: '/requirement', name: 'requirement', meta: { auth: true, shell: true }, component: () => import('@/views/SceneView.vue'), props: { scene: 'requirement' } },
  businessRoute,
  { path: '/wallet', name: 'wallet', meta: { auth: true, shell: true }, component: () => import('@/views/WalletView.vue') },
  { path: '/mine/profile', redirect: { path: '/requirement', query: { account: 'profile' } } },
  { path: '/mine/password', redirect: { path: '/requirement', query: { account: 'password' } } },
  { path: '/mine/about', redirect: { path: '/requirement', query: { account: 'about' } } },
  { path: '/mine', redirect: '/requirement' }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  auth.syncSso()
  if (!auth.token) {
    await auth.trySso()
  }
  if (auth.token && !auth.ready) {
    try {
      await auth.fetchInfo()
    } catch (err) {
      auth.clear({ broadcast: false, clearManager: false })
      await auth.trySso()
    }
  }
  if (to.name === 'entry') {
    return auth.token ? { name: 'requirement' } : { name: 'login' }
  }
  if (to.meta.auth && !auth.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.token) {
    const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : '/requirement'
    return redirect
  }
  return true
})

export default router
