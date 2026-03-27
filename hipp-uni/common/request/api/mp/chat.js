import config from '@/config.js'
import { getToken } from '@/common/utils/auth.js'
import request from '@/common/request/request.js'

/** 收件箱；对话 Tab 传 kind=session 仅已归档会话行，不含智能体入口行 */
export function getChatInbox(q) {
  return request.get('/mp/chat/inbox', {
    params: { q: q || undefined, kind: 'session' }
  })
}

/** 人工客服收件箱（分配给我的会话） */
export function getStaffChatInbox(q) {
  return request.get('/mp/chat/inbox', {
    params: { q: q || undefined, kind: 'staff' }
  })
}

/**
 * 某智能体下已归档话题分页（时间正序片段：页内旧→新，页尾靠近当前会话）
 * @param {number} agentId
 * @param {{ limit?: number, before_update_ts?: number, before_session_id?: number }} params
 */
export function getArchivedTopics(agentId, params = {}) {
  const q = { limit: params.limit || 20 }
  if (params.before_update_ts != null && params.before_session_id != null) {
    q.before_update_ts = params.before_update_ts
    q.before_session_id = params.before_session_id
  }
  return request.get(`/mp/chat/agents/${agentId}/archived-topics`, { params: q })
}

/** 创建会话 */
export function createChatSession(agentId) {
  return request.post('/mp/chat/sessions', { agent_id: agentId })
}

/**
 * 场景页解析可服务智能体（按类型随机 1 个，后端可选返回进行中会话）
 * @param {'requirement'|'business'} scene
 */
export function resolveSceneAgent(scene) {
  return request.get('/mp/chat/scene-agent', { params: { scene } })
}

/** 从已归档话题发起人工客服（创建或复用会话） */
export function createHumanSupportSession(sourceSessionId) {
  return request.post('/mp/chat/human-support/sessions', { source_session_id: sourceSessionId })
}

/** 会话详情 */
export function getChatSession(sessionId) {
  return request.get(`/mp/chat/sessions/${sessionId}`)
}

/** 更新会话 */
export function patchChatSession(sessionId, data) {
  return request.request({
    url: `/mp/chat/sessions/${sessionId}`,
    method: 'PATCH',
    data
  })
}

/** 删除会话 */
export function deleteChatSession(sessionId) {
  return request.delete(`/mp/chat/sessions/${sessionId}`)
}

/** 消息列表 */
export function getChatMessages(sessionId, page, limit) {
  return request.get(`/mp/chat/sessions/${sessionId}/messages`, {
    params: { page, limit }
  })
}

/** 发送消息（blocking） */
export function sendChatMessage(sessionId, query) {
  return request.post(`/mp/chat/sessions/${sessionId}/messages`, { query })
}

/**
 * Dify SSE 增量解析：将分片拼入行缓冲，对完整行解析 `data:` JSON，累积 assistant 文本；
 * 识别服务端扩展事件 `mp_topic`（话题归档）。
 */
export function createDifySseTextAccumulator() {
  let lineBuf = ''
  let fullText = ''
  let topicClosed = false
  function consumeLine(line) {
    const s = line.replace(/\r$/, '')
    if (!s.startsWith('data:')) return
    const raw = s.slice(5).trim()
    if (raw === '[DONE]') return
    try {
      const obj = JSON.parse(raw)
      if (obj.event === 'mp_topic') {
        topicClosed = !!obj.topic_closed
        return
      }
      if (
        (obj.event === 'message' || obj.event === 'agent_message') &&
        typeof obj.answer === 'string' &&
        obj.answer
      ) {
        fullText += obj.answer
      }
    } catch (e) {
      // ignore bad json line
    }
  }
  return {
    /** @param {string} decodedChunk */
    push(decodedChunk) {
      lineBuf += decodedChunk
      const parts = lineBuf.split('\n')
      lineBuf = parts.pop() || ''
      for (const line of parts) {
        consumeLine(line)
      }
      return fullText
    },
    end() {
      if (lineBuf.trim()) {
        consumeLine(lineBuf)
        lineBuf = ''
      }
      return fullText
    },
    getTopicClosed() {
      return topicClosed
    }
  }
}

/**
 * 微信小程序 WebSocket 流式发送。
 * 非微信环境或失败时 reject，调用方应回退到 sendChatMessage。
 *
 * @param {number} sessionId
 * @param {string} query
 * @param {(fullText: string) => void} onDelta
 * @returns {Promise<{ topicClosed: boolean }>}
 */
