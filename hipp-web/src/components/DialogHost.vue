<template>
  <div v-if="confirm" class="mask" @click.self="closeConfirm(false)">
    <div class="sheet" role="dialog">
      <h3>{{ confirm.title }}</h3>
      <p>{{ confirm.message }}</p>
      <div class="actions">
        <button class="ghost" type="button" @click="closeConfirm(false)">取消</button>
        <button class="solid" :class="{ danger: confirm.danger }" type="button" @click="closeConfirm(true)">
          {{ confirm.confirmText }}
        </button>
      </div>
    </div>
  </div>
  <div v-if="link" class="mask" @click.self="link = null">
    <div class="sheet" role="dialog">
      <h3>分享链接</h3>
      <input ref="linkInput" :value="link.url" readonly @focus="selectLink" />
      <div class="actions">
        <button class="ghost" type="button" @click="link = null">关闭</button>
        <button class="solid" type="button" @click="copyShownLink">复制</button>
      </div>
    </div>
  </div>
  <div v-if="ask" class="mask" @click.self="closeAsk(null)">
    <form class="sheet" @submit.prevent="closeAsk(draft.trim())">
      <h3>{{ ask.title }}</h3>
      <input v-model="draft" :placeholder="ask.placeholder" maxlength="80" />
      <div class="actions">
        <button class="ghost" type="button" @click="closeAsk(null)">取消</button>
        <button class="solid" type="submit" :disabled="!draft.trim()">保存</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { copyText } from '@/utils/copy'
import { toast } from '@/utils/toast'

const confirm = ref(null)
const ask = ref(null)
const link = ref(null)
const linkInput = ref(null)
const draft = ref('')

function onConfirm(event) {
  confirm.value = event.detail
}
function onAsk(event) {
  ask.value = event.detail
  draft.value = event.detail.value || ''
}
function onLink(event) {
  link.value = event.detail
  nextTick(selectLink)
}
function selectLink(event) {
  const el = (event && event.target) || linkInput.value
  if (!el) return
  el.focus()
  el.select()
}
function copyShownLink() {
  const url = link.value && link.value.url
  if (!url) return
  if (copyText(url)) {
    toast('分享链接已复制')
    link.value = null
    return
  }
  selectLink()
  toast('请选中链接后手动复制')
}
function closeConfirm(ok) {
  const job = confirm.value
  confirm.value = null
  if (job) job.resolve(ok)
}
function closeAsk(value) {
  const job = ask.value
  ask.value = null
  if (job) job.resolve(value)
}

onMounted(() => {
  window.addEventListener('hipp-confirm', onConfirm)
  window.addEventListener('hipp-ask', onAsk)
  window.addEventListener('hipp-copy', onLink)
})
onBeforeUnmount(() => {
  window.removeEventListener('hipp-confirm', onConfirm)
  window.removeEventListener('hipp-ask', onAsk)
  window.removeEventListener('hipp-copy', onLink)
})
</script>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  z-index: 70;
  background: rgba(12, 16, 20, 0.46);
  display: grid;
  place-items: center;
  padding: 24px;
}
.sheet {
  width: min(420px, 100%);
  background: var(--surface);
  color: var(--text);
  border-radius: 16px;
  padding: 22px;
  box-shadow: var(--shadow);
  border: 0;
}
h3 { margin: 0 0 8px; font-family: var(--serif); font-size: 22px; font-weight: 650; }
p { margin: 0; color: var(--text-2); }
input {
  width: 100%;
  margin-top: 12px;
  border: 0;
  background: var(--paper-2);
  border-radius: 12px;
  padding: 12px 14px;
  outline: none;
}
input:focus { box-shadow: 0 0 0 3px rgba(166, 124, 61, 0.18); }
.actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }
button {
  border: 0;
  border-radius: 12px;
  padding: 10px 16px;
  font-weight: 600;
}
.ghost { background: var(--paper-2); color: var(--text-2); }
.ghost:hover { background: var(--paper); }
.solid { background: var(--ink); color: #f6f1e8; }
.danger { background: var(--danger); color: #fff; }
button:disabled { opacity: 0.45; cursor: default; }
</style>
