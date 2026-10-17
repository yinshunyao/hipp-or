import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import { onRemoteLogout } from './utils/sso'
import './styles/tokens.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
useThemeStore().apply()

window.addEventListener('hipp-auth-lost', () => {
  const auth = useAuthStore()
  if (!auth.token) return
  auth.clear({ broadcast: false })
  const current = router.currentRoute.value
  if (current.meta.auth) {
    router.push({ name: 'login', query: { redirect: current.fullPath } })
  }
})

onRemoteLogout(() => {
  const auth = useAuthStore()
  if (!auth.token) return
  auth.clear({ broadcast: false })
  const current = router.currentRoute.value
  if (current.meta.auth) {
    router.push({ name: 'login', query: { redirect: current.fullPath } })
  }
})

app.mount('#app')
