<template>
  <view :class="themeClass" class="page-with-nav">
    <uni-nav-bar
      :title="sessionTitle || '对话'"
      fixed
      status-bar
      :border="false"
      :background-color="'var(--t-nav-bg)'"
      :color="'var(--t-nav-text)'"
      left-icon="left"
      @clickLeft="navBack"
    />
    <view class="chat-container page-with-nav__body">
    <scroll-view :scroll-top="scrollTop" scroll-y class="msg-list" scroll-with-animation>
      <view v-for="(item, index) in messages" :key="item.id || item.localId || 'idx-' + index" class="msg-item">
        <view
          v-if="item.role === 'system' && sessionKind === 'human_support'"
          class="archive-tip"
          @click="openSourceArchiveSession"
        >
          <text class="archive-tip-label">📁</text>
          <view class="archive-tip-title">{{ archiveTopicTitleFromSystem(item.content) }}</view>
        </view>
        <view v-else-if="item.role === 'system'" class="context-hint">
          <text class="context-hint-text" selectable>{{ item.content }}</text>
        </view>
        <template v-else-if="viewerContext === 'assigned_staff'">
          <view v-if="item.role === 'user'" class="bubble staff-peer">
            <text class="bubble-content" selectable>{{ item.content }}</text>
          </view>
          <view v-else class="bubble user">
            <text class="bubble-content" selectable>{{ item.content }}</text>
          </view>
          <view v-if="item.role === 'assistant' && (item.sendStatus === 'sending' || item.sendStatus === 'failed')" class="msg-meta msg-meta--staff">
            <text v-if="item.sendStatus === 'sending'" class="msg-meta-text">发送中…</text>
            <text v-else class="retry-link" @click="retrySend(index)">重试</text>
          </view>
        </template>
        <template v-else>
          <view :class="['bubble', item.role === 'user' ? 'user' : 'ai']">
            <text v-if="item.role === 'user'" class="bubble-content" selectable>{{ item.content }}</text>
            <rich-text v-else class="bubble-content bubble-content--rich" :nodes="renderAssistantMarkdown(item.content)"></rich-text>
          </view>
          <view v-if="item.role === 'user' && (item.sendStatus === 'sending' || item.sendStatus === 'failed')" class="msg-meta">
            <text v-if="item.sendStatus === 'sending'" class="msg-meta-text">发送中…</text>
            <text v-else class="retry-link" @click="retrySend(index)">重试</text>
          </view>
        </template>
      </view>
    </scroll-view>
    <view v-if="showNoticeBar" class="topic-end-stack">
      <view class="readonly-notice-slot">
        <!-- #ifdef MP-WEIXIN -->
        <van-notice-bar :wrapable="true" :scrollable="false" :text="readonlySessionTip" />
        <!-- #endif -->
        <!-- #ifndef MP-WEIXIN -->
        <view class="readonly-tip"><text>{{ readonlySessionTip }}</text></view>
        <!-- #endif -->
      </view>
      <view v-if="showHumanFab" class="human-fab" @click="startHumanSupport">
        <text class="human-fab-text">联系人工客服</text>
      </view>
    </view>
    <view v-if="showInputBar" class="input-bar">
      <view class="input-shell">
        <textarea v-model="inputText" class="input-text" :placeholder="inputPlaceholder" :placeholder-style="'color:' + tc.text3" :disabled="isReadonlySession" :auto-height="true" :maxlength="4000" :adjust-position="true" :cursor-spacing="24" :show-confirm-bar="false" @keydown="onInputKeydown" />
        <button class="send-fab" :class="{ 'send-fab--disabled': !inputText.trim() || loading || isReadonlySession || !sessionId }" :disabled="!inputText.trim() || loading || isReadonlySession || !sessionId" hover-class="send-fab--hover" @tap="sendMessage">
          <text class="send-fab-icon">↑</text>
        </button>
      </view>
    </view>
    </view>
  </view>
</template>

<script>
import { getChatMessages, sendChatMessage, sendChatMessageStream, getChatSession, createHumanSupportSession, createChatSession } from '@/common/request/api/mp/chat.js'
import { themeMixin } from '@/common/mixins/theme.js'
import navBackMixin from '@/common/mixins/nav-back.js'

