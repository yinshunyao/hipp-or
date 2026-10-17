<template>
  <section class="pane">
    <header class="head">
      <div>
        <p class="kicker">{{ kicker }}</p>
        <h1>{{ title }}</h1>
      </div>
      <slot name="extra" />
    </header>
    <p v-if="banner" class="banner">{{ banner }}</p>
    <div ref="scroller" class="stream" @scroll="onScroll">
      <p v-if="!timeline.length" class="empty">{{ emptyHint }}</p>
      <article v-for="(item, index) in timeline" :key="item.localId || item.id || index" class="msg">
        <button
          v-if="item.kind === 'archive'"
          class="archive"
          type="button"
          @click="$emit('archive', item.sessionId)"
        >
          <Icon name="box" />{{ item.title }}
        </button>
        <p v-else-if="item.role === 'system' && !human" class="sys">{{ item.content }}</p>
        <button
          v-else-if="item.role === 'system'"
          class="archive"
          type="button"
          @click="$emit('source')"
        >
          <Icon name="box" />{{ archiveTitle(item.content) }}
        </button>
        <div v-else :class="['bubble', bubbleSide(item)]">
          <div v-if="item.attachments && item.attachments.length" class="atts">
            <template v-for="(att, ai) in item.attachments" :key="`${item.localId || item.id}-a-${ai}`">
              <a v-if="att.type === 'image'" class="att-img" :href="att.url" target="_blank" rel="noopener">
                <img :src="att.url" :alt="att.name || '图片'" />
              </a>
              <a v-else class="att-file" :href="att.url" target="_blank" rel="noopener">{{ att.name || '文件' }}</a>
            </template>
          </div>
          <p v-if="item.live && !item.content" class="think">正在回复<i /><i /><i /></p>
          <p v-else-if="plain(item) && item.content" class="plain">{{ item.content }}<i v-if="item.live" class="caret" /></p>
          <div v-else-if="!plain(item)" class="md-wrap">
            <template v-for="(part, pi) in assistantParts(item.content)" :key="`${item.localId || item.id || index}-${pi}`">
              <div v-if="part.kind === 'think'" class="think-fold">
                <button
                  class="think-sum"
                  type="button"
                  :aria-expanded="isThinkOpen(item, index, pi) ? 'true' : 'false'"
                  @click="toggleThink(item, index, pi)"
                >
                  <Icon name="chev" class="chev" :class="{ on: isThinkOpen(item, index, pi) }" />
                  {{ thinkLabel(item, index, pi, part) }}
                </button>
                <div
                  v-show="isThinkOpen(item, index, pi)"
                  class="think-body md"
                  v-html="part.text.trim() ? renderMarkdown(part.text) : ''"
                />
              </div>
              <div v-else class="md" v-html="renderMarkdown(part.text)" />
            </template>
            <i v-if="item.live" class="caret" />
          </div>
        </div>
        <p v-if="item.kind !== 'archive' && stampText(item)" class="stamp" :class="stampSide(item)">{{ stampText(item) }}</p>
        <p v-if="showSending(item, index)" class="meta">发送中…</p>
        <button v-else-if="item.sendStatus === 'failed'" class="meta link" type="button" @click="$emit('retry', sourceIndex(item))">
          重试
        </button>
      </article>
    </div>
    <div v-if="notice || showHuman" class="notice-row">
      <p v-if="notice" class="notice">{{ notice }}</p>
      <button v-if="showHuman" class="human" type="button" @click="openAbout()">
        <Icon name="mail" />
        联系我们
      </button>
    </div>
    <form
      v-if="!bare"
      class="composer"
      :class="{ 'is-drag': dragOver && canAttach }"
      @submit.prevent="submit"
      @dragenter="onDragEnter"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <div v-if="dragOver && canAttach" class="drop-mask" aria-hidden="true">松开以添加图片或文件</div>
      <div v-if="pending.length" class="pending">
        <div v-for="(p, i) in pending" :key="p.key" class="chip">
          <img v-if="p.preview" :src="p.preview" alt="" />
          <span>{{ p.name }}</span>
          <button type="button" aria-label="移除" @click="removePending(i)">×</button>
        </div>
      </div>
      <div class="composer-row">
        <input ref="fileInput" class="hidden" type="file" multiple accept="image/*,.pdf,.txt,.md,.doc,.docx,.xls,.xlsx,.csv" @change="onPickFiles" />
        <button
          v-if="canAttach"
          class="tool"
          type="button"
          :disabled="disabled || sending || !sessionId"
          aria-label="附件"
          @click="pickFiles"
        >
          <Icon name="attach" />
        </button>
        <button
          v-if="canAttach && voiceInputEnabled"
          class="tool"
          type="button"
          :disabled="disabled || sending || !sessionId || voiceBusy"
          :aria-label="recording ? '停止录音' : '语音输入'"
          @click="toggleVoice"
        >
          <Icon name="mic" />
        </button>
        <textarea
          v-model="draft"
          :placeholder="attachHint"
          :disabled="disabled"
          rows="1"
          maxlength="4000"
          @keydown="onKey"
          @paste="onPaste"
        />
        <button class="send" type="submit" :disabled="disabled || sending || (!draft.trim() && !pending.length)" aria-label="发送">
          <Icon name="send" />
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { computed, inject, nextTick, onUnmounted, reactive, ref, watch } from 'vue'
import Icon from '@/components/Icon.vue'
import { audioToText, deleteChatUpload, uploadChatFile } from '@/api/chat'
import { assertAttachList, classifyLocalFile, collectTransferFiles, toSendFiles } from '@/utils/chatAttach'
import { renderMarkdown, splitAssistantParts } from '@/utils/markdown'
import { toast } from '@/utils/toast'

