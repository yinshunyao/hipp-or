<template>
  <section class="mine">
    <header>
      <UserAvatar class="avatar" :src="auth.avatarSrc" :name="auth.displayName" size="lg" />
      <h1>{{ auth.displayName }}</h1>
      <p v-if="auth.telephone">{{ auth.telephone }}</p>
    </header>
    <p v-if="auth.mustSetPasswordWithoutOld" class="note">首次登录请先设置密码，之后可用账号密码进入。</p>
    <nav>
      <RouterLink to="/mine/profile">编辑资料</RouterLink>
      <RouterLink to="/mine/password">{{ auth.mustSetPasswordWithoutOld ? '设置密码' : '修改密码' }}</RouterLink>
      <button type="button" @click="theme.toggle">
        深色模式
        <i :class="{ on: theme.isDark }" />
      </button>
      <RouterLink to="/mine/about">关于我们</RouterLink>
    </nav>
    <button class="logout" type="button" @click="logout">退出登录</button>
  </section>
</template>

<script setup>
import { RouterLink, useRouter } from 'vue-router'
import UserAvatar from '@/components/UserAvatar.vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { confirmDialog } from '@/utils/toast'

const auth = useAuthStore()
const theme = useThemeStore()
const router = useRouter()

async function logout() {
  const ok = await confirmDialog({ title: '退出登录', message: '确定退出当前账号吗？', confirmText: '退出' })
  if (!ok) return
  auth.clear()
  router.replace('/login')
}
</script>

<style scoped>
.mine { max-width: 680px; margin: 0 auto; padding: 36px 20px 64px; }
header { text-align: center; padding: 12px 0 24px; }
.avatar { margin: 0 auto 12px; }
h1 { margin: 0; font-family: var(--serif); font-size: 32px; }
header p { margin: 6px 0 0; color: var(--text-3); }
.note {
  background: rgba(166, 124, 61, 0.12); border-radius: 14px; padding: 12px 14px; color: var(--text);
}
nav { display: flex; flex-direction: column; margin-top: 12px; border-top: 1px solid var(--line); }
nav a, nav button {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 4px; border: 0; border-bottom: 1px solid var(--line);
  background: transparent; text-decoration: none; font-size: 16px; text-align: left;
}
i {
  width: 42px; height: 24px; border-radius: 999px; background: var(--paper-2); position: relative;
}
i::after {
  content: ""; position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%;
  background: var(--surface); transition: transform 0.2s ease;
}
i.on { background: var(--brass); }
i.on::after { transform: translateX(18px); }
.logout {
  margin-top: 28px; width: 100%; border: 0; border-radius: 999px; padding: 12px;
  background: transparent; color: var(--danger); font-weight: 650;
}
</style>
