<template>
  <ChatPane
    :title="title"
    :kicker="scene === 'business' ? 'Business' : 'Requirement'"
    :messages="messages"
    :sending="loading"
    :disabled="readonly || !meta.id"
    :placeholder="placeholder"
    :notice="notice"
    :banner="banner"
    :show-human="showHuman"
    :session-id="meta.id"
    empty-hint="从输入框开始这次咨询。有来回的会话会留在左侧「最近」。"
    @send="onSend"
    @retry="retry"
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
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatPane from '@/components/ChatPane.vue'
import Icon from '@/components/Icon.vue'
import {
  createChatSession,
  createChatShare,
  deleteChatShare,
  patchChatSession,
  resolveSceneAgent,
  sessionFeePrecheck,
} from '@/api/chat'
import { useChatThread } from '@/composables/useChatThread'
import { useAuthStore } from '@/stores/auth'
import { useSessionNav } from '@/stores/sessions'
import { applyBizErrorAction } from '@/utils/bizErrors'
import { toast } from '@/utils/toast'
import { giveShareLink } from '@/utils/share'
import { smartTitle } from '@/utils/title'

/** 空草稿可写前预检；失败已 toast（http）并可能跳转钱包。 */
async function ensureCanStartTalk() {
  if (auth.isEntitlement) return true
  try {
    await sessionFeePrecheck()
    return true
  } catch (err) {
    applyBizErrorAction(err)
    return false
  }
}

const props = defineProps({
  scene: { type: String, required: true }
})
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const nav = useSessionNav()
const { messages, loading, meta, isReadonly, open, send, retry } = useChatThread()
const sceneAgentId = ref(null)
const guestNeedLogin = ref(false)
const guestCount = ref(0)
const guestLimit = ref(2)

const title = computed(() => (props.scene === 'business' ? '商业' : '需求'))
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
const showHuman = computed(() => (
  !auth.isEntitlement
  && meta.kind === 'dify'
  && meta.topicClosed
  && meta.agentStatus === 'active'
))
const readonly = computed(() => isReadonly() || (auth.isEntitlement && meta.topicClosed))
const placeholder = computed(() => {
  if (auth.isEntitlement && meta.topicClosed) return ''
  if (meta.topicClosed && meta.agentStatus === 'active') return '开启新话题…'
  return props.scene === 'business' ? '输入你的商业问题…' : '输入你的需求…'
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
const banner = computed(() => {
  if (guestNeedLogin.value) return '本场景免费体验次数已用完，请登录后继续。'
  if (guestCount.value > 0) {
    const name = props.scene === 'business' ? '商业' : '需求'
    return `游客体验：${name}场景已归档话题 ${guestCount.value}/${guestLimit.value} 次（以话题结束归档为准）。`
  }
  return ''
})

function hasTalk() {
  return messages.value.some((item) => item.role === 'user' || (item.role === 'assistant' && String(item.content || '').trim()))
}
function listTitle() {
  const server = String(meta.title || '').trim()
  const agent = String(meta.agentName || '').trim()
  if (server && agent && server !== agent) return server
  if (server && !agent && server !== '对话' && server !== '需求' && server !== '商业') return server
  const first = messages.value.find((item) => item.role === 'user' && String(item.content || '').trim())
  if (first) return smartTitle(first.content)
  return server || '新对话'
}
function noteCurrent() {
  if (!meta.id || !hasTalk()) {
    nav.setLive(props.scene, null)
    return
  }
  nav.setLive(props.scene, { id: meta.id, title: listTitle() })
}
async function startNew() {
  if (!sceneAgentId.value || loading.value) return
  const sameAgent = Number(meta.agentId) === Number(sceneAgentId.value)
  if (sameAgent && meta.id && !hasTalk()) {
    if (!(await ensureCanStartTalk())) return
    messages.value = []
    noteCurrent()
    return
  }
  try {
    const created = await createChatSession(sceneAgentId.value)
    const id = created.data && created.data.id
    if (!id) {
      toast('新建会话失败')
      return
    }
    await open(id)
    noteCurrent()
    await nav.refresh()
  } catch (err) {
    applyBizErrorAction(err)
  }
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
async function boot() {
  try {
    const res = await resolveSceneAgent(props.scene)
    const data = res.data || {}
    guestNeedLogin.value = !!data.guest_need_login
    guestCount.value = Number(data.guest_scene_archived_count) || 0
    guestLimit.value = Number(data.guest_scene_trial_limit) || 2
    const agent = data.agent
    if (!agent || !agent.id) {
      toast('当前场景暂不可用')
      return
    }
    sceneAgentId.value = agent.id
    if (data.guest_need_login) return
    if (route.query.fresh === '1') {
      await startNew()
      const query = { ...route.query }
      delete query.fresh
      router.replace({ name: route.name, query })
      return
    }
    if (data.session && data.session.id) {
      await open(data.session.id)
      noteCurrent()
      // 复用未发言空草稿：先预检余额，避免写完再 46005
      if (!hasTalk() && !(await ensureCanStartTalk())) {
        messages.value = []
        meta.id = null
        nav.setLive(props.scene, null)
      }
      return
    }
    const created = await createChatSession(agent.id)
    if (created.data && created.data.id) {
      await open(created.data.id)
      noteCurrent()
    }
  } catch (err) {
    applyBizErrorAction(err)
  }
}
async function onSend(payload) {
  const text = typeof payload === 'string' ? payload : (payload && payload.text) || ''
  const files = typeof payload === 'string' ? null : (payload && payload.files) || null
  await send(text, {
    files,
    agentId: sceneAgentId.value,
    onRenewed: async () => {
      await nav.refresh()
      noteCurrent()
    },
    onTopicClosed: async () => { await nav.refresh() }
  })
  noteCurrent()
  await nav.refresh()
}
watch(() => [meta.id, meta.title, messages.value.length], noteCurrent)
watch(() => props.scene, () => { boot() }, { immediate: true })
watch(() => nav.newTick, () => { startNew() })
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
