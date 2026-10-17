import { onScopeDispose, reactive, ref } from 'vue'
import { createChatSession, getChatMessages, getChatSession, sendChatMessage } from '@/api/chat'
import { sendChatMessageStream } from '@/api/stream'
import { BizCode, applyBizErrorAction, resolveBizError } from '@/utils/bizErrors'
import { toast } from '@/utils/toast'

function localId() {
  return `c-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export function useChatThread() {
  const messages = ref([])
  const loading = ref(false)
  const meta = reactive({
    id: null,
    title: '对话',
    agentId: null,
    agentStatus: 'active',
    topicClosed: false,
    archived: false,
    shared: false,
    kind: 'dify',
    viewer: 'owner',
    sourceArchiveId: null,
    agentName: ''
  })
  let revealHandle = 0
  let alive = true
  onScopeDispose(() => {
    alive = false
    if (revealHandle) cancelAnimationFrame(revealHandle)
  })

  function settle(row) {
    if (!row) return
    const target = row.pending == null ? null : String(row.pending)
    const shown = String(row.content || '')
    const behind = target != null && shown.length < target.length
    row.live = !!row.streaming || behind
    if (!row.streaming && !behind) row.pending = undefined
  }

  function armReveal() {
    if (revealHandle || !alive) return
    const step = () => {
      revealHandle = 0
      if (!alive) return
      let more = false
      messages.value.forEach((row) => {
        if (!row || row.role !== 'assistant' || row.pending == null) return
        const target = String(row.pending)
        const shown = String(row.content || '')
        if (shown.length < target.length) {
          const gap = target.length - shown.length
          const count = gap > 240 ? 24 : gap > 80 ? 8 : gap > 16 ? 3 : gap
          row.content = target.slice(0, shown.length + count)
          more = true
        }
        settle(row)
      })
      if (more) revealHandle = requestAnimationFrame(step)
    }
    revealHandle = requestAnimationFrame(step)
  }

  function acceptAssistant(index, full, streaming) {
    const row = messages.value[index]
    if (!row) return
    row.pending = String(full || '')
    row.streaming = streaming
    if (row.content == null) row.content = ''
    settle(row)
    armReveal()
  }

  function finishAssistant(index) {
    const row = messages.value[index]
    if (!row) return
    row.streaming = false
    settle(row)
    armReveal()
  }

  function applyMeta(d = {}) {
    meta.title = d.display_title || d.title || '对话'
    const aid = d.agent && d.agent.id != null ? d.agent.id : d.agent_id
    meta.agentId = aid != null ? Number(aid) : null
    meta.agentStatus = d.agent_status || 'active'
    meta.topicClosed = d.is_topic_closed === true
    meta.archived = d.is_archived === true
    meta.shared = d.is_shared === true
    meta.kind = d.session_kind || 'dify'
    meta.viewer = d.viewer_context || 'owner'
    meta.sourceArchiveId = d.source_archive_session_id != null ? d.source_archive_session_id : null
    meta.agentName = String((d.agent && d.agent.name) || '').trim()
  }

  function isReadonly() {
    if (meta.kind === 'human_support') return false
    return !!(meta.agentStatus && meta.agentStatus !== 'active')
  }

  async function refreshMeta() {
    if (!meta.id) return
    try {
      applyMeta((await getChatSession(meta.id)).data || {})
    } catch (err) { /* 保持当前标题 */ }
  }

  async function loadMessages() {
    if (!meta.id) return
    const res = await getChatMessages(meta.id, 1, 100)
    const list = Array.isArray(res.data) ? res.data : []
    messages.value = list.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content || '',
      attachments: Array.isArray(m.attachments) ? m.attachments : [],
      at: m.create_datetime || ''
    }))
  }

  async function open(sessionId) {
    meta.id = Number(sessionId)
    try {
      applyMeta((await getChatSession(meta.id)).data || {})
    } catch (err) {
      meta.title = '对话'
    }
    try {
      await loadMessages()
    } catch (err) {
      messages.value = []
    }
  }

  async function ensureWritable(agentId) {
    if (meta.kind === 'human_support') return true
    if (!meta.topicClosed) return true
    if (meta.agentStatus !== 'active') return false
    const aid = agentId || meta.agentId
    if (!aid) return false
    try {
      const created = await createChatSession(aid)
      const nid = created.data && created.data.id
      if (!nid) return false
      await open(nid)
      return true
    } catch (err) {
      applyBizErrorAction(err)
      return false
    }
  }

  async function runDify(query, retryIndex, files) {
    const fileList = Array.isArray(files) && files.length ? files : null
    let userIndex
    let aiIndex
    if (typeof retryIndex === 'number') {
      userIndex = retryIndex
      const current = messages.value[userIndex]
      if (!current || current.role !== 'user') return false
      current.sendStatus = 'sending'
      aiIndex = userIndex + 1
      const next = messages.value[aiIndex]
      if (next && next.role === 'assistant') {
        next.content = ''
        next.pending = undefined
        next.streaming = true
        next.live = true
      } else messages.value.splice(aiIndex, 0, { role: 'assistant', content: '', streaming: true, live: true, localId: localId() })
    } else {
      userIndex = messages.value.length
      const sentAt = new Date().toISOString()
      const display = query || (fileList ? '请结合附件内容回答' : '')
      messages.value.push({
        role: 'user',
        content: display,
        attachments: fileList || [],
        sendStatus: 'sending',
        localId: localId(),
        at: sentAt
      })
      aiIndex = messages.value.length
      messages.value.push({ role: 'assistant', content: '', streaming: true, live: true, localId: localId(), at: sentAt })
    }
    const retryFiles = fileList || (messages.value[userIndex] && messages.value[userIndex].attachments) || null
    const markSent = () => {
      const row = messages.value[userIndex]
      if (row && row.sendStatus === 'sending') row.sendStatus = 'sent'
    }
    // 助手「正在回复」与用户气泡同帧出现；此时发送已进入通道，勿再叠「发送中」
    markSent()
    const fallback = async () => {
      const res = await sendChatMessage(meta.id, query, retryFiles)
      const payload = (res && res.data) || {}
      acceptAssistant(aiIndex, payload.answer || '（无内容）', true)
      finishAssistant(aiIndex)
      markSent()
      if (payload.topic_closed) {
        toast('话题已结束')
        await refreshMeta()
        return true
      }
      return false
    }
    try {
      let closed = false
      try {
        const streamed = await sendChatMessageStream(meta.id, query, (full) => {
          if (String(full || '').trim()) markSent()
          acceptAssistant(aiIndex, full, true)
        }, retryFiles, markSent)
        const shown = messages.value[aiIndex]
        const received = shown ? String(shown.pending != null ? shown.pending : shown.content || '') : ''
        if (shown && !received.trim()) acceptAssistant(aiIndex, '（无内容）', true)
        finishAssistant(aiIndex)
        markSent()
        await refreshMeta()
        if (streamed && streamed.topicClosed) {
          toast('话题已结束')
          await refreshMeta()
          closed = true
        }
      } catch (err) {
        const shown = messages.value[aiIndex]
        const received = shown ? String(shown.pending != null ? shown.pending : shown.content || '').trim() : ''
        if (received) {
          finishAssistant(aiIndex)
          markSent()
        } else if (err && err.transient) closed = await fallback()
        else throw err
      }
      if (messages.value[userIndex]) messages.value[userIndex].sendStatus = 'sent'
      return closed
    } catch (err) {
      const resolved = resolveBizError(err)
      if (resolved.code === BizCode.AGENT_UNAVAILABLE) {
        const msg = resolved.message || ''
        meta.agentStatus = msg.includes('删除') ? 'deleted' : 'offline'
      }
      if (messages.value[userIndex]) messages.value[userIndex].sendStatus = 'failed'
      if (messages.value[aiIndex]) {
        const failRow = messages.value[aiIndex]
        failRow.content = resolved.message
        failRow.pending = undefined
        failRow.streaming = false
        failRow.live = false
      }
      applyBizErrorAction(err)
      return false
    }
  }

  async function runHuman(query, retryIndex) {
    const staff = meta.viewer === 'assigned_staff'
    const role = staff ? 'assistant' : 'user'
    let idx
    if (typeof retryIndex === 'number') {
      idx = retryIndex
      const current = messages.value[idx]
      if (!current || current.role !== role) return
      current.sendStatus = 'sending'
    } else {
      idx = messages.value.length
      messages.value.push({ role, content: query, sendStatus: 'sending', localId: localId(), at: new Date().toISOString() })
    }
    try {
      await sendChatMessage(meta.id, query)
      if (messages.value[idx]) messages.value[idx].sendStatus = 'sent'
    } catch (err) {
      if (messages.value[idx]) messages.value[idx].sendStatus = 'failed'
    }
  }

  async function send(text, { agentId, onRenewed, onTopicClosed, files } = {}) {
    const query = String(text || '').trim()
    const fileList = Array.isArray(files) && files.length ? files : null
    if ((!query && !fileList) || loading.value || isReadonly() || !meta.id) return false
    loading.value = true
    try {
      if (meta.topicClosed && meta.agentStatus === 'active' && meta.kind !== 'human_support') {
        const ok = await ensureWritable(agentId)
        if (!ok) return false
        if (onRenewed) await onRenewed(meta.id)
      }
      if (meta.kind === 'human_support') {
        if (fileList) {
          toast('人工客服暂不支持附件')
          return false
        }
        await runHuman(query)
        return false
      }
      const closed = await runDify(query, undefined, fileList)
      if (closed && onTopicClosed) await onTopicClosed()
      return closed
    } finally {
      loading.value = false
    }
  }

  async function retry(index) {
    const current = messages.value[index]
    if (!current || loading.value || current.sendStatus !== 'failed') return
    loading.value = true
    try {
      if (meta.kind === 'human_support') await runHuman(current.content, index)
      else await runDify(current.content, index, current.attachments)
    } finally {
      loading.value = false
    }
  }

  return { messages, loading, meta, isReadonly, open, send, retry, refreshMeta }
}
