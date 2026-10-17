<template>
  <span class="seal" :class="size">
    <img v-if="photo" :src="photo" alt="" @error="broken = true" />
    <span v-else class="glyph">{{ glyph }}</span>
  </span>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, default: '' },
  name: { type: String, default: '' },
  size: { type: String, default: 'sm' }
})

const broken = ref(false)
watch(() => props.src, () => { broken.value = false })

const photo = computed(() => {
  const value = String(props.src || '').trim()
  if (!value || broken.value) return ''
  if (value.includes('1674820804e81e7631')) return ''
  return value
})
const glyph = computed(() => (String(props.name || '我').trim() || '我').slice(0, 1))
</script>

<style scoped>
.seal {
  display: grid;
  place-items: center;
  border-radius: 50%;
  overflow: hidden;
  flex: none;
  color: #f6f1e8;
  background:
    radial-gradient(circle at 32% 24%, #42586c 0%, #1b2834 52%, #101820 100%);
  box-shadow:
    inset 0 0 0 1px rgba(230, 201, 138, 0.9),
    inset 0 0 0 3.5px #121a22,
    inset 0 0 0 4.5px rgba(198, 161, 90, 0.55);
  font-family: var(--serif);
  font-weight: 650;
  line-height: 1;
}
.sm { width: 38px; height: 38px; font-size: 16px; }
.lg { width: 96px; height: 96px; font-size: 36px; }
.glyph { transform: translateY(-0.04em); }
.seal img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
</style>