const props = defineProps({
  title: { type: String, default: '对话' },
  kicker: { type: String, default: '会话' },
  messages: { type: Array, default: () => [] },
  archived: { type: Array, default: () => [] },
  placeholder: { type: String, default: '输入你的问题…' },
  disabled: { type: Boolean, default: false },
  sending: { type: Boolean, default: false },
  notice: { type: String, default: '' },
  banner: { type: String, default: '' },
  showHuman: { type: Boolean, default: false },
  human: { type: Boolean, default: false },
  staff: { type: Boolean, default: false },
  emptyHint: { type: String, default: '从下面的输入框开始这次咨询。' },
  bare: { type: Boolean, default: false },
  sessionId: { type: [Number, String], default: null },
  allowAttach: { type: Boolean, default: true }
})
const emit = defineEmits(['send', 'retry', 'archive', 'source', 'reach-top'])
const openAbout = inject('openAbout', () => {})

const draft = ref('')
const pending = ref([])
const fileInput = ref(null)
const scroller = ref(null)
const follow = ref(true)
const thinkOpen = reactive({})
const thinkClock = reactive({})
const thinkNow = ref(Date.now())
/** 语音输入暂有问题，先隐藏入口；修好后改为 true */
const voiceInputEnabled = false
const recording = ref(false)
const voiceBusy = ref(false)
const dragOver = ref(false)
let dragDepth = 0
let mediaRecorder = null
let mediaChunks = []
let thinkTick = null
const timeline = computed(() => [...props.archived, ...props.messages])
const canAttach = computed(() => !!(props.allowAttach && !props.human && !props.bare))
const attachHint = computed(() => props.placeholder)

