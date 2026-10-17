<template>
  <section v-if="open" class="panel">
    <header>
      <label class="avatar">
        <UserAvatar :src="auth.avatarSrc" :name="auth.displayName" size="lg" />
        <span class="cam"><Icon name="camera" /></span>
        <input type="file" accept="image/*" @change="onAvatar" />
      </label>
      <h1>{{ auth.displayName }}</h1>
      <p v-if="auth.telephone">{{ auth.telephone }}</p>
    </header>
    <p v-if="auth.mustSetPasswordWithoutOld" class="note">首次登录请先设置密码，之后可用账号密码进入。</p>
    <div class="rows">
      <button type="button" @click="goWallet">
        <span class="row-label"><Icon name="wallet" />账户余额</span>
        <Icon name="chev" class="row-chev" />
      </button>
      <button type="button" @click="toggle('profile')">
        <span class="row-label"><Icon name="edit" />编辑资料</span>
        <Icon name="chev" class="row-chev" :class="{ on: section === 'profile' }" />
      </button>
      <form v-if="section === 'profile'" class="fold" @submit.prevent="saveProfile">
        <label>
          <span>用户姓名</span>
          <input v-model="profile.name" required maxlength="32" />
        </label>
        <label>
          <span>用户昵称</span>
          <input v-model="profile.nickname" maxlength="32" />
        </label>
        <label>
          <span>手机号码</span>
          <input v-model="profile.telephone" required maxlength="11" />
        </label>
        <fieldset>
          <legend>用户性别</legend>
          <label v-for="item in genders" :key="item.value" class="radio">
            <input v-model="profile.gender" type="radio" :value="item.value" />
            {{ item.label }}
          </label>
        </fieldset>
        <p v-if="profileError" class="error">{{ profileError }}</p>
        <button class="submit" type="submit" :disabled="profileBusy">{{ profileBusy ? '提交中…' : '提交' }}</button>
      </form>

      <button type="button" @click="toggle('password')">
        <span class="row-label"><Icon name="lock" />{{ auth.mustSetPasswordWithoutOld ? '设置密码' : '修改密码' }}</span>
        <Icon name="chev" class="row-chev" :class="{ on: section === 'password' }" />
      </button>
      <form v-if="section === 'password'" class="fold" @submit.prevent="savePassword">
        <label v-if="!auth.mustSetPasswordWithoutOld">
          <span>当前密码</span>
          <input v-model="secret.old_password" type="password" required autocomplete="current-password" />
        </label>
        <label>
          <span>新密码</span>
          <input v-model="secret.password" type="password" required minlength="8" maxlength="20" autocomplete="new-password" />
        </label>
        <label>
          <span>确认密码</span>
          <input v-model="secret.password_two" type="password" required minlength="8" maxlength="20" autocomplete="new-password" />
        </label>
        <p v-if="secretError" class="error">{{ secretError }}</p>
        <button class="submit" type="submit" :disabled="secretBusy">{{ secretBusy ? '提交中…' : '提交' }}</button>
      </form>

      <button type="button" @click="theme.toggle">
        <span class="row-label"><Icon name="moon" />深色模式</span>
        <i :class="{ on: theme.isDark }" />
      </button>
      <button type="button" @click="about = true">
        <span class="row-label"><Icon name="info" />关于我们</span>
        <Icon name="chev" />
      </button>
    </div>
    <button class="logout" type="button" @click="logout">
      <Icon name="out" />
      退出登录
    </button>
  </section>
  <div v-if="about" class="mask" @click.self="closeAbout">
      <div class="sheet about-sheet" role="dialog" aria-labelledby="about-title">
        <div class="about-hero">
          <span class="about-kicker">需求 · 联系我们</span>
          <h2 id="about-title">成都智臻善算科技有限公司</h2>
        </div>
        <dl>
          <div><dt>联系人</dt><dd>殷先生</dd></div>
          <div><dt>微信 / 电话</dt><dd><a href="tel:17302868369">17302868369</a></dd></div>
          <div><dt>统一社会信用代码</dt><dd>91510106MAKFR2T55W</dd></div>
          <div><dt>公司地址</dt><dd>四川省成都市金牛区光荣西路 67 号 1 栋 4 楼 517 号</dd></div>
          <div><dt>公司网站</dt><dd><a href="http://hipp.site/">http://hipp.site/</a></dd></div>
          <div>
            <dt>备案号</dt>
            <dd><a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener">蜀ICP备2024076719号-1</a></dd>
          </div>
        </dl>
        <button type="button" class="submit" @click="closeAbout">关闭</button>
      </div>
    </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import Icon from '@/components/Icon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useRouter } from 'vue-router'
