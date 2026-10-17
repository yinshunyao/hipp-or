<template>
  <div v-if="open" class="mask" @click.self="close">
    <div class="sheet" role="dialog" :aria-labelledby="titleId">
      <h2 :id="titleId">{{ title }}</h2>
      <div class="qr-wrap">
        <img v-if="dataUrl" class="qr" :src="dataUrl" alt="支付二维码" />
        <p v-else class="hint">正在生成二维码…</p>
      </div>
      <p class="hint">{{ hint }}</p>
      <a
        v-if="isHttp"
        class="open-link"
        :href="payUrl"
        target="_blank"
        rel="noopener noreferrer"
      >打开支付页面</a>
      <button type="button" class="close" @click="close">关闭</button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '扫码支付' },
  hint: { type: String, default: '请扫码完成支付' },
  payUrl: { type: String, default: '' }
})
const emit = defineEmits(['close'])

const titleId = 'pay-qr-title'
const dataUrl = ref('')
const isHttp = computed(() => /^https?:\/\//i.test(props.payUrl || ''))

function close() {
  emit('close')
}

async function renderQr(text) {
  dataUrl.value = ''
  if (!text) return
  try {
    const QR = await import('qrcode')
    dataUrl.value = await QR.toDataURL(text, {
      width: 220,
      margin: 2,
      errorCorrectionLevel: 'M'
    })
  } catch {
    dataUrl.value = ''
  }
}

watch(
  () => [props.open, props.payUrl],
  ([open, url]) => {
    if (open && url) renderQr(url)
    else dataUrl.value = ''
  },
  { immediate: true }
)
</script>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  z-index: 90;
  background: rgba(12, 16, 20, 0.46);
  display: grid;
  place-items: center;
  padding: 24px;
}
.sheet {
  width: min(360px, 100%);
  background: var(--surface);
  color: var(--text);
  border-radius: 16px;
  padding: 22px;
  box-shadow: var(--shadow);
  text-align: center;
}
h2 {
  margin: 0 0 16px;
  font-family: var(--serif);
  font-size: 22px;
}
.qr-wrap {
  min-height: 220px;
  display: grid;
  place-items: center;
}
.qr {
  width: 220px;
  height: 220px;
  border-radius: 8px;
  background: #fff;
}
.hint {
  margin: 12px 0 0;
  color: var(--text-3);
  font-size: 14px;
}
.open-link {
  display: inline-block;
  margin-top: 10px;
  color: var(--teal);
  font-size: 14px;
}
.close {
  display: block;
  width: 100%;
  margin-top: 18px;
  border: 0;
  border-radius: 12px;
  padding: 12px;
  font-weight: 650;
  background: var(--paper-2);
  color: var(--text);
}
.close:hover {
  background: rgba(166, 124, 61, 0.16);
}
</style>
