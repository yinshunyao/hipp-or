<template>
  <section class="page">
    <RouterLink class="back" to="/mine">返回我的</RouterLink>
    <h1>编辑资料</h1>
    <form @submit.prevent="submit">
      <label class="avatar-row">
        <span>头像</span>
        <UserAvatar :src="auth.avatarSrc" :name="auth.displayName" size="lg" />
        <input type="file" accept="image/*" @change="onAvatar" />
      </label>
      <label>
        <span>用户姓名</span>
        <input v-model="form.name" required maxlength="32" />
      </label>
      <label>
        <span>用户昵称</span>
        <input v-model="form.nickname" maxlength="32" />
      </label>
      <label>
        <span>手机号码</span>
        <input v-model="form.telephone" required maxlength="11" />
      </label>
      <fieldset>
        <legend>用户性别</legend>
        <label v-for="item in genders" :key="item.value" class="radio">
          <input v-model="form.gender" type="radio" :value="item.value" />
          {{ item.label }}
        </label>
      </fieldset>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="busy">{{ busy ? '提交中…' : '提交' }}</button>
    </form>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { RouterLink } from 'vue-router'
import { getDictDetails, getInfo, updateCurrentUser, uploadAvatar } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { toast } from '@/utils/toast'

const auth = useAuthStore()
const form = reactive({ name: '', nickname: '', telephone: '', gender: '' })
const genders = ref([
  { label: '男', value: '0' },
  { label: '女', value: '1' }
])
const busy = ref(false)
const error = ref('')

async function load() {
  const res = await getInfo()
  const user = res.data || {}
  form.name = user.name || ''
  form.nickname = user.nickname || ''
  form.telephone = user.telephone || ''
  form.gender = user.gender == null ? '' : String(user.gender)
  try {
    const dict = await getDictDetails(['sys_vadmin_gender'])
    const list = dict.data && dict.data.sys_vadmin_gender
    if (Array.isArray(list) && list.length) {
      genders.value = list.map((item) => ({ label: item.label, value: String(item.value) }))
    }
  } catch (err) { /* 使用默认选项 */ }
}
async function onAvatar(event) {
  const file = event.target.files && event.target.files[0]
  event.target.value = ''
  if (!file) return
  const res = await uploadAvatar(file)
  const avatar = (res.data && (res.data.avatar || res.data)) || ''
  if (typeof avatar === 'string' && avatar) auth.avatar = avatar
  else await auth.fetchInfo()
  toast('头像已更新')
}
async function submit() {
  error.value = ''
  if (!/^1\d{10}$/.test(String(form.telephone || ''))) {
    error.value = '手机号码不正确'
    return
  }
  busy.value = true
  try {
    const res = await updateCurrentUser({ ...form })
    auth.patchProfile(res.data || form)
    toast('更新成功')
  } catch (err) {
    error.value = err.message || '更新失败'
  } finally {
    busy.value = false
  }
}
onMounted(load)
</script>

<style scoped>
.page { max-width: 640px; margin: 0 auto; padding: 28px 20px 64px; }
.back { color: var(--text-3); text-decoration: none; }
h1 { font-family: var(--serif); font-size: 34px; margin: 8px 0 18px; }
form { display: flex; flex-direction: column; gap: 14px; }
label span, legend { display: block; color: var(--text-2); font-size: 13px; margin-bottom: 6px; }
input[type="text"], input:not([type="radio"]):not([type="file"]) {
  width: 100%; border: 1px solid var(--line); background: var(--surface); border-radius: 12px; padding: 12px 14px;
}
fieldset { border: 1px solid var(--line); border-radius: 12px; display: flex; gap: 16px; }
.radio { display: flex; align-items: center; gap: 6px; }
.avatar-row { display: grid; grid-template-columns: 1fr auto; align-items: center; }
.avatar-row input { grid-column: 1 / -1; margin-top: 8px; }
button[type="submit"] {
  border: 0; border-radius: 12px; padding: 12px; font-weight: 650;
  background: var(--brass); color: #1a140c;
}
.error { color: var(--danger); margin: 0; }
</style>
