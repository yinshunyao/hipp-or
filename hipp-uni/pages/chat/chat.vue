<template>
  <view class="chat-container">
    <scroll-view
      :scroll-top="scrollTop"
      scroll-y
      class="msg-list"
      scroll-with-animation
    >
      <view
        v-for="(item, index) in messages"
        :key="item.id || item.localId || 'idx-' + index"
        class="msg-item"
      >
        <view :class="['bubble', item.role === 'user' ? 'user' : 'ai']">
          <text v-if="item.role === 'user'" class="bubble-content" selectable>{{ item.content }}</text>
          <rich-text v-else class="bubble-content bubble-content--rich" :nodes="renderAssistantMarkdown(item.content)"></rich-text>
        </view>
        <view
          v-if="item.role === 'user' && (item.sendStatus === 'sending' || item.sendStatus === 'failed')"
          class="msg-meta"
        >
          <text v-if="item.sendStatus === 'sending'" class="msg-meta-text">发送中…</text>
          <text v-else class="retry-link" @click="retrySend(index)">重试</text>
        </view>
      </view>
    </scroll-view>

    <view v-if="isReadonlySession" class="readonly-tip">
      <text>{{ readonlyTip }}</text>
    </view>

    <view class="input-bar">
      <view class="input-shell">
        <textarea
          v-model="inputText"
          class="input-text"
          placeholder="输入你的问题..."
          :disabled="isReadonlySession"
          :auto-height="true"
          :maxlength="4000"
          :adjust-position="true"
          :cursor-spacing="24"
          :show-confirm-bar="false"
          confirm-type="send"
          @confirm="sendMessage"
        />
        <button
          class="send-fab"
          :class="{ 'send-fab--disabled': !inputText.trim() || loading || isReadonlySession }"
          :disabled="!inputText.trim() || loading || isReadonlySession"
          hover-class="send-fab--hover"
          @click="sendMessage"
        >
          <uni-icons type="arrow-up" color="#ffffff" :size="22" />
        </button>
      </view>
    </view>
  </view>
</template>

<script>
import {
  getChatMessages,
  sendChatMessage,
  sendChatMessageStream,
  getChatSession
} from '@/common/request/api/mp/chat.js'

