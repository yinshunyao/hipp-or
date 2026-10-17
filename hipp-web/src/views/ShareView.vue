<template>
  <div class="share">
    <p v-if="missing" class="miss">这条分享不存在或已失效。</p>
    <ChatPane
      v-else
      bare
      :title="title"
      kicker="记录"
      :messages="messages"
      disabled
      show-human
      empty-hint="这条分享还没有内容。"
    />
    <AccountPanel :about="aboutOpen" @close-about="aboutOpen = false" />
  </div>
</template>

<script setup>
import { provide, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AccountPanel from '@/components/AccountPanel.vue'
import ChatPane from '@/components/ChatPane.vue'
import { getSharedChat } from '@/api/chat'

const route = useRoute()
const title = ref('分享')
const messages = ref([])
const missing = ref(false)
const aboutOpen = ref(false)
provide('openAbout', () => { aboutOpen.value = true })

async function load(token) {
  missing.value = false
  title.value = '分享'
  messages.value = []
  if (!token) {
    missing.value = true
    return
  }
  try {
    const res = await getSharedChat(token)
    const data = res.data || {}
    title.value = data.title || '分享'
    const list = Array.isArray(data.messages) ? data.messages : []
    messages.value = list.map((item) => ({
      role: item.role,
      content: item.content || '',
      attachments: Array.isArray(item.attachments) ? item.attachments : [],
      at: item.create_datetime || ''
    }))
  } catch (err) {
    missing.value = true
  }
}

watch(() => route.params.token, (token) => { load(token) }, { immediate: true })
</script>

<style scoped>
.share {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--paper);
}
.miss {
  margin: 20vh auto 0;
  color: var(--text-2);
}
</style>