function assistantParts(content) {
  return splitAssistantParts(content)
}
function thinkKey(item, index, pi) {
  return `${item.localId || item.id || index}:${pi}`
}
function isThinkOpen(item, index, pi) {
  return !!thinkOpen[thinkKey(item, index, pi)]
}
function toggleThink(item, index, pi) {
  const key = thinkKey(item, index, pi)
  thinkOpen[key] = !thinkOpen[key]
}
function formatThinkSec(ms) {
  return (Math.max(0, ms) / 1000).toFixed(1)
}
function thinkLabel(item, index, pi, part) {
  const key = thinkKey(item, index, pi)
  const live = !!(item && (item.live || item.streaming))
  let clock = thinkClock[key]
  if (!clock && (live || !part.closed)) {
    clock = { start: Date.now(), end: null }
    thinkClock[key] = clock
  }
  if (clock && part.closed && clock.end == null) clock.end = Date.now()
  if (!clock) return part.closed ? '深度思考' : '深度思考中...'
  const ms = (clock.end == null ? thinkNow.value : clock.end) - clock.start
  const sec = formatThinkSec(ms)
  return part.closed ? `深度思考 (${sec}s)` : `深度思考中...(${sec}s)`
}
function syncThinkTicker() {
  const running = timeline.value.some((item) => {
    if (!item || item.role === 'user' || item.role === 'system' || item.kind === 'archive') return false
    if (!(item.live || item.streaming)) return false
    return assistantParts(item.content).some((part) => part.kind === 'think' && !part.closed)
  })
  if (running && !thinkTick) {
    thinkTick = setInterval(() => { thinkNow.value = Date.now() }, 100)
  } else if (!running && thinkTick) {
    clearInterval(thinkTick)
    thinkTick = null
    thinkNow.value = Date.now()
  }
}
watch(timeline, () => { syncThinkTicker() }, { deep: true })
onUnmounted(() => {
  if (thinkTick) clearInterval(thinkTick)
})

