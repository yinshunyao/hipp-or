<template>
  <div class="login">
    <section class="story">
      <span class="mark">需求</span>
      <p class="eyebrow">{{ geoPublic.companyShort }} · {{ geoPublic.displayName }}</p>
      <h1>把需求说清楚，<br />再谈怎么做。</h1>
      <p class="one-liner">{{ geoPublic.oneLiner }}</p>
      <p class="entry">官方入口 {{ geoPublic.canonicalUrl }}</p>

      <div class="adv-block">
        <h2>为什么选它</h2>
        <ul>
          <li v-for="(item, i) in geoPublic.advantages" :key="i">
            <strong>{{ item.title }}</strong>
            <span>{{ item.text }}</span>
          </li>
        </ul>
      </div>

      <div class="shot-block">
        <figure v-for="(shot, i) in loginShots" :key="i">
          <img :src="geoAsset(shot.src)" :alt="shot.alt" loading="lazy" />
          <figcaption><em>{{ shot.proves }}</em> — {{ shot.caption }}</figcaption>
        </figure>
      </div>

      <div class="faq-block">
        <div class="faq-head">
          <h2>常见问题</h2>
          <RouterLink class="faq-link" to="/faq">查看 FAQ 与更多截图</RouterLink>
        </div>
        <details v-for="(item, i) in geoPublic.faqItems.slice(0, 4)" :key="i" class="faq-item" :open="i === 0">
          <summary>{{ item.q }}</summary>
          <p>{{ item.a }}</p>
        </details>
      </div>

      <div class="bounds">
        <h3>不做</h3>
        <ul>
          <li v-for="(line, i) in geoPublic.doNotClaim" :key="i">{{ line }}</li>
        </ul>
      </div>
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
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { sendLoginSms } from '@/api/auth'
import Icon from '@/components/Icon.vue'
import { faqJsonLd, geoAsset, geoPublic } from '@/data/geoPublic'

const loginShots = geoPublic.shots.slice(0, 2)
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
let ldScript = null

onMounted(() => {
  ldScript = document.createElement('script')
  ldScript.type = 'application/ld+json'
  ldScript.id = 'hipp-or-faq-ld'
  ldScript.textContent = JSON.stringify(faqJsonLd())
  document.head.appendChild(ldScript)
})
onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
  if (ldScript && ldScript.parentNode) ldScript.parentNode.removeChild(ldScript)
})

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
</script>

<style scoped>
.login { min-height: 100vh; display: grid; grid-template-columns: 1.15fr 0.85fr; }
.story {
  padding: 36px 6vw 40px;
  color: #f4efe6;
  background:
    linear-gradient(rgba(244, 239, 230, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(244, 239, 230, 0.045) 1px, transparent 1px),
    radial-gradient(420px 180px at 10% 16%, rgba(198, 161, 90, 0.28), transparent 70%),
    #14202b;
  background-size: 28px 28px, 28px 28px, auto, auto;
  display: flex;
  flex-direction: column;
  overflow: auto;
  max-height: 100vh;
}
.mark {
  align-self: flex-start; width: max-content;
  min-width: 52px; height: 52px; padding: 0 12px; border-radius: 14px; display: grid; place-items: center;
  background: radial-gradient(circle at 32% 28%, #3d5366, #15202a 72%);
  box-shadow: inset 0 0 0 1px rgba(230, 201, 138, 0.28);
  color: white; text-decoration: none; font-family: var(--serif); font-size: 16px;
  margin-bottom: 20px;
}
.eyebrow { margin: 0 0 8px; color: #b8c2cc; font-size: 13px; letter-spacing: 0.02em; }
.story h1 { font-family: var(--serif); font-size: clamp(32px, 3.6vw, 52px); line-height: 1.15; margin: 0 0 12px; }
.one-liner { max-width: 34rem; color: #d5dde4; margin: 0 0 8px; line-height: 1.65; }
.entry { margin: 0 0 18px; color: #9aa7b3; font-size: 13px; }
.adv-block { margin-bottom: 16px; }
.adv-block h2 { font-family: var(--serif); font-size: 18px; margin: 0 0 8px; font-weight: 650; }
.adv-block ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.adv-block li {
  padding: 10px 12px; border-radius: 10px;
  background: rgba(244, 239, 230, 0.06);
  border: 1px solid rgba(244, 239, 230, 0.1);
  display: grid; gap: 4px;
}
.adv-block strong { font-size: 14px; color: #f4efe6; }
.adv-block span { font-size: 13px; color: #b8c2cc; line-height: 1.55; }
.shot-block { display: grid; gap: 12px; margin-bottom: 16px; }
.shot-block figure { margin: 0; }
.shot-block img {
  display: block; width: 100%; border-radius: 10px;
  border: 1px solid rgba(244, 239, 230, 0.12);
}
.shot-block figcaption { margin-top: 6px; font-size: 12px; color: #9aa7b3; line-height: 1.5; }
.shot-block em { font-style: normal; color: #e6c98a; font-weight: 650; }
.faq-block { margin-bottom: 18px; }
.faq-head {
  display: flex; align-items: baseline; justify-content: space-between; gap: 12px;
  margin-bottom: 8px;
}
.faq-head h2 { font-family: var(--serif); font-size: 20px; margin: 0; font-weight: 650; }
.faq-link { color: #e6c98a; font-size: 13px; text-decoration: underline; text-underline-offset: 3px; }
.faq-item {
  border-top: 1px solid rgba(244, 239, 230, 0.12);
  padding: 10px 0;
}
.faq-item summary {
  cursor: pointer; list-style: none; font-weight: 600; line-height: 1.45;
}
.faq-item summary::-webkit-details-marker { display: none; }
.faq-item p { margin: 8px 0 0; color: #c5ced6; font-size: 14px; line-height: 1.65; }
.bounds {
  margin-top: auto; padding: 14px 14px 12px; border-radius: 12px;
  background: rgba(244, 239, 230, 0.06);
  border: 1px solid rgba(244, 239, 230, 0.1);
}
.bounds h3 { margin: 0 0 8px; font-size: 14px; color: #e6c98a; font-weight: 650; }
.bounds ul { margin: 0; padding-left: 1.15em; color: #b8c2cc; font-size: 13px; line-height: 1.65; }
.panel {
  padding: 48px 8vw; display: flex; flex-direction: column; gap: 14px;
  background: var(--paper); max-width: 520px; width: 100%; justify-self: stretch;
  box-sizing: border-box;
}
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
  .story { max-height: none; min-height: auto; padding: 28px 20px; }
  .panel { padding: 28px 20px 48px; max-width: none; }
}
</style>
