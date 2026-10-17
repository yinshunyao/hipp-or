<template>
  <div class="access">
    <p v-if="busy" class="msg">正在打开分析…</p>
    <p v-else-if="error" class="msg err">{{ error }}</p>
    <template v-else>
      <ChatPane
        :bare="mode === 'readonly'"
        :title="paneTitle"
        :kicker="mode === 'readonly' ? '记录' : 'Requirement'"
        :messages="displayMessages"
        :sending="loading"
        :disabled="mode === 'readonly' || !meta.id || meta.topicClosed"
        :placeholder="mode === 'readonly' ? '' : '输入你的需求…'"
        :notice="notice"
        :session-id="meta.id"
        :empty-hint="mode === 'readonly' ? '这条分析还没有内容。' : '从输入框开始这次咨询。完成后可将本链接发给他人只读查看。'"
        @send="onSend"
        @retry="retry"
      />
      <AccountPanel :about="aboutOpen" @close-about="aboutOpen = false" />
    </template>
  </div>
</template>

<script setup>
import { computed, provide, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AccountPanel from '@/components/AccountPanel.vue'
import ChatPane from '@/components/ChatPane.vue'
import { previewAccess, redeemAccess } from '@/api/commerce'
import { createChatSession, resolveSceneAgent } from '@/api/chat'
import { useChatThread } from '@/composables/useChatThread'
import { useAuthStore } from '@/stores/auth'
import { toast } from '@/utils/toast'

const route = useRoute()
const auth = useAuthStore()
const busy = ref(true)
const error = ref('')
const mode = ref('chat')
const aboutOpen = ref(false)
const readonlyTitle = ref('需求分析')
const readonlyMessages = ref([])
provide('openAbout', () => { aboutOpen.value = true })

const { messages, loading, meta, open, send, retry } = useChatThread()

const paneTitle = computed(() => {
  if (mode.value === 'readonly') return readonlyTitle.value || '需求分析'
  return '需求'
})
const displayMessages = computed(() => (
  mode.value === 'readonly' ? readonlyMessages.value : messages.value
))
const notice = computed(() => {
  if (mode.value === 'readonly') return '本次分析已完成。可将本链接分享给他人只读查看。'
  if (meta.topicClosed) return '本次分析已完成。可将本链接分享给他人只读查看。'
  return ''
})

function mapMessages(list) {
  return (Array.isArray(list) ? list : []).map((item) => ({
    role: item.role,
    content: item.content || '',
    attachments: Array.isArray(item.attachments) ? item.attachments : [],
    at: item.create_datetime || item.at || ''
  }))
}

function showReadonly(data) {
  mode.value = 'readonly'
  readonlyTitle.value = data.title || '需求分析'
  readonlyMessages.value = mapMessages(data.messages)
  busy.value = false
  error.value = ''
}

async function bootChat(boundSessionId) {
  mode.value = 'chat'
  const res = await resolveSceneAgent('requirement')
  const data = res.data || {}
  const agent = data.agent
  if (!agent || !agent.id) {
    throw new Error('当前场景暂不可用')
  }
  const sid = boundSessionId || (data.session && data.session.id) || null
  if (sid) {
    await open(sid)
    busy.value = false
    return
  }
  const created = await createChatSession(agent.id)
  const id = created.data && created.data.id
  if (!id) throw new Error('新建会话失败')
  await open(id)
  busy.value = false
}

async function run(token) {
  busy.value = true
  error.value = ''
  mode.value = 'chat'
  readonlyMessages.value = []
  if (!token) {
    busy.value = false
    error.value = '链接无效'
    return
  }
  try {
    const preview = await previewAccess(token)
    const pdata = preview.data || {}
    if (pdata.mode === 'readonly' || pdata.status === 'used') {
      showReadonly(pdata)
      return
    }
    const res = await redeemAccess(token)
    const data = res.data || {}
    auth.applyToken(data)
    try {
      await auth.fetchInfo()
    } catch {
      auth.name = '次卡用户'
      auth.nickname = '次卡用户'
      auth.userType = data.user_type || 'entitlement'
      auth.ready = true
    }
    await bootChat(data.bound_session_id || pdata.bound_session_id)
  } catch (err) {
    error.value = err?.message || '无法打开分析链接'
    busy.value = false
  }
}

async function onSend(payload) {
  const text = typeof payload === 'string' ? payload : (payload && payload.text) || ''
  const files = typeof payload === 'string' ? null : (payload && payload.files) || null
  const closed = await send(text, {
    files,
    agentId: meta.agentId,
    onTopicClosed: async () => {
      toast('本次分析已完成，可将本链接分享给他人查看')
      const token = route.params.token
      if (!token) {
        mode.value = 'readonly'
        readonlyTitle.value = meta.title || '需求分析'
        readonlyMessages.value = messages.value.slice()
        return
      }
      try {
        const preview = await previewAccess(token)
        showReadonly(preview.data || {})
      } catch {
        mode.value = 'readonly'
        readonlyTitle.value = meta.title || '需求分析'
        readonlyMessages.value = messages.value.slice()
      }
    }
  })
  if (closed && mode.value === 'chat' && meta.topicClosed) {
    // onTopicClosed 已处理；兜底
  }
}

watch(() => route.params.token, (token) => { run(token) }, { immediate: true })
</script>

<style scoped>
.access {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--paper);
}
.msg {
  margin: 20vh auto 0;
  font-size: 1.05rem;
  letter-spacing: 0.02em;
  color: var(--text);
  font-family: var(--serif);
}
.err {
  color: #8a2f2f;
  max-width: 22rem;
  text-align: center;
  line-height: 1.5;
  padding: 0 1.5rem;
}
</style>
