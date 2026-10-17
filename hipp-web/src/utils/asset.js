export function assetUrl(url) {
  if (!url) return ''
  let s = String(url).trim()
  s = s.replace(/^https?:\/\/(127\.0\.0\.1|localhost):46000/i, '')
  const base = String(import.meta.env.BASE_URL || '/').replace(/\/$/, '')
  if (base && s.startsWith('/media/')) return `${base}${s}`
  return s
}