function plain(item) {
  if (props.staff) return true
  return item.role === 'user'
}
function bubbleSide(item) {
  if (props.staff) return item.role === 'assistant' ? 'mine' : 'peer'
  return item.role === 'user' ? 'mine' : 'peer'
}
function sourceIndex(item) {
  return props.messages.indexOf(item)
}
function showSending(item, index) {
  if (!item || item.sendStatus !== 'sending') return false
  const next = timeline.value[index + 1]
  if (next && next.role === 'assistant' && (next.live || String(next.content || '').trim())) return false
  return true
}
function stampText(item) {
  if (!item || !item.at) return ''
  const date = new Date(String(item.at).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
function stampSide(item) {
  if (item.role === 'system') return 'center'
  return bubbleSide(item)
}
function archiveTitle(content) {
  const matched = String(content || '').match(/^【归档话题】([^\r\n]+)/)
  return (matched && matched[1].trim()) || '未命名话题'
}
function pickFiles() {
  if (!canAttach.value || props.disabled) return
  if (fileInput.value) fileInput.value.click()
}
async function removePending(index) {
  const row = pending.value[index]
  if (!row) return
  if (row.preview) URL.revokeObjectURL(row.preview)
  pending.value.splice(index, 1)
  if (row.url) {
    try {
      await deleteChatUpload(row.url)
    } catch (_) {
      /* 最佳努力：列表已移除 */
    }
  }
}
async function ingestFiles(rawFiles) {
  if (!canAttach.value || props.disabled || !props.sessionId) {
    if (!props.sessionId) toast('会话未就绪，请稍后再试')
    return
  }
  const files = Array.from(rawFiles || []).filter(Boolean)
  if (!files.length) return
  for (const file of files) {
    const kind = classifyLocalFile(file)
    if (!kind) {
      toast(`不支持的文件类型：${file.name || '未知'}`)
      continue
    }
    try {
      assertAttachList(pending.value, { type: kind, size: file.size })
    } catch (err) {
      toast(err.message || '附件超限')
      break
    }
    voiceBusy.value = true
    try {
      const res = await uploadChatFile(file, props.sessionId)
      const data = (res && res.data) || {}
      pending.value.push({
        key: `${Date.now()}-${Math.random()}`,
        type: data.type || kind,
        url: data.url,
        name: data.name || file.name,
        size: data.size || file.size,
        mime: data.mime || file.type || '',
        preview: kind === 'image' ? URL.createObjectURL(file) : ''
      })
    } catch (err) {
      /* toast 已由 http 处理 */
    } finally {
      voiceBusy.value = false
    }
  }
}
async function onPickFiles(event) {
  const files = Array.from((event.target && event.target.files) || [])
  if (event.target) event.target.value = ''
  await ingestFiles(files)
}
function onPaste(event) {
  if (!canAttach.value || props.disabled) return
  const files = collectTransferFiles(event.clipboardData)
  if (!files.length) return
  event.preventDefault()
  const text = event.clipboardData && event.clipboardData.getData('text/plain')
  if (text) {
    const insert = String(text)
    const el = event.target
    if (el && typeof el.selectionStart === 'number') {
      const start = el.selectionStart
      const end = el.selectionEnd
      const cur = draft.value || ''
      draft.value = cur.slice(0, start) + insert + cur.slice(end)
    } else {
      draft.value = draft.value ? `${draft.value}${insert}` : insert
    }
  }
  ingestFiles(files)
}
function onDragEnter(event) {
  if (!canAttach.value || props.disabled) return
  event.preventDefault()
  dragDepth += 1
  dragOver.value = true
}
function onDragOver(event) {
  if (!canAttach.value || props.disabled) return
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy'
  dragOver.value = true
}
function onDragLeave(event) {
  if (!canAttach.value) return
  event.preventDefault()
  dragDepth = Math.max(0, dragDepth - 1)
  if (dragDepth === 0) dragOver.value = false
}
function onDrop(event) {
  if (!canAttach.value || props.disabled) return
  event.preventDefault()
  dragDepth = 0
  dragOver.value = false
  const files = collectTransferFiles(event.dataTransfer)
  if (!files.length) {
    toast('未识别到可上传的文件')
    return
  }
  ingestFiles(files)
}
async function toggleVoice() {
  if (props.disabled || !props.sessionId) return
  if (recording.value) {
    recording.value = false
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop()
    return
  }
  if (!navigator.mediaDevices || !window.MediaRecorder) {
    toast('当前浏览器不支持录音')
    return
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaChunks = []
    mediaRecorder = new MediaRecorder(stream)
    mediaRecorder.ondataavailable = (ev) => {
      if (ev.data && ev.data.size) mediaChunks.push(ev.data)
    }
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop())
      const blob = new Blob(mediaChunks, { type: mediaRecorder.mimeType || 'audio/webm' })
      mediaChunks = []
      if (!blob.size) return
      voiceBusy.value = true
      try {
        const file = new File([blob], 'voice.webm', { type: blob.type || 'audio/webm' })
        const res = await audioToText(file, props.sessionId)
        const text = (res.data && res.data.text) || ''
        if (text) {
          draft.value = draft.value ? `${draft.value.trim()} ${text}` : text
        } else toast('未识别到语音')
      } catch (err) {
        /* toast 已处理 */
      } finally {
        voiceBusy.value = false
      }
    }
    mediaRecorder.start()
    recording.value = true
  } catch (err) {
    toast('无法使用麦克风')
  }
}
async function submit() {
  const text = draft.value.trim()
  if (props.disabled || props.sending) return
  if (!text && !pending.value.length) return
  const files = toSendFiles(pending.value)
  draft.value = ''
  pending.value.forEach((p) => { if (p.preview) URL.revokeObjectURL(p.preview) })
  pending.value = []
  emit('send', { text, files })
}
function onKey(event) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    submit()
  }
}
function onScroll() {
  const el = scroller.value
  if (!el) return
  follow.value = el.scrollHeight - el.scrollTop - el.clientHeight < 80
  if (el.scrollTop < 36) emit('reach-top')
}
async function stickBottom(force) {
  await nextTick()
  const el = scroller.value
  if (el && (force || follow.value)) el.scrollTop = el.scrollHeight
}
watch(() => props.messages.map((m) => `${m.role}:${m.content}:${m.sendStatus}:${m.live ? 1 : 0}`).join('|'), (value, prev) => {
  const grew = String(value).split('|').length > String(prev || '').split('|').length
  if (grew) follow.value = true
  stickBottom(grew)
})
watch(() => props.archived.length, stickBottom)
</script>

