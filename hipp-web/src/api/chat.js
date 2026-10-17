import { http } from './http'

export function getChatInbox(q) {
  return http.get('/mp/chat/inbox', { params: { q: q || undefined, kind: 'session', include_open: 1 } })
}

export function getStaffChatInbox(q) {
  return http.get('/mp/chat/inbox', { params: { q: q || undefined, kind: 'staff' } })
}

export function getArchivedTopics(agentId, params = {}) {
  const q = { limit: params.limit || 20 }
  if (params.before_update_ts != null && params.before_session_id != null) {
    q.before_update_ts = params.before_update_ts
    q.before_session_id = params.before_session_id
  }
  return http.get(`/mp/chat/agents/${agentId}/archived-topics`, { params: q })
}

export function createChatSession(agentId) {
  return http.post('/mp/chat/sessions', { agent_id: agentId })
}

/** 进入空草稿 / 复用「新会话」前预检咨询费余额（46005/46006）。 */
export function sessionFeePrecheck() {
  return http.get('/mp/chat/session-fee-precheck')
}

export function resolveSceneAgent(scene) {
  return http.get('/mp/chat/scene-agent', { params: { scene } })
}

export function createHumanSupportSession(sourceSessionId) {
  return http.post('/mp/chat/human-support/sessions', { source_session_id: sourceSessionId })
}

export function getChatSession(sessionId) {
  return http.get(`/mp/chat/sessions/${sessionId}`)
}

export function patchChatSession(sessionId, data) {
  return http.patch(`/mp/chat/sessions/${sessionId}`, data)
}

export function deleteChatSession(sessionId) {
  return http.delete(`/mp/chat/sessions/${sessionId}`)
}

export function createChatShare(sessionId) {
  return http.post(`/mp/chat/sessions/${sessionId}/share`, {})
}

export function deleteChatShare(sessionId) {
  return http.delete(`/mp/chat/sessions/${sessionId}/share`)
}

export function getSharedChat(token) {
  return http.get(`/mp/chat/share/${encodeURIComponent(token)}`, { skipToast: true })
}

export function getChatMessages(sessionId, page, limit) {
  return http.get(`/mp/chat/sessions/${sessionId}/messages`, { params: { page, limit } })
}

export function sendChatMessage(sessionId, query, files) {
  const body = { query: query || '' }
  if (files && files.length) body.files = files
  return http.post(`/mp/chat/sessions/${sessionId}/messages`, body)
}

export function uploadChatFile(file, sessionId) {
  const form = new FormData()
  form.append('file', file)
  if (sessionId != null) form.append('session_id', String(sessionId))
  return http.postForm('/mp/chat/upload', form)
}

export function deleteChatUpload(url) {
  return http.delete('/mp/chat/upload', { data: { url }, skipToast: true })
}

export function audioToText(file, sessionId) {
  const form = new FormData()
  form.append('file', file)
  form.append('session_id', String(sessionId))
  return http.postForm('/mp/chat/audio-to-text', form)
}
