function escapeHtml(text) {
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderInline(line) {
  let html = escapeHtml(line)
  html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>')
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>')
  html = html.replace(
    /\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
  )
  return html
}

function isTableRow(line) {
  if (!line || !line.includes('|')) return false
  const t = line.trim()
  return /^\|.*\|$/.test(t) || /^[^|]+\|[^|]+/.test(t)
}

function isTableDivider(line) {
  const t = String(line || '').trim()
  if (!t) return false
  const cols = t.replace(/^\|/, '').replace(/\|$/, '').split('|').map((s) => s.trim())
  return cols.length > 0 && cols.every((c) => /^:?-{3,}:?$/.test(c))
}

function splitCells(line) {
  return String(line || '').trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((s) => s.trim())
}

function isFenceMark(src, index) {
  if (!src.startsWith('```', index)) return false
  let prev = index - 1
  while (prev >= 0 && (src[prev] === ' ' || src[prev] === '\t')) prev -= 1
  return prev < 0 || src[prev] === '\n'
}

function pushMarkdown(parts, text) {
  if (!String(text || '').trim()) return
  parts.push({ kind: 'md', text })
}

/** 把助手回复拆成正文与深度思考。思考段默认由界面收起。 */
export function splitAssistantParts(content) {
  const src = String(content || '').replace(/\r/g, '')
  const parts = []
  let i = 0
  let buf = ''
  let fence = false
  while (i < src.length) {
    if (isFenceMark(src, i)) {
      fence = !fence
      buf += '```'
      i += 3
      continue
    }
    if (!fence && src.slice(i, i + 7).toLowerCase() === '<think>') {
      pushMarkdown(parts, buf)
      buf = ''
      const rest = src.slice(i + 7)
      const closeRel = rest.toLowerCase().indexOf('</think>')
      if (closeRel === -1) {
        parts.push({ kind: 'think', text: rest.replace(/^\n/, ''), closed: false })
        i = src.length
        continue
      }
      let text = rest.slice(0, closeRel)
      if (text.startsWith('\n')) text = text.slice(1)
      if (text.endsWith('\n')) text = text.slice(0, -1)
      if (text.trim()) parts.push({ kind: 'think', text, closed: true })
      i += 7 + closeRel + '</think>'.length
      continue
    }
    buf += src[i]
    i += 1
  }
  pushMarkdown(parts, buf)
  if (!parts.length) return [{ kind: 'md', text: src }]
  return parts
}

export function renderMarkdown(content) {
  const src = String(content || '')
  if (!src.trim()) return '<p class="md-empty">努力思考中…</p>'
  const rows = src.replace(/\r/g, '').split('\n')
  const out = []
  let inCode = false
  let codeRows = []
  let inList = false
  const flushCode = () => {
    if (!inCode) return
    out.push(`<pre><code>${escapeHtml(codeRows.join('\n'))}</code></pre>`)
    inCode = false
    codeRows = []
  }
  const flushList = () => {
    if (inList) {
      out.push('</ul>')
      inList = false
    }
  }
  for (let i = 0; i < rows.length; i += 1) {
    const line = rows[i]
    const trimmed = line.trim()
    if (trimmed.startsWith('```')) {
      if (inCode) flushCode()
      else {
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
      continue
    }
    const heading = trimmed.match(/^(#{1,3})\s+(.*)$/)
    if (heading) {
      flushList()
      const lv = heading[1].length
      out.push(`<h${lv}>${renderInline(heading[2])}</h${lv}>`)
      continue
    }
    const quote = trimmed.match(/^>\s?(.*)$/)
    if (quote) {
      flushList()
      out.push(`<blockquote>${renderInline(quote[1])}</blockquote>`)
      continue
    }
    if (isTableRow(trimmed) && i + 1 < rows.length && isTableDivider(rows[i + 1])) {
      flushList()
      const heads = splitCells(trimmed)
      out.push('<table><thead><tr>')
      heads.forEach((cell) => out.push(`<th>${renderInline(cell)}</th>`))
      out.push('</tr></thead><tbody>')
      i += 2
      while (i < rows.length) {
        const body = String(rows[i] || '').trim()
        if (!body || !isTableRow(body) || isTableDivider(body)) break
        out.push('<tr>')
        splitCells(body).forEach((cell) => out.push(`<td>${renderInline(cell)}</td>`))
        out.push('</tr>')
        i += 1
      }
      out.push('</tbody></table>')
      i -= 1
      continue
    }
    const item = trimmed.match(/^[-*]\s+(.*)$/)
    if (item) {
      if (!inList) {
        out.push('<ul>')
        inList = true
      }
      out.push(`<li>${renderInline(item[1])}</li>`)
      continue
    }
    flushList()
    out.push(`<p>${renderInline(trimmed)}</p>`)
  }
  flushCode()
  flushList()
  return out.join('') || '<p class="md-empty">（无内容）</p>'
}
