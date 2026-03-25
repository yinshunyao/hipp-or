import request from '@/config/axios'

export interface MpInboxOut {
  items: Array<{
    kind: string
    session?: {
      id: number
      display_title?: string
      title?: string
      last_message_preview?: string
    }
    agent?: { id: number; name?: string }
  }>
}

export const getMpStaffInboxApi = (q?: string) => {
  return request.get<MpInboxOut>({
    url: '/mp/chat/inbox',
    params: { kind: 'staff', q: q || undefined }
  })
}

export const getMpChatSessionApi = (sessionId: number) => {
  return request.get({ url: `/mp/chat/sessions/${sessionId}` })
}

export const getMpChatMessagesApi = (sessionId: number, page = 1, limit = 100) => {
  return request.get({
    url: `/mp/chat/sessions/${sessionId}/messages`,
    params: { page, limit }
  })
}

export const postMpChatMessageApi = (sessionId: number, query: string) => {
  return request.post({
    url: `/mp/chat/sessions/${sessionId}/messages`,
    data: { query }
  })
}
