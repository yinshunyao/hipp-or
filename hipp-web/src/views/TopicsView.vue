<template>
  <section class="topics">
    <header>
      <div>
        <p class="kicker">Archive</p>
        <h1>{{ auth.isStaff ? '客服接待' : '话题' }}</h1>
      </div>
      <input v-model="keyword" :placeholder="auth.isStaff ? '搜索用户或消息' : '搜索话题'" @input="schedule" />
    </header>
    <p v-if="loading" class="hint">加载中…</p>
    <p v-else-if="!items.length" class="hint">{{ auth.isStaff ? '暂无分配给你的会话' : '暂无归档话题' }}</p>
    <ul v-else>
      <li v-for="row in items" :key="row.session.id">
        <button class="row" type="button" @click="open(row)">
          <span class="avatar" :style="{ background: avatarBackground(row) }">
            <img v-if="avatarUrl(row)" :src="avatarUrl(row)" alt="" />
            <template v-else>{{ avatarText(row) }}</template>
          </span>
          <span class="meta">
            <span class="title">
              <strong>{{ displayName(row) }}</strong>
              <span class="tags">
                <em v-if="row.session.session_kind === 'human_support'">人工</em>
                <em v-if="statusLabel(row)" class="state">{{ statusLabel(row) }}</em>
                <em v-if="row.session.is_pinned" class="pin">置顶</em>
                <em v-if="row.session.session_kind !== 'human_support' && row.session.is_topic_closed" class="end">已结束</em>
              </span>
            </span>
            <span class="preview">{{ preview(row) }}</span>
          </span>
        </button>
        <button v-if="!auth.isStaff" class="more" type="button" @click="menu(row)">···</button>
      </li>
    </ul>
    <div v-if="sheet" class="mask" @click.self="sheet = null">
      <div class="menu">
        <button v-for="item in actions" :key="item.key" type="button" :class="{ danger: item.danger }" @click="run(item)">
          {{ item.label }}
        </button>
        <button type="button" class="cancel" @click="sheet = null">取消</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deleteChatSession, getChatInbox, getStaffChatInbox, patchChatSession } from '@/api/chat'
import { useAuthStore } from '@/stores/auth'
import { assetUrl } from '@/utils/asset'
import { askText, confirmDialog, toast } from '@/utils/toast'

const auth = useAuthStore()
const router = useRouter()
const keyword = ref('')
const items = ref([])
const loading = ref(false)
const sheet = ref(null)
const actions = ref([])
let timer = 0

