<template>
  <ChatPane
    :title="meta.title"
    :kicker="meta.kind === 'human_support' ? '人工' : '话题'"
    :messages="messages"
    :sending="loading"
    :disabled="readonly"
    :placeholder="placeholder"
    :notice="notice"
    :show-human="showHuman"
    :human="meta.kind === 'human_support'"
    :staff="meta.viewer === 'assigned_staff'"
    :session-id="meta.id"
    :allow-attach="meta.kind !== 'human_support'"
    @send="onSend"
    @retry="retry"
    @source="openSource"
  >
    <template #extra>
      <div class="actions">
        <button
          v-if="canShare"
          class="file iconly"
          type="button"
          :aria-label="meta.shared ? '复制链接' : '分享'"
          :data-tip="meta.shared ? '复制链接' : '分享'"
          @click="shareSession"
        >
          <Icon :name="meta.shared ? 'link' : 'share'" />
        </button>
        <button
          v-if="canShare && meta.shared"
          class="file iconly stop"
          type="button"
          aria-label="停止分享"
          data-tip="停止分享"
          @click="stopShare"
        >
          <Icon name="unlink" />
        </button>
        <button v-if="canArchive" class="file" type="button" @click="fileSession">
          <Icon name="box" />
          归档
        </button>
      </div>
    </template>
  </ChatPane>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatPane from '@/components/ChatPane.vue'
import Icon from '@/components/Icon.vue'
import { createChatShare, deleteChatShare, patchChatSession } from '@/api/chat'
import { toast } from '@/utils/toast'
import { giveShareLink } from '@/utils/share'
import { useChatThread } from '@/composables/useChatThread'
import { useAuthStore } from '@/stores/auth'
import { useSessionNav } from '@/stores/sessions'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const nav = useSessionNav()
const { messages, loading, meta, isReadonly, open, send, retry } = useChatThread()

const canArchive = computed(() => (
  !auth.isEntitlement
  && meta.kind === 'dify'
  && meta.viewer !== 'assigned_staff'
  && !meta.archived
))
const canShare = computed(() => (
  !auth.isEntitlement
  && meta.kind === 'dify'
  && meta.viewer !== 'assigned_staff'
  && meta.topicClosed
))
const readonly = computed(() => isReadonly() || (auth.isEntitlement && meta.topicClosed))
const showHuman = computed(() => (
  !auth.isEntitlement
  && meta.kind === 'dify'
  && meta.topicClosed
  && meta.agentStatus === 'active'
))
const placeholder = computed(() => {
  if (auth.isEntitlement && meta.topicClosed) return ''
  if (meta.viewer === 'assigned_staff') return '输入回复…'
  if (meta.topicClosed && meta.agentStatus === 'active') return '开启新话题…'
  return '输入你的问题…'
})
const notice = computed(() => {
  if (auth.isEntitlement && meta.topicClosed) {
    return '本次分析已完成。可将短链分享给他人只读查看。'
  }
  if (meta.topicClosed && meta.agentStatus === 'active') return '本话题已结束。继续输入并发送，将开启新的话题。'
  if (meta.agentStatus === 'deleted') return '智能体已删除，仅支持查看历史消息'
  if (meta.agentStatus === 'offline') return '智能体已下架，暂不支持继续对话'
  return ''
})

async function onSend(payload) {
  const text = typeof payload === 'string' ? payload : (payload && payload.text) || ''
  const files = typeof payload === 'string' ? null : (payload && payload.files) || null
  await send(text, {
    files,
    onRenewed: async (newId) => {
      await nav.refresh()
      const nid = Number(newId)
      if (nid && Number(route.params.id) !== nid) {
        await router.replace(`/chat/${nid}`)
      }
    },
    onTopicClosed: async () => { await nav.refresh() }
  })
  await nav.refresh()
}
async function shareSession() {
  if (!meta.id || !canShare.value) return
  try {
    const res = await createChatShare(meta.id)
    const token = res.data && res.data.share_token
    if (!token) return
    await giveShareLink(token)
    if (!meta.shared) {
      meta.shared = true
      await nav.refresh()
    }
  } catch (err) { /* 接口已提示 */ }
}
async function stopShare() {
  if (!meta.id || !meta.shared) return
  try {
    await deleteChatShare(meta.id)
    meta.shared = false
    toast('已停止分享')
    await nav.refresh()
  } catch (err) { /* 接口已提示 */ }
}
async function fileSession() {
  if (!meta.id || meta.archived) return
  try {
    await patchChatSession(meta.id, { is_archived: true })
    meta.archived = true
    await nav.refresh()
  } catch (err) { /* 保持未归档 */ }
}
function openSource() {
  if (meta.viewer !== 'owner' || !meta.sourceArchiveId) return
  router.push(`/chat/${meta.sourceArchiveId}`)
}
watch(() => route.params.id, (id) => {
  if (!id) return
  const nid = Number(id)
  if (nid && nid === Number(meta.id)) return
  open(nid)
}, { immediate: true })
</script>

<style scoped>
.actions { display: flex; align-items: center; gap: 8px; flex: none; }
.file {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: var(--paper-2);
  color: var(--text-2);
  border-radius: 12px;
  padding: 7px 12px;
  flex: none;
}
.file:hover { color: var(--text); background: var(--surface); }
.iconly {
  position: relative;
  width: 36px;
  height: 36px;
  padding: 0;
  justify-content: center;
  color: var(--brass);
}
.stop { color: var(--text-3); }
.iconly::after {
  content: attr(data-tip);
  position: absolute;
  left: 50%;
  top: calc(100% + 6px);
  transform: translateX(-50%);
  padding: 3px 7px;
  border-radius: 6px;
  background: #1a140c;
  color: #f4efe6;
  font-size: 12px;
  line-height: 1.3;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  z-index: 4;
}
.iconly:hover::after, .iconly:focus-visible::after { opacity: 1; }
</style>
