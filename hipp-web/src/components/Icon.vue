<template>
  <svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <template v-if="name === 'req'">
      <path d="M8 4.2h5.2L18 9v10.4a1.2 1.2 0 0 1-1.2 1.2H8.2A1.2 1.2 0 0 1 7 19.4V5.4A1.2 1.2 0 0 1 8.2 4.2z" />
      <path d="M13 4.4V9h4.6" />
      <path d="M9.2 12.4h5.6M9.2 15.5h3.6" />
    </template>
    <template v-else-if="name === 'biz'">
      <path d="M5 19.2h14" />
      <path d="M7.2 19.2V12.2" />
      <path d="M12 19.2V7.4" />
      <path d="M16.8 19.2V10.2" />
    </template>
    <template v-else-if="name === 'plus'">
      <path d="M12 6.2v11.6M6.2 12h11.6" />
    </template>
    <template v-else-if="name === 'box'">
      <path d="M4.2 8.2h15.6" />
      <path d="M5.4 8.2l1 11.2h11.2l1-11.2" />
      <path d="M9.4 12h5.2" />
    </template>
    <template v-else-if="name === 'chev'">
      <path d="M9 6.4 15 12l-6 5.6" />
    </template>
    <template v-else-if="name === 'send'">
      <path d="M12 18.4V6.2" />
      <path d="M7.2 10.6 12 5.6l4.8 5" />
    </template>
    <template v-else-if="name === 'mail'">
      <path d="M4.4 7.2h15.2v10.2H4.4z" />
      <path d="m4.8 7.8 7.2 5.2 7.2-5.2" />
    </template>
    <template v-else-if="name === 'user'">
      <circle cx="12" cy="9" r="3" />
      <path d="M6.4 18.6c.9-2.7 2.9-4 5.6-4s4.7 1.3 5.6 4" />
    </template>
    <template v-else-if="name === 'edit'">
      <path d="M4.6 16.6 5 13.4 14.2 4.2l3.2 3.2-9.2 9.2z" />
      <path d="m12.8 5.6 3.2 3.2" />
    </template>
    <template v-else-if="name === 'lock'">
      <rect x="7.2" y="10.6" width="9.6" height="8" rx="1.2" />
      <path d="M9.2 10.6V8.4a2.8 2.8 0 0 1 5.6 0v2.2" />
    </template>
    <template v-else-if="name === 'moon'">
      <path d="M15.6 14.6A5.8 5.8 0 0 1 9.2 6.4 6.1 6.1 0 1 0 15.6 14.6z" />
    </template>
    <template v-else-if="name === 'info'">
      <circle cx="12" cy="12" r="8" />
      <path d="M12 11.2V16" />
      <path d="M12 8.2h.01" />
    </template>
    <template v-else-if="name === 'out'">
      <path d="M10 7.2H6.8A1.4 1.4 0 0 0 5.4 8.6v6.8a1.4 1.4 0 0 0 1.4 1.4H10" />
      <path d="M13 12h6" />
      <path d="m16.4 8.8 3.2 3.2-3.2 3.2" />
    </template>
    <template v-else-if="name === 'eye'">
      <path d="M3 12s3.4-5.2 9-5.2S21 12 21 12s-3.4 5.2-9 5.2S3 12 3 12z" />
      <circle cx="12" cy="12" r="2.1" />
    </template>
    <template v-else-if="name === 'eyeOff'">
      <path d="M4 5.2 19.2 19" />
      <path d="M9.2 9.4A3 3 0 0 0 12 15a3 3 0 0 0 2.2-.9" />
      <path d="M6.2 7.6C4.4 8.8 3 12 3 12s3.4 5.2 9 5.2c1.3 0 2.5-.3 3.5-.8" />
      <path d="M10.2 6.9c.6-.1 1.2-.1 1.8-.1 5.6 0 9 5.2 9 5.2s-.7 1.1-1.9 2.2" />
    </template>
    <template v-else-if="name === 'camera'">
      <path d="M4.2 8.4h3.1l1.2-1.8h7l1.2 1.8h3.1v9.2H4.2z" />
      <circle cx="12" cy="12.6" r="2.3" />
    </template>
    <template v-else-if="name === 'share'">
      <path d="M14.2 5.6h4.2v4.2" />
      <path d="M18.2 5.8 10.2 13.8" />
      <path d="M15.6 12.8v4.6a1.4 1.4 0 0 1-1.4 1.4H6.6a1.4 1.4 0 0 1-1.4-1.4V9.6a1.4 1.4 0 0 1 1.4-1.4h4.6" />
    </template>
    <template v-else-if="name === 'link'">
      <path d="M10.2 13.2a3.2 3.2 0 0 0 4.8.4l1.9-1.9a3.2 3.2 0 0 0-4.5-4.5l-1.1 1.1" />
      <path d="M13.8 10.8a3.2 3.2 0 0 0-4.8-.4l-1.9 1.9a3.2 3.2 0 0 0 4.5 4.5l1.1-1.1" />
    </template>
    <template v-else-if="name === 'unlink'">
      <circle cx="12" cy="12" r="6.4" />
      <path d="M7.6 7.6 16.4 16.4" />
    </template>
    <template v-else-if="name === 'wallet'">
      <rect x="4.2" y="7.2" width="15.6" height="11.2" rx="1.6" />
      <path d="M4.8 10.2h14.4" />
      <path d="M15.2 14.2h2.4" />
    </template>
    <template v-else-if="name === 'attach'">
      <path d="M15.2 7.4 9.4 13.2a2.6 2.6 0 0 0 3.7 3.7l6.2-6.2a4.2 4.2 0 0 0-5.9-5.9l-6.6 6.6a5.6 5.6 0 0 0 7.9 7.9l5.4-5.4" />
    </template>
    <template v-else-if="name === 'mic'">
      <rect x="9.4" y="4.4" width="5.2" height="9.2" rx="2.6" />
      <path d="M7.2 12.2a4.8 4.8 0 0 0 9.6 0" />
      <path d="M12 17v2.6" />
    </template>
  </svg>
</template>

<script setup>
defineProps({
  name: { type: String, required: true }
})
</script>

<style scoped>
.ico {
  width: 18px;
  height: 18px;
  display: block;
  flex: none;
}
</style>
