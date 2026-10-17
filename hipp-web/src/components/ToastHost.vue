<template>
  <div class="toasts" aria-live="polite">
    <div v-for="item in items" :key="item.id" class="toast" :data-type="item.type">{{ item.message }}</div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const items = ref([])
let seq = 0

function push(event) {
  const id = ++seq
  items.value.push({ id, message: event.detail.message, type: event.detail.type || 'info' })
  setTimeout(() => {
    items.value = items.value.filter((item) => item.id !== id)
  }, 2800)
}

onMounted(() => window.addEventListener('hipp-toast', push))
onBeforeUnmount(() => window.removeEventListener('hipp-toast', push))
</script>

<style scoped>
.toasts {
  position: fixed;
  left: 50%;
  bottom: 28px;
  transform: translateX(-50%);
  z-index: 80;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}
.toast {
  min-width: 180px;
  max-width: min(420px, 86vw);
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--ink);
  color: #f4efe6;
  text-align: center;
  box-shadow: var(--shadow);
  font-size: 14px;
}
</style>
