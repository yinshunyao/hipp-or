<template>
  <div class="login">
    <section class="story">
      <span class="mark">需求</span>
      <h1>把需求说清楚，<br />再谈怎么做。</h1>
      <p>短信或密码登录后，即可进入需求会话。协议内容与小程序一致。</p>
    </section>
    <section class="panel">
      <span class="back">智臻善算</span>
      <h2>登录</h2>
      <div class="modes">
        <button type="button" :class="{ on: mode === 'sms' }" @click="mode = 'sms'">短信登录</button>
        <button type="button" :class="{ on: mode === 'password' }" @click="mode = 'password'">账号密码</button>
      </div>
      <label>
        <span>{{ mode === 'sms' ? '手机号' : '手机号或账号' }}</span>
        <input v-model="telephone" maxlength="11" inputmode="numeric" autocomplete="username" />
      </label>
      <label v-if="mode === 'sms'">
        <span>验证码</span>
        <div class="split">
          <input v-model="code" maxlength="8" inputmode="numeric" />
          <button type="button" class="minor" :disabled="cooldown > 0" @click="sendCode">
            {{ cooldown > 0 ? `${cooldown}s` : '获取验证码' }}
          </button>
        </div>
      </label>
      <label v-else>
        <span>密码</span>
        <div class="split">
          <input v-model="password" :type="visible ? 'text' : 'password'" maxlength="20" autocomplete="current-password" />
          <button type="button" class="minor icon-btn" :aria-label="visible ? '隐藏密码' : '显示密码'" @click="visible = !visible">
            <Icon :name="visible ? 'eyeOff' : 'eye'" />
          </button>
        </div>
      </label>
      <button class="submit" type="button" :disabled="!agreed || busy" @click="submit">
        {{ busy ? '登录中…' : '登录' }}
      </button>
      <label class="agree">
        <input v-model="agreed" type="checkbox" @change="onAgreeChange" />
        <span>
          允许我们在必要场景下合理使用您的个人信息，且阅读并同意
          <button type="button" @click="openLegal('agreement')">《用户协议》</button>、
          <button type="button" @click="openLegal('privacy')">《隐私协议》</button>
        </span>
      </label>
      <p v-if="hint" class="hint">{{ hint }}</p>
    </section>

    <div v-if="sheet" class="mask">
      <div class="sheet">
        <h3>{{ sheet.title }}</h3>
        <div ref="legalBox" class="body" @scroll="onLegalScroll">{{ sheet.body }}</div>
        <button type="button" :disabled="!sheet.ready" @click="closeLegal">
          {{ sheet.ready ? (sheet.returnOnly ? '返回' : '我已阅读') : '请滚动到底' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sendLoginSms } from '@/api/auth'
import Icon from '@/components/Icon.vue'
import { legalDoc } from '@/data/legal'
import { useAuthStore } from '@/stores/auth'
import { toast } from '@/utils/toast'

const KEY = 'hipp_web_legal'
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const mode = ref('sms')
const telephone = ref('')
const password = ref('')
const code = ref('')
const visible = ref(false)
const agreed = ref(false)
const busy = ref(false)
const hint = ref('')
const cooldown = ref(0)
const declined = ref(false)
const sheet = ref(null)
const legalBox = ref(null)
let timer = 0

function readFlags() {
  try { return JSON.parse(localStorage.getItem(KEY) || '{}') } catch (err) { return {} }
}
function writeFlag(kind) {
  const flags = readFlags()
  flags[kind] = true
  localStorage.setItem(KEY, JSON.stringify(flags))
}
function bothConfirmed() {
  const flags = readFlags()
  return !!flags.agreement && !!flags.privacy
}
if (bothConfirmed()) agreed.value = true

function onAgreeChange() {
  if (!agreed.value) declined.value = true
}
async function openLegal(kind) {
  const doc = legalDoc(kind)
  const returnOnly = !!readFlags()[kind]
  sheet.value = { ...doc, kind, ready: returnOnly, returnOnly }
  await nextTick()
  if (legalBox.value && legalBox.value.scrollHeight <= legalBox.value.clientHeight + 8) {
    sheet.value.ready = true
  }
}
function onLegalScroll() {
  const el = legalBox.value
  if (!el || !sheet.value) return
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 8) sheet.value.ready = true
}
function closeLegal() {
  if (!sheet.value || !sheet.value.ready) return
  writeFlag(sheet.value.kind)
  sheet.value = null
  if (bothConfirmed() && !declined.value) agreed.value = true
}
async function sendCode() {
  if (!/^1\d{10}$/.test(telephone.value.trim())) {
    toast('请输入 11 位手机号')
    return
  }
  await sendLoginSms(telephone.value.trim())
  toast('验证码已发送')
  cooldown.value = 60
  timer = window.setInterval(() => {
    cooldown.value -= 1
    if (cooldown.value <= 0) window.clearInterval(timer)
  }, 1000)
}
async function submit() {
  hint.value = ''
  if (!agreed.value) {
    hint.value = '请阅读并同意协议'
    return
  }
  busy.value = true
  try {
    if (mode.value === 'sms') await auth.smsLogin(telephone.value, code.value)
    else await auth.login(telephone.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/requirement'
    if (auth.mustSetPasswordWithoutOld) router.replace({ path: '/requirement', query: { account: 'password' } })
    else router.replace(redirect)
  } catch (err) {
    hint.value = err.message || '登录失败'
  } finally {
    busy.value = false
  }
}
onBeforeUnmount(() => { if (timer) window.clearInterval(timer) })
</script>

<style scoped>
.login { min-height: 100vh; display: grid; grid-template-columns: 1.05fr 0.95fr; }
.story {
  padding: 48px 8vw;
  color: #f4efe6;
  background:
    linear-gradient(rgba(244, 239, 230, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(244, 239, 230, 0.045) 1px, transparent 1px),
    radial-gradient(420px 180px at 10% 16%, rgba(198, 161, 90, 0.28), transparent 70%),
    #14202b;
  background-size: 28px 28px, 28px 28px, auto, auto;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.mark {
  align-self: flex-start; width: max-content;
  min-width: 52px; height: 52px; padding: 0 12px; border-radius: 14px; display: grid; place-items: center;
  background: radial-gradient(circle at 32% 28%, #3d5366, #15202a 72%);
  box-shadow: inset 0 0 0 1px rgba(230, 201, 138, 0.28);
  color: white; text-decoration: none; font-family: var(--serif); font-size: 16px;
  margin-bottom: auto;
}
.story h1 { font-family: var(--serif); font-size: clamp(36px, 4vw, 58px); line-height: 1.15; margin: 0 0 12px; }
.story p { max-width: 28rem; color: #d5dde4; }
.panel { padding: 48px 8vw; display: flex; flex-direction: column; gap: 14px; background: var(--paper); }
.back { color: var(--text-3); text-decoration: none; }
h2 { font-family: var(--serif); font-size: 36px; margin: 0; }
.modes {
  display: grid; grid-template-columns: 1fr 1fr; gap: 4px;
  padding: 4px; border-radius: 12px; background: var(--paper-2);
}
.modes button, .minor, .submit, .sheet button, .agree button {
  border: 0; background: transparent;
}
.modes button { padding: 9px 12px; border-radius: 9px; color: var(--text-2); font-weight: 600; }
.modes button.on { background: var(--surface); color: var(--text); box-shadow: 0 1px 2px rgba(20, 32, 43, 0.08); }
label span { display: block; font-size: 13px; color: var(--text-2); margin-bottom: 6px; }
input:not([type="checkbox"]):not([type="radio"]) {
  width: 100%; border: 0; background: var(--paper-2); border-radius: 12px;
  padding: 12px 14px; outline: none;
}
input:focus { box-shadow: 0 0 0 3px rgba(166, 124, 61, 0.18); }
.split { display: flex; gap: 8px; align-items: center; }
.minor { white-space: nowrap; color: var(--teal); font-weight: 650; padding: 0 4px; }
.icon-btn {
  width: 40px; height: 40px; display: grid; place-items: center;
  border-radius: 10px; color: var(--text-2);
}
.icon-btn:hover { background: var(--paper-2); color: var(--text); }
.submit {
  margin-top: 6px; border-radius: 12px; padding: 13px; background: var(--brass);
  color: #1a140c; font-weight: 650;
}
.submit:hover:not(:disabled) { background: var(--brass-2); }
.submit:disabled { opacity: 0.45; }
.agree {
  display: flex; gap: 8px; align-items: flex-start;
  font-size: 13px; color: var(--text-2); line-height: 1.55;
}
.agree input {
  width: 16px; height: 16px; margin: 3px 0 0; padding: 0; flex: none;
  accent-color: var(--brass);
}
.agree span { margin: 0; }
.agree button { color: var(--teal); padding: 0; text-decoration: underline; }
.hint { color: var(--danger); margin: 0; }
.mask { position: fixed; inset: 0; background: rgba(12,16,20,.5); display: grid; place-items: center; padding: 20px; }
.sheet {
  width: min(560px, 100%); max-height: min(78vh, 680px); background: var(--surface); border-radius: 16px;
  padding: 20px; display: flex; flex-direction: column; gap: 12px; border: 0; box-shadow: var(--shadow);
}
.sheet h3 { margin: 0; font-family: var(--serif); }
.body { overflow: auto; white-space: pre-wrap; line-height: 1.7; color: var(--text-2); flex: 1; min-height: 180px; }
.sheet button { border-radius: 12px; padding: 10px; background: var(--ink); color: #f6f1e8; font-weight: 650; }
.sheet button:disabled { background: var(--paper-2); color: var(--text-3); }
@media (max-width: 860px) {
  .login { grid-template-columns: 1fr; }
  .story { min-height: 34vh; padding: 28px 20px; }
  .panel { padding: 28px 20px 48px; }
}
</style>
