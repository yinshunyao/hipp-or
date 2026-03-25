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
 * 微信小程序：分块接收 Dify 透传的 SSE，通过 onDelta 回传当前累积的助手全文。
 * 非微信环境或失败时返回 false，调用方应回退到 sendChatMessage。
 *
 * @param {number} sessionId
 * @param {string} query
 * @param {(fullText: string) => void} onDelta
 * @returns {Promise<{ topicClosed: boolean }>} 流式完成时返回是否话题已归档
 */
export function sendChatMessageStream(sessionId, query, onDelta) {
  // #ifdef MP-WEIXIN
  return new Promise((resolve, reject) => {
    const token = getToken()
    const acc = createDifySseTextAccumulator()
    const decoder = new TextDecoder('utf-8')
    const url = `${config.baseUrl}/mp/chat/sessions/${sessionId}/messages/stream`
    const task = uni.request({
      url,
      method: 'POST',
      header: {
        'Content-Type': 'application/json',
        Authorization: token || ''
      },
      data: { query },
      timeout: 300000,
      enableChunked: true,
      success(res) {
        const text = acc.end()
        onDelta && onDelta(text)
        const topicClosed = acc.getTopicClosed()
        const headers = res.header || {}
        const contentType = String(headers['content-type'] || headers['Content-Type'] || '').toLowerCase()
        if (res.statusCode >= 200 && res.statusCode < 300 && contentType.includes('text/event-stream')) {
          resolve({ topicClosed })
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          let bodyText = ''
          try {
            if (typeof res.data === 'string') {
              bodyText = res.data
            } else {
              bodyText = decoder.decode(res.data || new ArrayBuffer(0), { stream: false })
            }
            const payload = JSON.parse(bodyText)
            reject(new Error(payload.message || '发送失败'))
            return
          } catch (e) {
            reject(new Error('发送失败'))
            return
          }
        }
        reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail(err) {
        reject(err)
      }
    })
    if (!task || typeof task.onChunkReceived !== 'function') {
      if (task && typeof task.abort === 'function') {
        task.abort()
      }
      reject(new Error('no chunked'))
      return
    }
    task.onChunkReceived((res) => {
      const chunk = decoder.decode(res.data, { stream: true })
      const text = acc.push(chunk)
      onDelta && onDelta(text)
    })
  })
  // #endif
  // #ifndef MP-WEIXIN
  return Promise.reject(new Error('no stream'))
  // #endif
}