function displayName(row) {
  const session = row.session || {}
  return session.display_title || session.title || (row.agent && row.agent.name) || '对话'
}
function preview(row) {
  const session = row.session || {}
  if (session.last_message_preview) return session.last_message_preview
  if (session.agent_status && session.agent_status !== 'active') return '仅可查看历史消息'
  return ' '
}
function statusLabel(row) {
  const status = row.session && row.session.agent_status
  if (status === 'offline') return '已下架'
  if (status === 'deleted') return '已删除'
  return ''
}
function avatarText(row) {
  const agent = row.agent || {}
  if (agent.icon_type === 'emoji' && agent.icon) return agent.icon
  return (agent.name || '智').trim().slice(0, 1)
}
function avatarUrl(row) {
  const agent = row.agent || {}
  return agent.icon_type === 'image' && agent.icon_url ? assetUrl(agent.icon_url) : ''
}
function avatarBackground(row) {
  const raw = String((row.agent && row.agent.icon_background) || '').trim()
  return raw || 'linear-gradient(145deg, #3d5368, #1c5f68)'
}
async function load() {
  loading.value = true
  try {
    const res = auth.isStaff ? await getStaffChatInbox(keyword.value.trim()) : await getChatInbox(keyword.value.trim())
    items.value = (res.data && res.data.items) || []
  } catch (err) {
    items.value = []
  } finally {
    loading.value = false
  }
}
function schedule() {
  window.clearTimeout(timer)
  timer = window.setTimeout(load, 280)
}
function open(row) {
  const id = row.session && row.session.id
  if (!id) {
    toast('会话参数缺失')
    return
  }
  router.push(`/chat/${id}`)
}
function menu(row) {
  const closed = !!(row.session && row.session.is_topic_closed)
  const pinLabel = row.session && row.session.is_pinned ? '取消置顶' : '置顶'
  actions.value = closed
    ? [
        { key: 'resume', label: '继续对话' },
        { key: 'pin', label: pinLabel },
        { key: 'rename', label: '修改标题' },
        { key: 'delete', label: '删除会话', danger: true }
      ]
    : [
        { key: 'pin', label: pinLabel },
        { key: 'rename', label: '修改标题' },
        { key: 'delete', label: '删除会话', danger: true }
      ]
  sheet.value = row
}
async function run(action) {
  const row = sheet.value
  sheet.value = null
  const id = row && row.session && row.session.id
  if (!id) return
  if (action.key === 'resume') {
    await patchChatSession(id, { resume_topic: true })
    router.push(`/chat/${id}`)
    return
  }
  if (action.key === 'pin') {
    await patchChatSession(id, { is_pinned: !row.session.is_pinned })
    await load()
    return
  }
  if (action.key === 'rename') {
    const title = await askText({ title: '修改标题', value: displayName(row), placeholder: '话题标题' })
    if (title) {
      await patchChatSession(id, { title })
      await load()
    }
    return
  }
  if (action.key === 'delete') {
    const ok = await confirmDialog({ title: '确认删除', message: '删除后不可恢复', confirmText: '删除', danger: true })
    if (ok) {
      await deleteChatSession(id)
      await load()
    }
  }
}
onMounted(load)
</script>

<style scoped>
.topics { max-width: 880px; margin: 0 auto; padding: 28px 22px 48px; }
header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-end; margin-bottom: 18px; }
.kicker { margin: 0; font-family: var(--display); letter-spacing: 0.16em; color: var(--brass); font-size: 12px; text-transform: uppercase; }
h1 { margin: 4px 0 0; font-family: var(--serif); font-size: 36px; }
input {
  width: min(280px, 46vw); border: 1px solid var(--line); background: var(--surface);
  border-radius: 999px; padding: 10px 14px; outline: none;
}
ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
li { display: flex; align-items: stretch; gap: 6px; }
.row {
  flex: 1; display: flex; gap: 12px; text-align: left; border: 1px solid var(--line);
  background: var(--surface); border-radius: 18px; padding: 14px; min-width: 0;
}
.row:hover { border-color: rgba(166, 124, 61, 0.45); }
.avatar {
  width: 46px; height: 46px; border-radius: 14px; flex: none; display: grid; place-items: center;
  overflow: hidden; color: var(--text);
}
.avatar img { width: 100%; height: 100%; object-fit: cover; }
.meta { min-width: 0; display: flex; flex-direction: column; }
.title { display: flex; gap: 8px; align-items: flex-start; }
strong {
  font-size: 16px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.tags { margin-left: auto; display: flex; gap: 4px; flex-wrap: wrap; justify-content: flex-end; }
em { font-style: normal; font-size: 12px; padding: 1px 6px; border-radius: 999px; background: rgba(28, 95, 104, 0.12); color: var(--teal); }
.pin { background: rgba(166, 124, 61, 0.16); color: var(--brass); }
.end, .state { background: var(--paper-2); color: var(--text-2); }
.preview { color: var(--text-3); font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.more { border: 0; background: transparent; color: var(--text-3); font-size: 20px; padding: 0 8px; }
.hint { color: var(--text-3); }
.mask { position: fixed; inset: 0; background: rgba(12,16,20,.42); display: grid; align-items: end; justify-items: center; padding: 18px; z-index: 30; }
.menu { width: min(420px, 100%); display: flex; flex-direction: column; gap: 8px; }
.menu button { border: 0; border-radius: 16px; background: var(--surface); padding: 14px; font-size: 16px; }
.danger { color: var(--danger); }
.cancel { color: var(--text-2); }
@media (max-width: 860px) {
  header { flex-direction: column; align-items: stretch; }
  input { width: 100%; }
}
</style>
