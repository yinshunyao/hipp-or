<template>
  <section class="page">
    <RouterLink class="back" to="/mine">返回我的</RouterLink>
    <h1>{{ auth.mustSetPasswordWithoutOld ? '设置密码' : '修改密码' }}</h1>
    <form @submit.prevent="submit">
      <label v-if="!auth.mustSetPasswordWithoutOld">
        <span>当前密码</span>
        <input v-model="form.old_password" type="password" required autocomplete="current-password" />
      </label>
      <label>
        <span>新密码</span>
        <input v-model="form.password" type="password" required minlength="8" maxlength="20" autocomplete="new-password" />
      </label>
      <label>
        <span>确认密码</span>
        <input v-model="form.password_two" type="password" required minlength="8" maxlength="20" autocomplete="new-password" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="busy">{{ busy ? '提交中…' : '提交' }}</button>
    </form>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { resetPassword } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { toast } from '@/utils/toast'

const auth = useAuthStore()
const router = useRouter()
const form = reactive({ old_password: '', password: '', password_two: '' })
const busy = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (form.password.length < 8 || form.password.length > 20) {
    error.value = '长度在 8 到 20 个字符'
    return
  }
  if (form.password !== form.password_two) {
    error.value = '两次输入的密码不一致'
    return
  }
  busy.value = true
  try {
    const payload = { password: form.password, password_two: form.password_two }
    if (!auth.mustSetPasswordWithoutOld) payload.old_password = form.old_password
    await resetPassword(payload)
    auth.mustSetPasswordWithoutOld = false
    const phone = (auth.telephone || '').trim()
    if (phone) {
      try {
        await auth.login(phone, form.password)
      } catch (err) {
        toast('密码已更新，请用新密码重新登录')
        auth.clear()
        router.replace('/login')
        return
      }
    }
    toast('修改成功')
    router.replace('/')
  } catch (err) {
    error.value = err.message || '修改失败'
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.page { max-width: 640px; margin: 0 auto; padding: 28px 20px 64px; }
.back { color: var(--text-3); text-decoration: none; }
h1 { font-family: var(--serif); font-size: 34px; }
form { display: flex; flex-direction: column; gap: 14px; }
label span { display: block; color: var(--text-2); font-size: 13px; margin-bottom: 6px; }
input {
  width: 100%; border: 1px solid var(--line); background: var(--surface); border-radius: 12px; padding: 12px 14px;
}
button {
  border: 0; border-radius: 999px; padding: 12px; font-weight: 700;
  background: linear-gradient(160deg, var(--brass-2), var(--brass)); color: #1a140c;
}
.error { color: var(--danger); margin: 0; }
</style>
