import { copyText } from './copy'
import { toast } from './toast'

export function sharePageUrl(token) {
  const base = window.location.origin + (import.meta.env.BASE_URL || '/')
  return new URL(`share/${token}`, base).href
}

export async function giveShareLink(token) {
  const url = sharePageUrl(token)
  if (copyText(url)) {
    toast('分享链接已复制')
    return
  }
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(url)
      toast('分享链接已复制')
      return
    } catch (err) { /* 交给弹层 */ }
  }
  window.dispatchEvent(new CustomEvent('hipp-copy', { detail: { url } }))
}