import { getDictDetails, getInfo, resetPassword, updateCurrentUser, uploadAvatar } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { confirmDialog, toast } from '@/utils/toast'

const props = defineProps({
  open: { type: Boolean, default: false },
  initialSection: { type: String, default: '' },
  about: { type: Boolean, default: false }
})
const emit = defineEmits(['close-about'])

const auth = useAuthStore()
const theme = useThemeStore()
const router = useRouter()
const section = ref('')
const about = ref(false)

function closeAbout() {
  about.value = false
  emit('close-about')
}
watch(() => props.about, (value) => {
  about.value = !!value
}, { immediate: true })
const profileBusy = ref(false)
const secretBusy = ref(false)
const profileError = ref('')
const secretError = ref('')
const profile = reactive({ name: '', nickname: '', telephone: '', gender: '' })
const secret = reactive({ old_password: '', password: '', password_two: '' })
const genders = ref([
  { label: '男', value: '0' },
  { label: '女', value: '1' }
])

watch(() => [props.open, props.initialSection], () => {
  if (!props.open) return
  if (props.initialSection === 'about') {
    section.value = ''
    about.value = true
    return
  }
  section.value = props.initialSection || ''
  if (section.value === 'profile') loadProfile()
}, { immediate: true })

function toggle(name) {
  section.value = section.value === name ? '' : name
  if (section.value === 'profile') loadProfile()
}
function goWallet() {
  router.push('/wallet')
}
async function loadProfile() {
  const res = await getInfo()
  const user = res.data || {}
  profile.name = user.name || ''
  profile.nickname = user.nickname || ''
  profile.telephone = user.telephone || ''
  profile.gender = user.gender == null ? '' : String(user.gender)
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
async function saveProfile() {
  profileError.value = ''
  if (!/^1\d{10}$/.test(String(profile.telephone || ''))) {
    profileError.value = '手机号码不正确'
    return
  }
  profileBusy.value = true
  try {
    const res = await updateCurrentUser({ ...profile })
    auth.patchProfile(res.data || profile)
    toast('更新成功')
    section.value = ''
  } catch (err) {
    profileError.value = err.message || '更新失败'
  } finally {
    profileBusy.value = false
  }
}
async function savePassword() {
  secretError.value = ''
  if (secret.password.length < 8 || secret.password.length > 20) {
    secretError.value = '长度在 8 到 20 个字符'
    return
  }
  if (secret.password !== secret.password_two) {
    secretError.value = '两次输入的密码不一致'
    return
  }
  secretBusy.value = true
  try {
    const payload = { password: secret.password, password_two: secret.password_two }
    if (!auth.mustSetPasswordWithoutOld) payload.old_password = secret.old_password
    await resetPassword(payload)
    auth.mustSetPasswordWithoutOld = false
    const phone = (auth.telephone || '').trim()
    if (phone) {
      try {
        await auth.login(phone, secret.password)
      } catch (err) {
        toast('密码已更新，请用新密码重新登录')
        auth.clear()
        router.replace('/login')
        return
      }
    }
    secret.old_password = ''
    secret.password = ''
    secret.password_two = ''
    toast('修改成功')
    section.value = ''
  } catch (err) {
    secretError.value = err.message || '修改失败'
  } finally {
    secretBusy.value = false
  }
}
async function logout() {
  const ok = await confirmDialog({ title: '退出登录', message: '确定退出当前账号吗？', confirmText: '退出' })
  if (!ok) return
  auth.clear()
  router.replace('/login')
}
</script>

<style scoped>
.panel {
  position: absolute;
  inset: 0;
  z-index: 6;
  overflow: auto;
  background: var(--paper);
  padding: 36px 20px 64px;
}
header { text-align: center; padding: 12px 0 24px; }
.avatar {
  width: 96px; height: 96px; margin: 0 auto 14px;
  display: grid; place-items: center;
  cursor: pointer; position: relative;
}
.cam {
  position: absolute; right: 0; bottom: 0;
  width: 28px; height: 28px; border-radius: 50%;
  display: grid; place-items: center;
  background: var(--brass); color: #1a140c;
  box-shadow: 0 4px 10px rgba(20, 32, 43, 0.18);
  pointer-events: none;
}
.cam :deep(.ico) { width: 14px; height: 14px; }
.avatar input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
h1 { margin: 0; font-family: var(--serif); font-size: 32px; }
header p { margin: 6px 0 0; color: var(--text-3); }
.note {
  max-width: 680px; margin: 0 auto 12px;
  background: rgba(166, 124, 61, 0.12); border-radius: 14px; padding: 12px 14px;
}
.rows { max-width: 680px; margin: 0 auto; border-top: 1px solid var(--line); }
.rows > button, .fold {
  width: 100%;
}
.rows > button {
  display: flex; justify-content: space-between; align-items: center;
  padding: 15px 4px; border: 0; border-bottom: 1px solid var(--line);
  background: transparent; font-size: 16px; text-align: left;
}
.rows > button:hover { color: var(--brass); }
.row-label { display: inline-flex; align-items: center; gap: 10px; }
.row-chev { color: var(--text-3); transition: transform 0.15s ease; }
.row-chev.on { transform: rotate(90deg); color: var(--brass); }
i {
  width: 42px; height: 24px; border-radius: 999px; background: var(--paper-2); position: relative;
}
i::after {
  content: ""; position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%;
  background: var(--surface); transition: transform 0.2s ease;
}
i.on { background: var(--brass); }
i.on::after { transform: translateX(18px); }
.fold {
  display: flex; flex-direction: column; gap: 12px;
  padding: 4px 4px 16px; border-bottom: 1px solid var(--line);
}
.fold span, legend { display: block; color: var(--text-2); font-size: 13px; margin-bottom: 6px; }
.fold input:not([type="radio"]) {
  width: 100%; border: 0; background: var(--paper-2); border-radius: 12px; padding: 12px 14px; outline: none;
}
.fold input:not([type="radio"]):focus { box-shadow: 0 0 0 3px rgba(166, 124, 61, 0.18); }
fieldset { border: 0; border-radius: 12px; background: var(--paper-2); display: flex; gap: 16px; }
.radio { display: flex; align-items: center; gap: 6px; }
.submit {
  border: 0; border-radius: 12px; padding: 12px; font-weight: 650;
  background: var(--brass); color: #1a140c;
}
.submit:hover:not(:disabled) { background: var(--brass-2); }
.error { color: var(--danger); margin: 0; }
.logout {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  max-width: 680px; margin: 28px auto 0; width: 100%;
  border: 0; border-radius: 12px;
  background: rgba(141, 59, 59, 0.08); color: var(--danger); font-weight: 650; padding: 12px;
}
.logout:hover { background: rgba(141, 59, 59, 0.08); }
.mask {
  position: fixed; inset: 0; z-index: 80; background: rgba(12, 16, 20, 0.46);
  display: grid; place-items: center; padding: 24px;
}
.sheet {
  width: min(520px, 100%); background: var(--surface); color: var(--text);
  border-radius: 16px; padding: 22px; border: 0; box-shadow: var(--shadow);
}
.about-sheet { padding: 0 0 22px; overflow: hidden; }
.about-hero {
  padding: 22px 22px 18px;
  background:
    radial-gradient(120% 80% at 100% 0%, rgba(230, 201, 138, 0.35), transparent 55%),
    linear-gradient(145deg, #1a140c 0%, #2c2418 55%, #3d3224 100%);
  color: #f6f1e8;
}
.about-kicker {
  display: block; font-size: 12px; letter-spacing: 0.08em;
  color: var(--brass-2); margin-bottom: 8px; text-transform: uppercase;
}
.sheet h2 { margin: 0 0 8px; font-family: var(--serif); font-size: 22px; }
.about-sheet h2 { margin: 0; color: #f6f1e8; font-size: 22px; line-height: 1.35; }
.sheet dl { margin: 0 0 16px; }
.about-sheet dl { margin: 0 22px 16px; }
.sheet div { display: flex; justify-content: space-between; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--line); }
.sheet dt { color: var(--text-2); flex: none; min-width: 7.5em; }
.sheet dd { margin: 0; text-align: right; line-height: 1.5; }
.sheet a { color: var(--teal); }
.about-sheet .submit { margin: 0 22px; width: calc(100% - 44px); }
</style>