export function sendChatMessageStream(sessionId, query, onDelta) {
  // #ifdef MP-WEIXIN
  return new Promise((resolve, reject) => {
    if (typeof uni === 'undefined' || typeof uni.connectSocket !== 'function') {
      return reject(new Error('no stream'))
    }
    const rawToken = String(getToken() || '')
    const jwtToken = rawToken.replace(/^bearer\s+/i, '').trim()
    const wsBase = String(config.baseUrl || '')
      .replace(/^http:\/\//i, 'ws://')
      .replace(/^https:\/\//i, 'wss://')
    if (!/^wss?:\/\//i.test(wsBase)) {
      return reject(new Error('bad ws base'))
    }
    const url = `${wsBase}/mp/chat/sessions/${sessionId}/messages/ws?token=${encodeURIComponent(jwtToken)}`
    const tag = '[WS:' + sessionId + ']'
    console.log(tag, 'connecting', url.slice(0, 100))

    let done = false
    let sent = false
    let fullText = ''
    let hasServerMsg = false
    let timeoutId = null

    const finish = (err, payload) => {
      if (done) return
      done = true
      if (timeoutId) { clearTimeout(timeoutId); timeoutId = null }
      console.log(tag, err ? 'FINISH:ERR ' + err.message : 'FINISH:OK')
      try { socketTask.close({}) } catch (_) {}
      err ? reject(err) : resolve(payload || { topicClosed: false })
    }

    const decodeData = (d) => {
      if (typeof d === 'string') return d
      if (d && typeof ArrayBuffer !== 'undefined' && d instanceof ArrayBuffer) {
        try { return new TextDecoder('utf-8').decode(d) } catch (_) {}
        const a = new Uint8Array(d)
        let s = ''
        for (let i = 0; i < a.length; i++) s += String.fromCharCode(a[i])
        return s
      }
      try { return JSON.stringify(d) } catch (_) { return '' }
    }

    const dispatch = (msg) => {
      if (!msg || typeof msg !== 'object') return false
      const ev = msg.event
      if (ev === 'delta' || ev === 'message' || ev === 'agent_message') {
        if (typeof msg.full_text === 'string') fullText = msg.full_text
        else if (typeof msg.answer === 'string' && msg.answer) fullText += msg.answer
        onDelta && onDelta(fullText)
        return true
      }
      if (ev === 'ready') {
        console.log(tag, 'got ready -> doSend')
        doSend()
        return true
      }
      if (ev === 'done') {
        console.log(tag, 'got done, topicClosed=' + !!msg.topic_closed)
        onDelta && onDelta(fullText)
        finish(null, { topicClosed: !!msg.topic_closed })
        return true
      }
      if (ev === 'error') {
        console.log(tag, 'got error:', msg.message)
        finish(new Error(msg.message || 'stream error'))
        return true
      }
      return false
    }

    const queryPayload = JSON.stringify({ query })

    const doSend = () => {
      if (done || sent) return
      console.log(tag, 'doSend', queryPayload.length, 'bytes')
      try {
        socketTask.send({
          data: queryPayload,
          success() { sent = true; console.log(tag, 'send OK') },
          fail(e) {
            console.log(tag, 'send FAIL', e && e.errMsg)
            setTimeout(() => {
              if (done || sent) return
              console.log(tag, 'send retry#1')
              try {
                socketTask.send({
                  data: queryPayload,
                  success() { sent = true; console.log(tag, 'retry#1 OK') },
                  fail(e2) {
                    console.log(tag, 'retry#1 FAIL', e2 && e2.errMsg)
                    setTimeout(() => {
                      if (done || sent) return
                      console.log(tag, 'send retry#2')
                      try {
                        socketTask.send({
                          data: queryPayload,
                          success() { sent = true; console.log(tag, 'retry#2 OK') },
                          fail() { console.log(tag, 'retry#2 FAIL, giving up send') }
                        })
                      } catch (_) {}
                    }, 500)
                  }
                })
              } catch (_) {}
            }, 300)
          }
        })
      } catch (ex) {
        console.log(tag, 'send threw', ex)
      }
    }

    // 1. 创建连接
    let socketTask
    try {
      socketTask = uni.connectSocket({ url, success() {}, fail() {} })
    } catch (e) {
      return reject(new Error('ws open failed'))
    }
    if (!socketTask) {
      return reject(new Error('no socket task'))
    }

    // 2. 立即注册全部事件（必须紧跟 connectSocket，避免竞态丢 onOpen）
    socketTask.onOpen(() => {
      console.log(tag, 'onOpen')
      doSend()
    })

    socketTask.onMessage((evt) => {
      const raw = decodeData(evt && evt.data)
      if (!raw) return
      hasServerMsg = true
      console.log(tag, 'onMsg', raw.length > 200 ? raw.slice(0, 200) + '...' : raw)
      try { if (dispatch(JSON.parse(raw))) return } catch (_) {}
      const lines = raw.split('\n')
      for (const ln of lines) {
        const t = ln.trim()
        if (!t.startsWith('data:')) continue
        const p = t.slice(5).trim()
        if (!p || p === '[DONE]') continue
        try { if (dispatch(JSON.parse(p))) return } catch (_) {}
      }
    })

    socketTask.onError((e) => {
      console.log(tag, 'onError', e && e.errMsg)
      if (!hasServerMsg) finish(new Error((e && e.errMsg) || 'ws error'))
    })

    socketTask.onClose((e) => {
      console.log(tag, 'onClose code=' + (e && e.code), 'reason=' + (e && e.reason))
      if (done) return
      if (hasServerMsg) {
        onDelta && onDelta(fullText)
        finish(null, { topicClosed: false })
        return
      }
      finish(new Error('ws closed unexpectedly'))
    })

    // 3. 超时保护
    timeoutId = setTimeout(() => finish(new Error('ws timeout 5min')), 300000)
  })
  // #endif
  // #ifndef MP-WEIXIN
  return Promise.reject(new Error('no stream'))
  // #endif
}
