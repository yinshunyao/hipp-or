<template>
  <view :class="themeClass" class="page-with-nav">
    <uni-nav-bar
      title="需求"
      fixed
      status-bar
      :border="false"
      :background-color="'var(--t-nav-bg)'"
      :color="'var(--t-nav-text)'"
    />
    <view class="chat-container page-with-nav__body">
    <scroll-view
      :scroll-top="scrollTop"
      scroll-y
      class="msg-list"
      scroll-with-animation
      :upper-threshold="80"
      @scrolltoupper="onArchiveScrollToUpper"
    >
      <view v-for="(item, index) in timelineItems" :key="index" class="msg-item">
        <view v-if="item.kind === 'archive_tip'" class="archive-tip" :data-session-id="item.sessionId" @click="openArchivedSession">
          <text class="archive-tip-label">📁</text>
          <view class="archive-tip-title">{{ item.title }}</view>
        </view>
        <view v-if="item.kind !== 'archive_tip'" :class="['bubble', item.role === 'user' ? 'user' : 'ai']">
          <text v-if="item.role === 'user'" class="bubble-content" selectable>{{ item.content }}</text>
          <rich-text v-else class="bubble-content bubble-content--rich" :nodes="renderAssistantMarkdown(item.content)"></rich-text>
        </view>
        <view v-if="item.role === 'user' && (item.sendStatus === 'sending' || item.sendStatus === 'failed')" class="msg-meta">
          <text v-if="item.sendStatus === 'sending'" class="msg-meta-text">发送中…</text>
          <text v-else class="retry-link" @click="retrySend(index)">重试</text>
        </view>
      </view>
    </scroll-view>
    <view v-if="showNoticeBar" class="readonly-notice-slot">
      <!-- #ifdef MP-WEIXIN -->
      <van-notice-bar :wrapable="true" :scrollable="false" :text="readonlySessionTip" />
      <!-- #endif -->
      <!-- #ifndef MP-WEIXIN -->
      <view class="readonly-tip"><text>{{ readonlySessionTip }}</text></view>
      <!-- #endif -->
    </view>
    <view class="input-bar">
      <view class="input-shell">
        <textarea v-model="inputText" class="input-text" :placeholder="inputPlaceholder" :placeholder-style="'color:' + tc.text3" :disabled="isReadonlySession || !sessionId" :auto-height="true" :maxlength="4000" :adjust-position="true" :cursor-spacing="24" :show-confirm-bar="false" @keydown="onInputKeydown" />
        <button class="send-fab" :class="{ 'send-fab--disabled': !inputText.trim() || loading || isReadonlySession || !sessionId }" :disabled="!inputText.trim() || loading || isReadonlySession || !sessionId" hover-class="send-fab--hover" @tap="sendMessage">
          <text class="send-fab-icon">↑</text>
        </button>
      </view>
    </view>
    </view>
  </view>
</template>

<script>
import { resolveSceneAgent, createChatSession, getArchivedTopics, getChatMessages, sendChatMessage, sendChatMessageStream, getChatSession } from '@/common/request/api/mp/chat.js'
import { themeMixin } from '@/common/mixins/theme.js'