export default {
  data() {
    return {
      sessionId: null,
      sessionTitle: '',
      sessionAgentStatus: 'active',
      messages: [],
      inputText: '',
      loading: false,
      scrollTop: 0
    }
  },
  onLoad(query) {
    this.sessionId = parseInt(query.sessionId, 10) || null
    if (!this.sessionId) {
      uni.showToast({ title: '参数错误', icon: 'none' })
      return
    }
    this.bootstrap()
  },
  onReady() {
    if (this.sessionTitle) {
      uni.setNavigationBarTitle({ title: this.sessionTitle })
    }
  },
  methods: {
    isReadonlyStatus(status) {
      return status && status !== 'active'
    },
    readonlyMessage(status) {
      if (status === 'deleted') return '智能体已删除，仅支持查看历史消息'
      if (status === 'offline') return '智能体已下架，暂不支持继续对话'
      return ''
    },
    newLocalId() {
      return `c-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
    },
    escapeHtml(text) {
      return String(text || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
    },
    renderInlineMarkdown(line) {
      let html = this.escapeHtml(line)
      html = html.replace(
        /`([^`\n]+)`/g,
        '<code style="font-size:24rpx;font-family:Menlo,Monaco,Consolas,\'Courier New\',monospace;padding:2rpx 8rpx;border-radius:8rpx;background:rgba(0,0,0,0.06);">$1</code>'
      )
      html = html.replace(/\*\*([^*]+)\*\*/g, '<strong style="font-weight:700;">$1</strong>')
      html = html.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em style="font-style:italic;">$2</em>')
      html = html.replace(
        /\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/g,
        '<a href="$2" style="color:#1677ff;text-decoration:underline;">$1</a>'
      )
      return html
    },
    renderAssistantMarkdown(content) {
      const src = String(content || '')
      if (!src.trim()) return '<p>努力思考中...</p>'

      const rows = src.replace(/\r/g, '').split('\n')
      const out = []
      let inCode = false
      let codeRows = []
      let inList = false
      const pStyle = 'margin:0 0 10rpx;font-size:24rpx;line-height:36rpx;word-break:break-word;color:inherit;'
      const h1Style = 'margin:0 0 8rpx;font-size:26rpx;line-height:36rpx;font-weight:700;color:inherit;'
      const h2Style = 'margin:0 0 8rpx;font-size:25rpx;line-height:34rpx;font-weight:700;color:inherit;'
      const h3Style = 'margin:0 0 6rpx;font-size:24rpx;line-height:32rpx;font-weight:700;color:inherit;'
      const quoteStyle =
        'margin:0 0 12rpx;padding:8rpx 14rpx;border-left:6rpx solid #d5d7db;color:#555;background:rgba(0,0,0,0.03);border-radius:8rpx;font-size:27rpx;line-height:40rpx;'
      const ulStyle = 'margin:0 0 12rpx;padding-left:34rpx;font-size:28rpx;line-height:40rpx;'
      const liStyle = 'margin:8rpx 0;font-size:26rpx;line-height:40rpx;word-break:break-word;'
      const preStyle =
        'margin:0 0 12rpx;padding:14rpx;border-radius:12rpx;background:#f6f8fa;overflow:auto;font-size:24rpx;line-height:36rpx;'
      const tableStyle =
        'width:100%;border-collapse:collapse;table-layout:fixed;margin:0 0 12rpx;font-size:26rpx;line-height:38rpx;border:1px solid #d8dde3;'
      const thStyle =
        'border:1px solid #d8dde3;padding:10rpx 12rpx;background:#f4f6f8;font-weight:600;vertical-align:top;word-break:break-word;font-size:26rpx;line-height:38rpx;'
      const tdStyle =
        'border:1px solid #d8dde3;padding:10rpx 12rpx;vertical-align:top;word-break:break-word;font-size:26rpx;line-height:38rpx;'
      const isTableRow = (line) => {
        if (!line || !line.includes('|')) return false
        const t = line.trim()
        return /^\|.*\|$/.test(t) || /^[^|]+\|[^|]+/.test(t)
      }
      const isTableDivider = (line) => {
        const t = String(line || '').trim()
        if (!t) return false
        const norm = t.replace(/^\|/, '').replace(/\|$/, '')
        const cols = norm.split('|').map((s) => s.trim())
        if (!cols.length) return false
        return cols.every((c) => /^:?-{3,}:?$/.test(c))
      }
      const splitTableCells = (line) => {
        const norm = String(line || '')
          .trim()
          .replace(/^\|/, '')
          .replace(/\|$/, '')
        return norm.split('|').map((s) => s.trim())
      }

      const flushCode = () => {
        if (!inCode) return
        const code = this.escapeHtml(codeRows.join('\n'))
        out.push(
          `<pre style="${preStyle}"><code style="font-size:24rpx;line-height:36rpx;font-family:Menlo,Monaco,Consolas,'Courier New',monospace;">${code}</code></pre>`
        )
        inCode = false
        codeRows = []
      }
      const flushList = () => {
        if (inList) {
          out.push('</ul>')
          inList = false
        }
      }

      for (let i = 0; i < rows.length; i++) {
        const line = rows[i]
        const trimmed = line.trim()

        if (trimmed.startsWith('```')) {
          if (inCode) {
            flushCode()
          } else {
            flushList()
            inCode = true
            codeRows = []
          }
          continue
        }
        if (inCode) {
          codeRows.push(line)
          continue
        }

        if (!trimmed) {
          flushList()
          out.push(`<p style="${pStyle}"><br/></p>`)
          continue
        }

        const h = trimmed.match(/^(#{1,3})\s+(.*)$/)
        if (h) {
          flushList()
          const level = h[1].length
          const hStyle = level === 1 ? h1Style : level === 2 ? h2Style : h3Style
          out.push(`<h${level} style="${hStyle}">${this.renderInlineMarkdown(h[2])}</h${level}>`)
          continue
        }

        const q = trimmed.match(/^>\s?(.*)$/)
        if (q) {
          flushList()
          out.push(`<blockquote style="${quoteStyle}">${this.renderInlineMarkdown(q[1])}</blockquote>`)
          continue
        }
        if (
          isTableRow(trimmed) &&
          i + 1 < rows.length &&
          isTableDivider(rows[i + 1])
        ) {
          flushList()
          const headerCells = splitTableCells(trimmed)
          out.push(`<table style="${tableStyle}"><thead><tr>`)
          headerCells.forEach((cell) => {
            out.push(`<th style="${thStyle}">${this.renderInlineMarkdown(cell)}</th>`)
          })
          out.push('</tr></thead><tbody>')
          i += 2
          while (i < rows.length) {
            const bodyLine = String(rows[i] || '').trim()
            if (!bodyLine || !isTableRow(bodyLine) || isTableDivider(bodyLine)) break
            const bodyCells = splitTableCells(bodyLine)
            out.push('<tr>')
            bodyCells.forEach((cell) => {
              out.push(`<td style="${tdStyle}">${this.renderInlineMarkdown(cell)}</td>`)
            })
            out.push('</tr>')
            i += 1
          }
          out.push('</tbody></table>')
          i -= 1
          continue
        }

        const li = trimmed.match(/^[-*]\s+(.*)$/)
        if (li) {
          if (!inList) {
            out.push(`<ul style="${ulStyle}">`)
            inList = true
          }
          out.push(`<li style="${liStyle}">${this.renderInlineMarkdown(li[1])}</li>`)
          continue
        }

        flushList()
        out.push(`<p style="${pStyle}">${this.renderInlineMarkdown(trimmed)}</p>`)
      }

      flushCode()
      flushList()
      return out.join('') || '<p>（无内容）</p>'
    },
    async bootstrap() {
      try {
        const detail = await getChatSession(this.sessionId)
        const d = detail.data || {}
        this.sessionTitle = d.title || '对话'
        this.sessionAgentStatus = d.agent_status || 'active'
        uni.setNavigationBarTitle({ title: this.sessionTitle })
      } catch (e) {
        this.sessionTitle = '对话'
        this.sessionAgentStatus = 'active'
      }
      await this.loadMessages()
    },
    async loadMessages() {
      try {
        const res = await getChatMessages(this.sessionId, 1, 100)
        const list = Array.isArray(res.data) ? res.data : []
        this.messages = list.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content
        }))
        this.$nextTick(() => this.scrollToBottom())
      } catch (e) {
        this.messages = []
      }
    },
    async sendMessage() {
      const t = this.inputText.trim()
      if (!t || this.loading || !this.sessionId || this.isReadonlySession) return
      this.inputText = ''
      await this.runSend(t)
    },
    retrySend(index) {
      const m = this.messages[index]
      if (!m || m.role !== 'user' || m.sendStatus !== 'failed' || this.loading) return
      this.runSend(m.content, { retryUserIndex: index })
    },
    /**
     * @param {string} query
     * @param {{ retryUserIndex?: number }} [opts]
     */
    async runSend(query, opts = {}) {
      const { retryUserIndex } = opts
      if (!this.sessionId || !query || this.loading) return

      let userIndex
      let aiIndex

      if (typeof retryUserIndex === 'number') {
        userIndex = retryUserIndex
        const u = this.messages[userIndex]
        if (!u || u.role !== 'user' || u.sendStatus !== 'failed') return
        u.sendStatus = 'sending'
        aiIndex = userIndex + 1
        const next = this.messages[aiIndex]
        if (next && next.role === 'assistant') {
          next.content = ''
        } else {
          this.messages.splice(aiIndex, 0, {
            role: 'assistant',
            content: '',
            localId: this.newLocalId()
          })
        }
      } else {
        userIndex = this.messages.length
        this.messages.push({
          role: 'user',
          content: query,
          sendStatus: 'sending',
          localId: this.newLocalId()
        })
        aiIndex = this.messages.length
        this.messages.push({
          role: 'assistant',
          content: '',
          localId: this.newLocalId()
        })
      }

      this.loading = true
      this.$nextTick(() => this.scrollToBottom())

      const fallbackBlocking = async () => {
        const res = await sendChatMessage(this.sessionId, query)
        const answer = (res.data && res.data.answer) || ''
        if (this.messages[aiIndex]) {
          this.messages[aiIndex].content = answer || '（无内容）'
        }
      }

      try {
        try {
          await sendChatMessageStream(this.sessionId, query, (full) => {
            if (this.messages[aiIndex]) {
              this.messages[aiIndex].content = full
            }
            this.$nextTick(() => this.scrollToBottom())
          })
          if (this.messages[aiIndex] && !String(this.messages[aiIndex].content || '').trim()) {
            this.messages[aiIndex].content = '（无内容）'
          }
        } catch (e) {
          const msg = (e && e.message) || ''
          if (msg === 'no stream' || msg === 'no chunked') {
            await fallbackBlocking()
          } else {
            throw e
          }
        }
        if (this.messages[userIndex]) {
          this.messages[userIndex].sendStatus = 'sent'
        }
      } catch (e) {
        const msg = (e && e.message) || ''
        if (msg.includes('删除')) {
          this.sessionAgentStatus = 'deleted'
        } else if (msg.includes('下架')) {
          this.sessionAgentStatus = 'offline'
        }
        if (this.messages[userIndex]) {
          this.messages[userIndex].sendStatus = 'failed'
        }
        if (this.messages[aiIndex]) {
          this.messages[aiIndex].content = '发送失败，请稍后重试。'
        }
      } finally {
        this.loading = false
        this.$nextTick(() => this.scrollToBottom())
      }
    },
    scrollToBottom() {
      this.scrollTop = this.scrollTop === 99999 ? 99998 : 99999
    }
  },
  computed: {
    isReadonlySession() {
      return this.isReadonlyStatus(this.sessionAgentStatus)
    },
    readonlyTip() {
      return this.readonlyMessage(this.sessionAgentStatus)
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  box-sizing: border-box;
  background: #f5f5f5;
}
.msg-list {
  flex: 1;
  padding: 20rpx;
  overflow-y: auto;
}
.msg-item {
  display: flex;
  flex-direction: column;
}
.bubble {
  max-width: 80%;
  padding: 20rpx;
  margin: 10rpx 0;
  border-radius: 16rpx;
  word-break: break-all;
  box-sizing: border-box;
}
.bubble-content {
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 28rpx;
  line-height: 40rpx;
}
.bubble-content--rich {
  white-space: normal;
  font-size: 28rpx;
  line-height: 40rpx;
}
.bubble-content--rich /deep/ p,
.bubble-content--rich /deep/ blockquote,
.bubble-content--rich /deep/ ul,
.bubble-content--rich /deep/ pre,
.bubble-content--rich /deep/ h1,
.bubble-content--rich /deep/ h2,
.bubble-content--rich /deep/ h3 {
  margin: 0 0 14rpx;
}
.bubble-content--rich /deep/ table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 14rpx;
  table-layout: fixed;
}
.bubble-content--rich /deep/ th,
.bubble-content--rich /deep/ td {
  border: 1rpx solid #d8dde3;
  padding: 10rpx 12rpx;
  font-size: 28rpx;
  line-height: 40rpx;
  vertical-align: top;
  word-break: break-all;
}
.bubble-content--rich /deep/ th {
  background: #f4f6f8;
  font-weight: 600;
}
.bubble-content--rich /deep/ p:last-child,
.bubble-content--rich /deep/ ul:last-child,
.bubble-content--rich /deep/ pre:last-child,
.bubble-content--rich /deep/ blockquote:last-child,
.bubble-content--rich /deep/ table:last-child {
  margin-bottom: 0;
}
.bubble-content--rich /deep/ ul {
  padding-left: 34rpx;
}
.bubble-content--rich /deep/ li {
  margin: 8rpx 0;
}
.bubble-content--rich /deep/ blockquote {
  padding: 8rpx 14rpx;
  border-left: 6rpx solid #d5d7db;
  color: #555;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8rpx;
}
.bubble-content--rich /deep/ pre {
  padding: 14rpx;
  border-radius: 12rpx;
  background: #f6f8fa;
  overflow: auto;
}
.bubble-content--rich /deep/ code {
  font-size: 26rpx;
  font-family: Menlo, Monaco, Consolas, 'Courier New', monospace;
}
.bubble-content--rich /deep/ .md-inline-code {
  padding: 2rpx 8rpx;
  border-radius: 8rpx;
  background: rgba(0, 0, 0, 0.06);
}
.bubble-content--rich /deep/ .md-link {
  color: #1677ff;
  text-decoration: underline;
}
.bubble-content--rich /deep/ h1,
.bubble-content--rich /deep/ h2,
.bubble-content--rich /deep/ h3 {
  font-weight: 700;
}
.bubble-content--rich /deep/ h1 {
  font-size: 38rpx;
}
.bubble-content--rich /deep/ h2 {
  font-size: 34rpx;
}
.bubble-content--rich /deep/ h3 {
  font-size: 32rpx;
}
.user {
  background: #007aff;
  color: #fff;
  align-self: flex-end;
  margin-left: auto;
  max-width: 80%;
}
/* 助手回复通常较长：横向铺满屏幕，抵消 msg-list 左右 padding，右侧不留大块空白 */
.ai {
  background: #fff;
  color: #222;
  align-self: stretch;
  max-width: none;
  width: calc(100% + 40rpx);
  margin-left: -20rpx;
  margin-right: -20rpx;
  border-radius: 0;
}
.msg-meta {
  align-self: flex-end;
  margin-left: auto;
  padding: 4rpx 0 8rpx;
  font-size: 24rpx;
  color: #888;
}
.msg-meta-text {
  color: #888;
}
.retry-link {
  color: #007aff;
}
.input-bar {
  flex-shrink: 0;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: #f5f6f8;
  border-top: 1rpx solid #e8eaed;
  box-sizing: border-box;
}
.readonly-tip {
  flex-shrink: 0;
  margin: 0 24rpx 12rpx;
  padding: 14rpx 18rpx;
  border-radius: 12rpx;
  background: #fff6e6;
  color: #8a5a00;
  font-size: 24rpx;
}
.input-shell {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  background: #ffffff;
  border-radius: 36rpx;
  border: 1rpx solid #e8eaed;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  padding: 14rpx 14rpx 14rpx 28rpx;
  gap: 12rpx;
}
.input-text {
  flex: 1;
  min-height: 80rpx;
  max-height: 280rpx;
  overflow-y: auto;
  padding: 10rpx 0;
  font-size: 30rpx;
  line-height: 44rpx;
  color: #1a1a1a;
  box-sizing: border-box;
  width: 100%;
}
.send-fab {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  margin: 0;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: linear-gradient(145deg, #2b8cff 0%, #1677ff 100%);
  line-height: 1;
}
.send-fab::after {
  border: none;
}
.send-fab--disabled {
  background: #c5d4e8;
  opacity: 0.95;
}
.send-fab--hover {
  opacity: 0.88;
}
.send-fab--disabled.send-fab--hover {
  opacity: 0.95;
}
</style>
