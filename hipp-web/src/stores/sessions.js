import { defineStore } from 'pinia'
import { getChatInbox } from '@/api/chat'
import { useAuthStore } from '@/stores/auth'

function sceneOf(agent) {
  const text = String((agent && agent.service_type) || '')
  if (text.includes('商业')) return 'business'
  if (text.includes('需求')) return 'requirement'
  return ''
}

function rowTitle(session, agent) {
  const agentName = String((agent && agent.name) || '').trim()
  const display = String(session.display_title || session.title || '').trim()
  const preview = String(session.last_message_preview || '').trim()
  if (display && display !== agentName) return display
  return preview || display || '对话'
}

function formatWhen(value) {
  if (!value) return ''
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getMonth() + 1}/${date.getDate()} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function formatTokens(value) {
  const count = Number(value) || 0
  if (count >= 10000) {
    const text = count >= 100000 ? String(Math.round(count / 10000)) : (count / 10000).toFixed(1)
    return `${text}万 token`
  }
  return `${count} token`
}

function toItem(session, agent) {
  return {
    id: Number(session.id),
    title: rowTitle(session, agent),
    archived: session.is_archived === true,
    closed: session.is_topic_closed === true,
    shared: session.is_shared === true,
    when: formatWhen(session.update_datetime),
    tokensLabel: formatTokens(session.token_usage)
  }
}

export const useSessionNav = defineStore('sessions', {
  state: () => ({
    requirement: [],
    requirementArchived: [],
    business: [],
    businessArchived: [],
    requirementLive: null,
    businessLive: null,
    newTick: 0,
    repairTries: 0
  }),
  actions: {
    askNew() {
      this.newTick += 1
    },
    setLive(scene, item) {
      const key = scene === 'business' ? 'businessLive' : 'requirementLive'
      if (!item || !item.id) {
        this[key] = null
        return
      }
      this[key] = { id: Number(item.id), title: item.title || '对话' }
    },
    async refresh() {
      const auth = useAuthStore()
      if (!auth.token) {
        this.requirement = []
        this.requirementArchived = []
        this.business = []
        this.businessArchived = []
        return
      }
      try {
        const res = await getChatInbox('')
        const rows = (res.data && res.data.items) || []
        const requirement = []
        const requirementArchived = []
        const business = []
        const businessArchived = []
        rows.forEach((row) => {
          const session = row.session || {}
          if (!session.id || session.session_kind === 'human_support') return
          const scene = sceneOf(row.agent)
          const item = toItem(session, row.agent)
          if (scene === 'business') (item.archived ? businessArchived : business).push(item)
          else if (scene === 'requirement') (item.archived ? requirementArchived : requirement).push(item)
        })
        this.requirement = requirement
        this.requirementArchived = requirementArchived
        this.business = business
        this.businessArchived = businessArchived
        const pending = [...requirement, ...requirementArchived, ...business, ...businessArchived].some((item) => {
          const title = String(item.title || '')
          return title.startsWith('#') || title.endsWith('…')
        })
        if (pending && this.repairTries < 6) {
          this.repairTries += 1
          setTimeout(() => { this.refresh() }, 8000)
        } else if (!pending) {
          this.repairTries = 0
        }
      } catch (err) {
        this.requirement = []
        this.requirementArchived = []
        this.business = []
        this.businessArchived = []
      }
    }
  }
})
