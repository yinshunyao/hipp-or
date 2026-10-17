<template>
  <article class="legal">
    <RouterLink to="/login">返回登录</RouterLink>
    <h1>{{ doc.title }}</h1>
    <p>{{ doc.body }}</p>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { legalDoc } from '@/data/legal'

const route = useRoute()
const doc = computed(() => legalDoc(route.params.kind))
</script>

<style scoped>
.legal { max-width: 760px; margin: 0 auto; padding: 48px 20px 80px; }
a { color: var(--teal); }
h1 { font-family: var(--serif); }
p { white-space: pre-wrap; color: var(--text-2); line-height: 1.8; }
</style>