export default {
  mixins: [themeMixin],
  data() {
    return {
      sessionId: null, sceneAgentId: null, sessionTitle: '需求', sessionAgentStatus: 'active', sessionTopicClosed: false,
      messages: [], archivedTopicTips: [], archivedHasMore: false, archivedLoading: false,
      inputText: '', loading: false, scrollTop: 0,
    }
  },
  async onShow() { await this.ensureSceneSession(); if (this.sessionId) await this.bootstrap() },
  onPullDownRefresh() {
    this.ensureSceneSession().then(() => (this.sessionId ? this.bootstrap() : Promise.resolve())).finally(() => uni.stopPullDownRefresh())
  },
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
    async ensureSceneSession() {
      try {
        const res = await resolveSceneAgent('requirement')
        const d = (res && res.data) || {}
        const ag = d.agent
        if (!ag || !ag.id) {
          this.sceneAgentId = null
          this.archivedTopicTips = []
          this.archivedHasMore = false
          uni.showToast({ title: '当前场景暂不可用', icon: 'none' })
          return
        }
        const sceneAgentId = ag.id
        this.sceneAgentId = sceneAgentId
        await this.loadArchivedInitial()
        if (d.session && d.session.id) { this.sessionId = d.session.id; return }
        const created = await createChatSession(sceneAgentId)
        this.sessionId = created.data && created.data.id
      } catch (e) {
        this.sessionId = null
        this.sceneAgentId = null
        this.archivedTopicTips = []
        this.archivedHasMore = false
      }
    },
    isReadonlyStatus(status) { return status && status !== 'active' },
    readonlyMessage(status) { if (status === 'deleted') return '智能体已删除，仅支持查看历史消息'; if (status === 'offline') return '智能体已下架，暂不支持继续对话'; return '' },
    newLocalId() { return `c-${Date.now()}-${Math.random().toString(36).slice(2, 9)}` },
    escapeHtml(text) { return String(text || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;') },
    renderInlineMarkdown(line) {
      const c = this.tc
      let html = this.escapeHtml(line)
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
    async loadArchivedInitial() {
      if (!this.sceneAgentId) { this.archivedTopicTips = []; this.archivedHasMore = false; return }
      this.archivedLoading = true
      try {
        const res = await getArchivedTopics(this.sceneAgentId, { limit: 20 })
        const d = (res && res.data) || {}
        const raw = Array.isArray(d.items) ? d.items : []
        this.archivedTopicTips = raw.map((x) => ({
          kind: 'archive_tip',
          localId: `archive-${x.session_id}`,
          sessionId: x.session_id,
          title: x.display_title || '未命名话题',
          updateTs: typeof x.update_ts === 'number' ? x.update_ts : 0
        }))
        this.archivedHasMore = !!d.has_more
      } catch (e) {
        this.archivedTopicTips = []
        this.archivedHasMore = false
      } finally { this.archivedLoading = false }
    },
    async onArchiveScrollToUpper() {
      if (!this.archivedHasMore || this.archivedLoading || !this.sceneAgentId || !this.archivedTopicTips.length) return
      const first = this.archivedTopicTips[0]
      if (first == null || first.sessionId == null) return
      this.archivedLoading = true
      try {
        const res = await getArchivedTopics(this.sceneAgentId, {
          limit: 20,
          before_update_ts: first.updateTs,
          before_session_id: first.sessionId
        })
        const d = (res && res.data) || {}
        const raw = Array.isArray(d.items) ? d.items : []
        const mapped = raw.map((x) => ({
          kind: 'archive_tip',
          localId: `archive-${x.session_id}`,
          sessionId: x.session_id,
          title: x.display_title || '未命名话题',
          updateTs: typeof x.update_ts === 'number' ? x.update_ts : 0
        }))
        const seen = new Set(this.archivedTopicTips.map((t) => t.sessionId))
        const merged = mapped.filter((x) => !seen.has(x.sessionId))
        this.archivedTopicTips = [...merged, ...this.archivedTopicTips]
        this.archivedHasMore = !!d.has_more
      } catch (e) {} finally { this.archivedLoading = false }
    },
    async bootstrap() {
      if (!this.sessionId) return
      try { const d = (await getChatSession(this.sessionId)).data || {}; this.sessionTitle = d.display_title || d.title || '需求'; this.sessionAgentStatus = d.agent_status || 'active'; this.sessionTopicClosed = d.is_topic_closed === true }
      catch (e) { this.sessionTitle = '需求'; this.sessionAgentStatus = 'active'; this.sessionTopicClosed = false }
      await this.loadMessages()
    },
    async loadMessages() {
      if (!this.sessionId) return
      try {
        const res = await getChatMessages(this.sessionId, 1, 100)
        const list = Array.isArray(res.data) ? res.data : []
        this.messages = list.map((m) => ({ id: m.id, role: m.role, content: m.content }))
        this.$nextTick(() => this.scrollToBottom())
      } catch (e) { this.messages = [] }
    },
    async ensureWritableSessionForNewTopic() {
      if (!this.sessionTopicClosed) return true
      if (this.sessionAgentStatus !== 'active') return false
      if (!this.sceneAgentId) return false
      try {
        uni.showLoading({ title: '开启新话题…', mask: true })
        const created = await createChatSession(this.sceneAgentId)
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
      if (!t || this.loading || !this.sessionId || this.isReadonlySession) return
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
    retrySend(index) { const m = this.timelineItems[index]; if (!m || m.role !== 'user' || m.sendStatus !== 'failed' || this.loading) return; const ui = this.messages.findIndex((x) => x.localId === m.localId || x.id === m.id); if (ui < 0) return; this.runSend(m.content, { retryUserIndex: ui }) },
    openArchivedSession(e) { const sid = e && e.currentTarget && e.currentTarget.dataset ? e.currentTarget.dataset.sessionId : null; if (sid) uni.navigateTo({ url: `/subpkg/chat/chat?sessionId=${sid}` }) },
    async runSend(query, opts = {}) {
      const { retryUserIndex } = opts
      if (!this.sessionId || !query || this.loading) return
      let userIndex, aiIndex
      if (typeof retryUserIndex === 'number') {
        userIndex = retryUserIndex; const u = this.messages[userIndex]; if (!u || u.role !== 'user' || u.sendStatus !== 'failed') return; u.sendStatus = 'sending'; aiIndex = userIndex + 1
        const next = this.messages[aiIndex]; if (next && next.role === 'assistant') next.content = ''; else this.messages.splice(aiIndex, 0, { role: 'assistant', content: '', localId: this.newLocalId() })
      } else {
        userIndex = this.messages.length; this.messages.push({ role: 'user', content: query, sendStatus: 'sending', localId: this.newLocalId() })
        aiIndex = this.messages.length; this.messages.push({ role: 'assistant', content: '', localId: this.newLocalId() })
      }
      this.loading = true; this.$nextTick(() => this.scrollToBottom())
      const fallbackBlocking = async () => { const res = await sendChatMessage(this.sessionId, query); const p = (res && res.data) || {}; if (this.messages[aiIndex]) this.messages[aiIndex].content = p.answer || '（无内容）'; if (p.topic_closed) { uni.showToast({ title: '话题已结束', icon: 'none' }); await this.bootstrap(); await this.loadArchivedInitial() } }
      try {
        try { const sr = await sendChatMessageStream(this.sessionId, query, (full) => { if (this.messages[aiIndex]) this.messages[aiIndex].content = full; this.$nextTick(() => this.scrollToBottom()) }); if (this.messages[aiIndex] && !String(this.messages[aiIndex].content || '').trim()) this.messages[aiIndex].content = '（无内容）'; if (sr && sr.topicClosed) { uni.showToast({ title: '话题已结束', icon: 'none' }); await this.bootstrap(); await this.loadArchivedInitial() } }
        catch (e) { const msg = (e && e.message) || ''; if (msg === 'no stream' || msg === 'no chunked') await fallbackBlocking(); else throw e }
        if (this.messages[userIndex]) this.messages[userIndex].sendStatus = 'sent'
      } catch (e) { const msg = (e && e.message) || ''; if (msg.includes('删除')) this.sessionAgentStatus = 'deleted'; else if (msg.includes('下架')) this.sessionAgentStatus = 'offline'; if (this.messages[userIndex]) this.messages[userIndex].sendStatus = 'failed'; if (this.messages[aiIndex]) this.messages[aiIndex].content = '发送失败，请稍后重试。' }
      finally { this.loading = false; this.$nextTick(() => this.scrollToBottom()) }
    },
    scrollToBottom() { this.scrollTop = this.scrollTop === 99999 ? 99998 : 99999 }
  },
  computed: {
    timelineItems() { return [...this.archivedTopicTips, ...this.messages] },
    showNoticeBar() { return (this.sessionTopicClosed && this.sessionAgentStatus === 'active') || this.isReadonlyStatus(this.sessionAgentStatus) },
    inputPlaceholder() { return (this.sessionTopicClosed && this.sessionAgentStatus === 'active') ? '开启新话题…' : '输入你的需求...' },
    isReadonlySession() { return this.isReadonlyStatus(this.sessionAgentStatus) },
    readonlySessionTip() { if (this.sessionTopicClosed && this.sessionAgentStatus === 'active') return '本话题已结束。你可以继续输入并发送，开启新的话题。'; return this.readonlyMessage(this.sessionAgentStatus) }
  }
}
</script>

<style lang="scss">
/* 避免 100vh 在部分微信端与原生导航栏区域叠加，遮挡左上角返回/胶囊 */
page {
  height: 100%;
  box-sizing: border-box;
}
</style>

<style lang="scss" scoped>
@import '@/uni.scss';

.chat-container { display: flex; flex-direction: column; flex: 1; min-height: 0; background: var(--t-root); }
.msg-list { flex: 1; padding: $mp-gap-6 $mp-gap-7; overflow-y: auto; }
.msg-item { display: flex; flex-direction: column; margin-bottom: $mp-gap-2; }
.archive-tip {
  align-self: center; max-width: 88%; min-width: 0; box-sizing: border-box;
  background: transparent; border: none;
  padding: $mp-scene-archive-py $mp-scene-archive-px;
  margin: $mp-scene-archive-my 0 $mp-gap-1; display: flex; align-items: center;
}
.archive-tip-label { flex-shrink: 0; font-size: $mp-font-meta; margin-right: $mp-gap-2; }
.archive-tip-title {
  flex: 1;
  min-width: 0;
  color: var(--t-accent);
  font-size: $mp-font-sub;
  line-height: $mp-lh-archive;
  text-decoration: underline;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bubble {
  max-width: $mp-scene-bubble-max; padding: $mp-gap-6 $mp-gap-7; margin: $mp-gap-2 0;
  border-radius: $mp-radius-bubble; word-break: break-all; box-sizing: border-box;
}
.bubble-content {
  white-space: pre-wrap; word-break: break-all;
  font-size: $mp-font-body; line-height: $mp-lh-body;
}
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
  align-self: flex-end; margin-left: auto;
  padding: $mp-gap-1 0 $mp-gap-2; font-size: $mp-font-meta; color: var(--t-text-3);
}
.msg-meta-text { color: var(--t-text-3); }
.retry-link { color: var(--t-accent); font-weight: 500; }
.input-bar {
  flex-shrink: 0; padding: $mp-gap-4 $mp-gap-7;
  padding-bottom: calc(#{$mp-gap-4} + var(--custom-tabbar-height) + env(safe-area-inset-bottom));
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
  padding: $mp-gap-3 $mp-gap-3 $mp-gap-3 $mp-gap-7;
  gap: $mp-gap-3;
}
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