<style scoped>
.pane {
  flex: 1;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(520px 220px at 100% 0%, rgba(198, 161, 90, 0.16), transparent 60%),
    var(--paper);
}
.head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-end;
  padding: 22px 28px 12px;
}
.kicker {
  margin: 0;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 11px;
  color: var(--brass);
  font-family: var(--display);
}
h1 {
  margin: 4px 0 0;
  font-family: var(--serif);
  font-size: 28px;
  line-height: 1.25;
  font-weight: 650;
}
.banner, .notice {
  margin: 0 28px 8px;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(166, 124, 61, 0.12);
  color: var(--text);
  font-size: 13px;
}
.stream {
  flex: 1;
  overflow: auto;
  padding: 8px 8vw 18px;
}
.empty { color: var(--text-3); text-align: center; margin-top: 12vh; }
.msg { display: flex; flex-direction: column; margin: 8px 0; }
.archive, .sys {
  align-self: center;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 680px;
  border: 0;
  background: transparent;
  color: var(--teal);
  text-decoration: underline;
  text-underline-offset: 3px;
  font-size: 13px;
}
.archive :deep(.ico) { width: 14px; height: 14px; }
.sys { text-decoration: none; color: var(--text-3); }
.bubble { max-width: 760px; }
.mine {
  align-self: flex-end;
  background: var(--ink);
  color: #f6f1e8;
  border-radius: 16px 16px 4px 16px;
  padding: 12px 16px;
  box-shadow: 0 10px 24px rgba(20, 32, 43, 0.12);
}
.peer {
  align-self: flex-start;
  max-width: min(760px, 100%);
  background: var(--surface);
  color: var(--text);
  border-radius: 4px 16px 16px 16px;
  padding: 12px 16px;
}
.plain { margin: 0; white-space: pre-wrap; word-break: break-word; }
.think {
  margin: 0;
  color: var(--text-3);
  letter-spacing: 0.04em;
}
.think i, .caret {
  display: inline-block;
  width: 7px;
  height: 1.05em;
  margin-left: 3px;
  border-radius: 2px;
  background: var(--brass);
  vertical-align: text-bottom;
  animation: blink 1s steps(1) infinite;
}
.think i {
  width: 5px;
  height: 5px;
  margin: 0 2px;
  border-radius: 50%;
  vertical-align: middle;
}
.think i:nth-child(2) { animation-delay: 0.2s; }
.think i:nth-child(3) { animation-delay: 0.4s; }
.md-wrap { display: flex; flex-direction: column; align-items: flex-start; }
.think-fold { margin: 0 0 10px; max-width: 760px; }
.think-sum {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 2px 0;
  border: 0;
  background: transparent;
  color: var(--text-3);
  font-size: 13px;
  letter-spacing: 0.06em;
}
.think-sum :deep(.chev) { width: 14px; height: 14px; transition: transform 0.15s ease; }
.chev.on { transform: rotate(90deg); }
.think-body {
  margin-top: 6px;
  padding: 8px 12px;
  border-left: 2px solid var(--line);
  color: var(--text-3);
  font-size: 13px;
}
@keyframes blink {
  50% { opacity: 0; }
}
.stamp {
  margin: 4px 4px 0;
  font-size: 12px;
  color: var(--text-3);
  font-variant-numeric: tabular-nums;
}
.stamp.mine { align-self: flex-end; }
.stamp.peer { align-self: flex-start; }
.stamp.center { align-self: center; }
.meta { align-self: flex-end; margin: 4px 4px 0; color: var(--text-3); font-size: 12px; background: none; border: 0; }
.link { color: var(--brass); }
.notice-row { display: flex; gap: 10px; align-items: center; padding: 0 28px 8px; flex-wrap: wrap; }
.notice { margin: 0; flex: 1; }
.human {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  border-radius: 12px;
  padding: 8px 14px;
  background: var(--brass);
  color: #1a140c;
  font-weight: 650;
}
.human:hover { background: var(--brass-2); }
.atts { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 8px; }
.att-img img {
  display: block;
  max-width: 220px;
  max-height: 160px;
  border-radius: 10px;
  object-fit: cover;
}
.att-file {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.12);
  color: inherit;
  text-decoration: underline;
  text-underline-offset: 3px;
  font-size: 13px;
}
.peer .att-file { background: var(--paper-2); color: var(--teal); }
.composer {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0 28px 22px;
  padding: 10px 12px 10px 14px;
  border-radius: 16px;
  background: var(--surface);
  border: 1px solid transparent;
  box-shadow: 0 8px 24px rgba(20, 32, 43, 0.05);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.composer:focus-within { box-shadow: 0 0 0 3px rgba(166, 124, 61, 0.16); }
.composer.is-drag {
  border-color: rgba(166, 124, 61, 0.55);
  box-shadow: 0 0 0 3px rgba(166, 124, 61, 0.18);
}
.drop-mask {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: rgba(250, 247, 240, 0.92);
  color: var(--teal);
  font-size: 14px;
  letter-spacing: 0.04em;
  pointer-events: none;
}
.composer-row { display: flex; gap: 8px; align-items: flex-end; }
.pending { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 220px;
  padding: 4px 8px;
  border-radius: 10px;
  background: var(--paper-2);
  font-size: 12px;
}
.chip img { width: 28px; height: 28px; border-radius: 6px; object-fit: cover; }
.chip span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chip button { border: 0; background: transparent; color: var(--text-3); cursor: pointer; }
.tool {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--text-2);
}
.tool:hover:not(:disabled) { background: var(--paper-2); color: var(--text); }
.tool:disabled { opacity: 0.45; }
.hidden { display: none; }
textarea {
  flex: 1;
  resize: none;
  border: 0;
  outline: none;
  background: transparent;
  min-height: 44px;
  max-height: 140px;
  padding: 10px 0;
  line-height: 1.5;
}
.send {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 12px;
  background: var(--brass);
  color: #1a140c;
}
.send:hover:not(:disabled) { background: var(--brass-2); }
.send:disabled { background: var(--paper-2); color: var(--text-3); }
.md :deep(p) { margin: 0 0 8px; }
.md :deep(h1), .md :deep(h2), .md :deep(h3) { font-family: var(--serif); margin: 0 0 8px; }
.md :deep(ul) { margin: 0 0 8px; padding-left: 1.2em; }
.md :deep(blockquote) {
  margin: 0 0 8px;
  padding: 8px 12px;
  border-left: 3px solid var(--brass);
  background: rgba(166, 124, 61, 0.08);
}
.md :deep(pre) {
  margin: 0 0 8px;
  padding: 12px;
  overflow: auto;
  border-radius: 12px;
  background: var(--ink);
  color: #f4efe6;
}
.md :deep(code) { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.92em; }
.md :deep(p code), .md :deep(li code) {
  padding: 1px 5px;
  border-radius: 6px;
  background: var(--paper-2);
}
.md :deep(table) { width: 100%; border-collapse: collapse; margin: 0 0 10px; font-size: 14px; }
.md :deep(th), .md :deep(td) { border: 1px solid var(--line); padding: 6px 8px; vertical-align: top; }
.md :deep(th) { background: rgba(166, 124, 61, 0.12); }
.md :deep(a) { color: var(--teal); }

@media (max-width: 860px) {
  .head, .composer { margin-left: 14px; margin-right: 14px; }
  .head { padding-left: 14px; padding-right: 14px; }
  .stream { padding-left: 14px; padding-right: 14px; }
  h1 { font-size: 22px; }
}
</style>