export default {
  mixins: [themeMixin, navBackMixin],
  data() {
    return {
      sessionId: null,
      sessionTitle: '',
      sessionAgentId: null,
      sessionAgentStatus: 'active',
      sessionTopicClosed: false,
      sessionKind: 'dify',
      viewerContext: 'owner',
      messages: [],
      inputText: '',
      loading: false,
      scrollTop: 0,
      skipShowMetaRefreshOnce: false,
      sourceArchiveSessionId: null
    }
  },
  onLoad(query) {
    this.sessionId = parseInt(query.sessionId, 10) || null
    if (!this.sessionId) { uni.showToast({ title: '参数错误', icon: 'none' }); return }
    this.skipShowMetaRefreshOnce = true; this.bootstrap()
  },
  onShow() {
    if (this.skipShowMetaRefreshOnce) { this.skipShowMetaRefreshOnce = false; return }
    if (this.sessionId) this.refreshSessionMeta()
  },
  onReady() {},
  methods: {
    onInputKeydown(e) {
      const evt = (e && e.detail) || e || {}
      const keyCode = Number(evt.keyCode || evt.which || 0)
      const isEnter = keyCode === 13
      const hasCombo = !!(evt.ctrlKey || evt.metaKey)
      if (!isEnter || !hasCombo) return
      if (typeof evt.preventDefault === 'function') evt.preventDefault()
      this.sendMessage()
    },
    isReadonlyStatus(status) { return status && status !== 'active' },
    readonlyMessage(status) { if (status === 'deleted') return '智能体已删除，仅支持查看历史消息'; if (status === 'offline') return '智能体已下架，暂不支持继续对话'; return '' },
    newLocalId() { return `c-${Date.now()}-${Math.random().toString(36).slice(2, 9)}` },
    escapeHtml(text) { return String(text || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;') },
    renderInlineMarkdown(line) {
      const c = this.tc; let html = this.escapeHtml(line)
      html = html.replace(/`([^`\n]+)`/g, `<code style="font-size:24rpx;font-family:Menlo,Monaco,Consolas,'Courier New',monospace;padding:2rpx 8rpx;border-radius:8rpx;background:${c.codeBg};color:${c.codeColor};">$1</code>`)
      html = html.replace(/\*\*([^*]+)\*\*/g, `<strong style="font-weight:700;color:${c.strongColor};">$1</strong>`)
      html = html.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em style="font-style:italic;">$2</em>')
      html = html.replace(/\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/g, `<a href="$2" style="color:${c.linkColor};text-decoration:underline;">$1</a>`)
      return html
    },
    renderAssistantMarkdown(content) {
      const c = this.tc; const src = String(content || '')
      if (!src.trim()) return `<p style="color:${c.text2};">努力思考中...</p>`
      const rows = src.replace(/\r/g, '').split('\n'); const out = []; let inCode = false; let codeRows = []; let inList = false
      const pStyle = `margin:0 0 10rpx;font-size:28rpx;line-height:42rpx;word-break:break-word;color:${c.aiText};`
      const h1Style = `margin:0 0 12rpx;font-size:34rpx;line-height:46rpx;font-weight:700;color:${c.strongColor};`
      const h2Style = `margin:0 0 10rpx;font-size:32rpx;line-height:44rpx;font-weight:700;color:${c.strongColor};`
      const h3Style = `margin:0 0 8rpx;font-size:30rpx;line-height:42rpx;font-weight:700;color:${c.strongColor};`
      const quoteStyle = `margin:0 0 12rpx;padding:10rpx 16rpx;border-left:6rpx solid ${c.quoteBorder};color:${c.quoteText};background:${c.quoteBg};border-radius:0 10rpx 10rpx 0;font-size:27rpx;line-height:40rpx;`
      const ulStyle = `margin:0 0 12rpx;padding-left:34rpx;font-size:28rpx;line-height:42rpx;`
      const liStyle = `margin:8rpx 0;font-size:28rpx;line-height:42rpx;word-break:break-word;color:${c.aiText};`
      const preStyle = `margin:0 0 14rpx;padding:16rpx;border-radius:14rpx;background:${c.preBg};border:1rpx solid ${c.preBorder};overflow:auto;font-size:24rpx;line-height:36rpx;`
      const tableStyle = `width:100%;border-collapse:collapse;table-layout:fixed;margin:0 0 14rpx;font-size:26rpx;line-height:38rpx;border:1px solid ${c.tableBorder};`
      const thStyle = `border:1px solid ${c.tableBorder};padding:10rpx 12rpx;background:${c.thBg};font-weight:600;vertical-align:top;word-break:break-word;font-size:26rpx;line-height:38rpx;color:${c.thText};`
      const tdStyle = `border:1px solid ${c.tableBorder};padding:10rpx 12rpx;vertical-align:top;word-break:break-word;font-size:26rpx;line-height:38rpx;color:${c.tdText};`
      const isTableRow = (line) => { if (!line || !line.includes('|')) return false; const t = line.trim(); return /^\|.*\|$/.test(t) || /^[^|]+\|[^|]+/.test(t) }
      const isTableDivider = (line) => { const t = String(line || '').trim(); if (!t) return false; const norm = t.replace(/^\|/, '').replace(/\|$/, ''); const cols = norm.split('|').map((s) => s.trim()); return cols.length > 0 && cols.every((cc) => /^:?-{3,}:?$/.test(cc)) }
      const splitTableCells = (line) => String(line || '').trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((s) => s.trim())
      const flushCode = () => { if (!inCode) return; const code = this.escapeHtml(codeRows.join('\n')); out.push(`<pre style="${preStyle}"><code style="font-size:24rpx;line-height:36rpx;font-family:Menlo,Monaco,Consolas,'Courier New',monospace;color:${c.preText};">${code}</code></pre>`); inCode = false; codeRows = [] }
      const flushList = () => { if (inList) { out.push('</ul>'); inList = false } }
      for (let i = 0; i < rows.length; i++) {
        const line = rows[i]; const trimmed = line.trim()
        if (trimmed.startsWith('```')) { if (inCode) flushCode(); else { flushList(); inCode = true; codeRows = [] }; continue }
        if (inCode) { codeRows.push(line); continue }
        if (!trimmed) { flushList(); out.push(`<p style="${pStyle}"><br/></p>`); continue }
        const h = trimmed.match(/^(#{1,3})\s+(.*)$/); if (h) { flushList(); const lv = h[1].length; out.push(`<h${lv} style="${lv === 1 ? h1Style : lv === 2 ? h2Style : h3Style}">${this.renderInlineMarkdown(h[2])}</h${lv}>`); continue }
        const q = trimmed.match(/^>\s?(.*)$/); if (q) { flushList(); out.push(`<blockquote style="${quoteStyle}">${this.renderInlineMarkdown(q[1])}</blockquote>`); continue }
        if (isTableRow(trimmed) && i + 1 < rows.length && isTableDivider(rows[i + 1])) {
          flushList(); const hCells = splitTableCells(trimmed); out.push(`<table style="${tableStyle}"><thead><tr>`); hCells.forEach((cell) => out.push(`<th style="${thStyle}">${this.renderInlineMarkdown(cell)}</th>`)); out.push('</tr></thead><tbody>'); i += 2
          while (i < rows.length) { const bl = String(rows[i] || '').trim(); if (!bl || !isTableRow(bl) || isTableDivider(bl)) break; out.push('<tr>'); splitTableCells(bl).forEach((cell) => out.push(`<td style="${tdStyle}">${this.renderInlineMarkdown(cell)}</td>`)); out.push('</tr>'); i += 1 }
          out.push('</tbody></table>'); i -= 1; continue
        }
        const li = trimmed.match(/^[-*]\s+(.*)$/); if (li) { if (!inList) { out.push(`<ul style="${ulStyle}">`); inList = true }; out.push(`<li style="${liStyle}">${this.renderInlineMarkdown(li[1])}</li>`); continue }
        flushList(); out.push(`<p style="${pStyle}">${this.renderInlineMarkdown(trimmed)}</p>`)
      }
      flushCode(); flushList(); return out.join('') || `<p style="color:${c.text3};">（无内容）</p>`
    },
    applySessionMeta(d) {
      this.sessionTitle = d.display_title || d.title || '对话'
      this.sessionAgentId =
        (d.agent && d.agent.id != null ? d.agent.id : null) != null
          ? parseInt(d.agent.id, 10)
          : (d.agent_id != null ? parseInt(d.agent_id, 10) : null)
      this.sessionAgentStatus = d.agent_status || 'active'
      this.sessionTopicClosed = d.is_topic_closed === true
      this.sessionKind = d.session_kind || 'dify'
      this.viewerContext = d.viewer_context || 'owner'
      this.sourceArchiveSessionId = d.source_archive_session_id != null ? d.source_archive_session_id : null
    },
    /** 与后端 format_archive_topic_context 首行「【归档话题】标题」一致，用于单行提示展示 */
    archiveTopicTitleFromSystem(content) {
      const s = String(content || '')
      const m = s.match(/^【归档话题】([^\r\n]+)/)
      if (m) return (m[1] || '').trim() || '未命名话题'
      return '未命名话题'
    },
    openSourceArchiveSession() {
      if (this.viewerContext !== 'owner') return
      if (!this.sourceArchiveSessionId) return
      uni.navigateTo({ url: `/subpkg/chat/chat?sessionId=${this.sourceArchiveSessionId}` })
    },
    async bootstrap() {
      try {
        const d = (await getChatSession(this.sessionId)).data || {}
        this.applySessionMeta(d)
      } catch (e) {
        this.sessionTitle = '对话'
        this.sessionAgentId = null
        this.sessionAgentStatus = 'active'
        this.sessionTopicClosed = false
        this.sessionKind = 'dify'
        this.viewerContext = 'owner'
        this.sourceArchiveSessionId = null
      }
      await this.loadMessages()
    },
    async refreshSessionMeta() {
      try {
        const d = (await getChatSession(this.sessionId)).data || {}
        this.applySessionMeta(d)
      } catch (e) {}
    },
    async refreshSessionAfterTopic() { try { const d = (await getChatSession(this.sessionId)).data || {}; this.applySessionMeta(d) } catch (e) {} },
    async loadMessages() {
      try {
        const res = await getChatMessages(this.sessionId, 1, 100)
        const list = Array.isArray(res.data) ? res.data : []
        this.messages = list.map((m) => ({ id: m.id, role: m.role, content: m.content }))
        this.$nextTick(() => this.scrollToBottom())
      } catch (e) { this.messages = [] }
    },
    async startHumanSupport() {
      if (!this.sessionId) return
      try {
        uni.showLoading({ title: '分配客服…', mask: true })
        const res = await createHumanSupportSession(this.sessionId)
        const d = (res && res.data) || {}
        const nid = d.id
        if (!nid) { uni.showToast({ title: '创建失败', icon: 'none' }); return }
        uni.redirectTo({ url: `/subpkg/chat/chat?sessionId=${nid}` })
      } catch (e) {
        const msg = (e && (e.message || e.msg)) || '暂不可用'
        uni.showToast({ title: String(msg), icon: 'none' })
      } finally {
        try { uni.hideLoading() } catch (err) {}
      }
    },
    async ensureWritableSessionForNewTopic() {
      if (this.sessionKind === 'human_support') return true
      if (!this.sessionTopicClosed) return true
      if (this.sessionAgentStatus !== 'active') return false
      const agentId = this.sessionAgentId
      if (!agentId) return false
      try {
        uni.showLoading({ title: '开启新话题…', mask: true })
        const created = await createChatSession(agentId)
        const nid = created && created.data && created.data.id
        if (!nid) return false
        this.sessionId = nid
        this.sessionTopicClosed = false
        this.messages = []
        await this.bootstrap()
        return true
      } catch (e) {
        return false
      } finally {
        try { uni.hideLoading() } catch (err) {}
      }
    },
    async sendMessage() {
      const t = this.inputText.trim()
      if (!t || this.loading || this.isReadonlySession) return
      if (!this.sessionId) {
        uni.showToast({ title: '会话初始化中，请稍后重试', icon: 'none' })
        return
      }
      this.inputText = ''
      if (this.sessionTopicClosed && this.sessionAgentStatus === 'active') {
        const ok = await this.ensureWritableSessionForNewTopic()
        if (!ok) {
          uni.showToast({ title: '开启新话题失败', icon: 'none' })
          return
        }
      }
      await this.runSend(t)
    },
    retrySend(index) {
      const m = this.messages[index]
      if (!m || this.loading) return
      if (this.viewerContext === 'assigned_staff') {
        if (m.role !== 'assistant' || m.sendStatus !== 'failed') return
        this.runSend(m.content, { retryUserIndex: index })
        return
      }
      if (m.role !== 'user' || m.sendStatus !== 'failed') return
      this.runSend(m.content, { retryUserIndex: index })
    },
    async runSend(query, opts = {}) {
      if (this.sessionKind === 'human_support') {
        await this.runSendHuman(query, opts)
        return
      }
      const { retryUserIndex } = opts; if (!this.sessionId || !query || this.loading) return
      let userIndex, aiIndex
      if (typeof retryUserIndex === 'number') { userIndex = retryUserIndex; const u = this.messages[userIndex]; if (!u || u.role !== 'user' || u.sendStatus !== 'failed') return; u.sendStatus = 'sending'; aiIndex = userIndex + 1; const next = this.messages[aiIndex]; if (next && next.role === 'assistant') next.content = ''; else this.messages.splice(aiIndex, 0, { role: 'assistant', content: '', localId: this.newLocalId() }) }
      else { userIndex = this.messages.length; this.messages.push({ role: 'user', content: query, sendStatus: 'sending', localId: this.newLocalId() }); aiIndex = this.messages.length; this.messages.push({ role: 'assistant', content: '', localId: this.newLocalId() }) }
      this.loading = true; this.$nextTick(() => this.scrollToBottom())
      const fallbackBlocking = async () => { const res = await sendChatMessage(this.sessionId, query); const p = (res && res.data) || {}; if (this.messages[aiIndex]) this.messages[aiIndex].content = p.answer || '（无内容）'; if (p.topic_closed) { uni.showToast({ title: '话题已结束', icon: 'none' }); await this.refreshSessionAfterTopic() } }
      try {
        try {
          const sr = await sendChatMessageStream(this.sessionId, query, (full) => {
            if (this.messages[aiIndex]) this.messages[aiIndex].content = full
            this.$nextTick(() => this.scrollToBottom())
          })
          if (this.messages[aiIndex] && !String(this.messages[aiIndex].content || '').trim()) this.messages[aiIndex].content = '（无内容）'
          if (sr && sr.topicClosed) {
            uni.showToast({ title: '话题已结束', icon: 'none' })
            await this.refreshSessionAfterTopic()
          }
        } catch (e) {
          // 真机优先稳定性：流式链路任意失败都回退 blocking 发送
          await fallbackBlocking()
        }
        if (this.messages[userIndex]) this.messages[userIndex].sendStatus = 'sent'
      } catch (e) { const msg = (e && e.message) || ''; if (msg.includes('删除')) this.sessionAgentStatus = 'deleted'; else if (msg.includes('下架')) this.sessionAgentStatus = 'offline'; if (this.messages[userIndex]) this.messages[userIndex].sendStatus = 'failed'; if (this.messages[aiIndex]) this.messages[aiIndex].content = '发送失败，请稍后重试。' }
      finally { this.loading = false; this.$nextTick(() => this.scrollToBottom()) }
    },
    async runSendHuman(query, opts = {}) {
      const { retryUserIndex } = opts
      if (!this.sessionId || !query || this.loading) return
      let idx = null
      let userIndex = null
      if (this.viewerContext === 'assigned_staff') {
        if (typeof retryUserIndex === 'number') {
          idx = retryUserIndex
          const u = this.messages[idx]
          if (!u || u.role !== 'assistant' || u.sendStatus !== 'failed') return
        } else {
          idx = this.messages.length
        }
      } else if (typeof retryUserIndex === 'number') {
        userIndex = retryUserIndex
        const u = this.messages[userIndex]
        if (!u || u.role !== 'user' || u.sendStatus !== 'failed') return
      } else {
        userIndex = this.messages.length
      }
      this.loading = true
      this.$nextTick(() => this.scrollToBottom())
      try {
        if (this.viewerContext === 'assigned_staff') {
          if (typeof retryUserIndex !== 'number') {
            this.messages.push({ role: 'assistant', content: query, sendStatus: 'sending', localId: this.newLocalId() })
          } else {
            this.messages[idx].sendStatus = 'sending'
          }
          await sendChatMessage(this.sessionId, query)
          if (this.messages[idx]) this.messages[idx].sendStatus = 'sent'
        } else {
          if (typeof retryUserIndex !== 'number') {
            this.messages.push({ role: 'user', content: query, sendStatus: 'sending', localId: this.newLocalId() })
          } else {
            this.messages[userIndex].sendStatus = 'sending'
          }
          await sendChatMessage(this.sessionId, query)
          if (this.messages[userIndex]) this.messages[userIndex].sendStatus = 'sent'
        }
      } catch (e) {
        if (this.viewerContext === 'assigned_staff') {
          if (this.messages[idx] && this.messages[idx].role === 'assistant') this.messages[idx].sendStatus = 'failed'
        } else if (this.messages[userIndex] && this.messages[userIndex].role === 'user') {
          this.messages[userIndex].sendStatus = 'failed'
        }
      } finally {
        this.loading = false
        this.$nextTick(() => this.scrollToBottom())
      }
    },
    scrollToBottom() { this.scrollTop = this.scrollTop === 99999 ? 99998 : 99999 }
  },
  computed: {
    showHumanFab() {
      return this.sessionKind === 'dify' && this.sessionTopicClosed && this.sessionAgentStatus === 'active'
    },
    showNoticeBar() {
      return (this.sessionTopicClosed && this.sessionAgentStatus === 'active') || this.isReadonlyStatus(this.sessionAgentStatus)
    },
    showInputBar() {
      if (this.sessionKind === 'human_support') return true
      return true
    },
    inputPlaceholder() {
      if (this.viewerContext === 'assigned_staff') return '输入回复…'
      if (this.sessionTopicClosed && this.sessionAgentStatus === 'active') return '开启新话题…'
      return '输入你的问题…'
    },
    isReadonlySession() {
      if (this.sessionKind === 'human_support') return false
      return this.isReadonlyStatus(this.sessionAgentStatus)
    },
    readonlySessionTip() {
      if (this.sessionTopicClosed && this.sessionAgentStatus === 'active') return '本话题已结束。你可以继续输入并发送，开启新的话题。'
      return this.readonlyMessage(this.sessionAgentStatus)
    }
  }
}
</script>

<style lang="scss">
page {
  height: 100%;
  box-sizing: border-box;
}
</style>

<style lang="scss" scoped>
@import '@/uni.scss';

.chat-container { display: flex; flex-direction: column; flex: 1; min-height: 0; background: var(--t-root); position: relative; }
.msg-list {
  flex: 1;
  min-height: 0;
  padding: $mp-gap-6 $mp-gap-7;
  padding-bottom: $mp-scene-detail-list-pad-bottom;
  overflow-y: auto;
}
.msg-item { display: flex; flex-direction: column; margin-bottom: $mp-gap-2; }
.context-hint {
  align-self: center; max-width: $mp-scene-context-max; background: var(--t-accent-bg); border: 1rpx solid var(--t-border-focus);
  border-radius: $mp-radius-lg; padding: $mp-scene-context-py $mp-scene-context-px; margin: $mp-scene-context-my 0;
}
.context-hint-text {
  color: var(--t-text-2); font-size: $mp-font-meta; line-height: $mp-lh-context;
  white-space: pre-wrap; word-break: break-all;
}
.archive-tip {
  align-self: center; max-width: 88%; min-width: 0; box-sizing: border-box;
  background: transparent; border: none;
  padding: $mp-scene-archive-py $mp-scene-archive-px;
  margin: $mp-scene-archive-my 0 $mp-gap-1; display: flex; align-items: center;
}
.archive-tip-label { flex-shrink: 0; font-size: $mp-font-meta; margin-right: $mp-gap-2; }
.archive-tip-title {
  flex: 1; min-width: 0; color: var(--t-accent);
  font-size: $mp-font-sub; line-height: $mp-lh-archive;
  text-decoration: underline; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.staff-peer {
  max-width: $mp-scene-user-max; align-self: flex-start; background: var(--t-elevated); color: var(--t-text-1);
  border-radius: $mp-radius-bubble $mp-radius-bubble $mp-radius-bubble $mp-radius-xs; border: 1rpx solid var(--t-border);
}
/* 高度随 NoticeBar + 按钮内容自适应；安全区仅由下方 .input-bar 承担，避免与输入栏之间重复留白 */
.topic-end-stack {
  flex-shrink: 0;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: $mp-gap-3;
}
.human-fab {
  align-self: flex-end;
  margin-right: $mp-scene-human-fab-x;
  padding: $mp-scene-human-fab-pad-y $mp-scene-human-fab-pad-x; border-radius: $mp-radius-pill;
  background: linear-gradient(135deg, var(--t-accent-from), var(--t-accent-to));
  box-shadow: 0 $mp-scene-human-fab-shadow-y $mp-scene-human-fab-shadow-blur var(--t-accent-shadow);
}
.human-fab-text { color: var(--t-accent-text); font-size: $mp-font-sub; font-weight: 600; }
.bubble {
  max-width: $mp-scene-bubble-max; padding: $mp-gap-6 $mp-gap-7; margin: $mp-gap-2 0;
  border-radius: $mp-radius-bubble; word-break: break-all; box-sizing: border-box;
}
.bubble-content { white-space: pre-wrap; word-break: break-all; font-size: $mp-font-body; line-height: $mp-lh-body; }
.bubble-content--rich { white-space: normal; font-size: $mp-font-body; line-height: $mp-lh-body; }
.user {
  background: linear-gradient(135deg, var(--t-accent-from), var(--t-accent-to)); color: var(--t-accent-text);
  align-self: flex-end; margin-left: auto; max-width: $mp-scene-user-max;
  border-radius: $mp-radius-bubble $mp-radius-bubble $mp-radius-xs $mp-radius-bubble;
  box-shadow: 0 $mp-scene-elev-y $mp-scene-blur-bubble var(--t-accent-shadow);
}
.ai {
  background: var(--t-surface); color: var(--t-text-1); align-self: stretch; max-width: none;
  width: calc(100% + #{$mp-scene-ai-pull-total}); margin-left: -$mp-scene-ai-pull; margin-right: -$mp-scene-ai-pull;
  border-radius: 0; border-bottom: 1rpx solid var(--t-divider); padding: $mp-gap-7 $mp-gap-8;
}
.msg-meta {
  align-self: flex-end; margin-left: auto; padding: $mp-gap-1 0 $mp-gap-2; font-size: $mp-font-meta; color: var(--t-text-3);
}
.msg-meta--staff { align-self: flex-end; margin-left: auto; margin-right: 0; }
.msg-meta-text { color: var(--t-text-3); }
.retry-link { color: var(--t-accent); font-weight: 500; }
.input-bar {
  flex-shrink: 0; padding: $mp-gap-4 $mp-gap-7;
  padding-bottom: calc(#{$mp-gap-4} + env(safe-area-inset-bottom));
  background: var(--t-surface); box-shadow: var(--t-shadow-up);
}
.readonly-notice-slot { flex-shrink: 0; width: 100%; box-sizing: border-box; }
.readonly-tip {
  padding: $mp-gap-4 $mp-gap-5; border-radius: $mp-radius-md;
  background: var(--t-error-bg); color: var(--t-error); font-size: $mp-font-meta;
  border: 1rpx solid var(--t-error-border);
}
.input-shell {
  display: flex; align-items: flex-end; background: var(--t-elevated); border-radius: $mp-radius-pill;
  border: $mp-border solid var(--t-border);
  padding: $mp-gap-3 $mp-gap-3 $mp-gap-3 $mp-gap-7; gap: $mp-gap-3;
  transition: border-color 0.25s ease;
}
.input-shell:focus-within { border-color: var(--t-border-focus); }
.input-text {
  flex: 1; min-height: $mp-scene-input-min-h; max-height: $mp-scene-input-max-h;
  padding: $mp-scene-input-pty 0; font-size: $mp-font-input; line-height: $mp-lh-input;
  color: var(--t-text-1); width: 100%;
}
.send-fab {
  flex-shrink: 0; display: flex; align-items: center; justify-content: center;
  width: $mp-hit-fab; height: $mp-hit-fab; margin: 0; padding: 0; border: none; border-radius: 50%;
  background: linear-gradient(135deg, var(--t-accent-from), var(--t-accent-to)); line-height: 1;
  box-shadow: 0 $mp-scene-elev-y $mp-scene-blur-fab var(--t-accent-shadow);
}
.send-fab-icon { color: var(--t-accent-text); font-size: $mp-hit-fab-icon; line-height: 1; font-weight: 700; }
.send-fab::after { border: none; }
.send-fab--disabled { background: var(--t-text-4); box-shadow: none; }
.send-fab--disabled .send-fab-icon { color: var(--t-text-3); }
.send-fab--hover { opacity: 0.88; }
.send-fab--disabled.send-fab--hover { opacity: 1; }
</style>
