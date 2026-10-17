<template>
  <AppShell v-if="shell">
    <RouterView />
  </AppShell>
  <RouterView v-else />
  <ToastHost />
  <DialogHost />
</template>

<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import ToastHost from '@/components/ToastHost.vue'
import DialogHost from '@/components/DialogHost.vue'

const route = useRoute()
const shell = computed(() => !!route.meta.shell)
</script>
