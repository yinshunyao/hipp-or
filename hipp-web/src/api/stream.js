function transient(message) {
  const error = new Error(message)
  error.transient = true
  return error
}

export function sendChatMessageStream(sessionId, query, onDelta, files, onAccepted) {
  return new Promise((resolve, reject) => {
    const raw = String(localStorage.getItem('hipp_web_token') || '').replace(/^bearer\s+/i, '').trim()
    if (!raw) {
      reject(new Error('请先登录'))
      return
    }
    const base = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${proto}//${location.host}${base}/mp/chat/sessions/${sessionId}/messages/ws?token=${encodeURIComponent(raw)}`
    let ws
    try {
      ws = new WebSocket(url)
    } catch (err) {
      reject(transient('no stream'))
      return
    }
    let done = false
    let sent = false
    let fullText = ''
    const idleMs = 5 * 60 * 1000
    const absoluteMs = 20 * 60 * 1000
    const startedAt = Date.now()
    let idleTimer = 0
    function armIdle() {
      if (done) return
      clearTimeout(idleTimer)
      const left = absoluteMs - (Date.now() - startedAt)
      if (left <= 0) {
        finish(transient('响应超时'))
        return
      }
      idleTimer = setTimeout(() => finish(transient('响应超时')), Math.min(idleMs, left))
    }
    function finish(err, payload) {
      if (done) return
      done = true
      clearTimeout(idleTimer)
      try { ws.close() } catch (e) { /* ignore */ }
      if (err) reject(err)
      else resolve(payload || { topicClosed: false })
    }
    armIdle()
    ws.onerror = () => finish(transient('no stream'))
    ws.onclose = () => { if (!done) finish(transient('连接中断')) }
    ws.onmessage = (ev) => {
      armIdle()
      let msg
      try { msg = JSON.parse(ev.data) } catch (e) { return }
      const event = msg.event
      if (event === 'delta' || event === 'message' || event === 'agent_message') {
        if (typeof msg.full_text === 'string') fullText = msg.full_text
        else if (typeof msg.answer === 'string' && msg.answer) fullText += msg.answer
        if (onDelta) onDelta(fullText)
        return
      }
      if (event === 'ready') {
        if (sent) return
        sent = true
        const payload = { query: query || '' }
        if (files && files.length) payload.files = files
        ws.send(JSON.stringify(payload))
        if (typeof onAccepted === 'function') onAccepted()
        return
      }
      if (event === 'done') {
        if (onDelta) onDelta(fullText)
        finish(null, { topicClosed: !!msg.topic_closed })
        return
      }
      if (event === 'error') {
        const error = new Error(msg.message || '发送失败')
        if (msg.code != null) error.code = Number(msg.code)
        finish(error)
      }
    }
  })
}
