export const MAX_TOTAL_BYTES = 20 * 1024 * 1024 - 1
export const MAX_IMAGE_BYTES = 10 * 1024 * 1024
export const MAX_DOCUMENT_BYTES = 15 * 1024 * 1024
export const MAX_FILE_COUNT = 3

const IMAGE_EXTS = /\.(jpe?g|png|gif|webp|svg)$/i
const DOC_EXTS = /\.(pdf|txt|md|markdown|docx?|xlsx?|csv|html?)$/i

export function classifyLocalFile(file) {
  const name = file && file.name ? file.name : ''
  const type = (file && file.type) || ''
  if (type.startsWith('image/') || IMAGE_EXTS.test(name)) return 'image'
  if (DOC_EXTS.test(name) || type === 'application/pdf' || type.startsWith('text/')) return 'document'
  return null
}

/** 粘贴截图等常无文件名，补一个可上传的名字。 */
export function normalizeIncomingFile(file, index = 0) {
  if (!(file instanceof File) && !(file instanceof Blob)) return null
  const type = (file.type || '').trim()
  let name = (file.name || '').trim()
  if (!name || name === 'blob') {
    const ext =
      type === 'image/jpeg' || type === 'image/jpg' ? 'jpg'
        : type === 'image/gif' ? 'gif'
          : type === 'image/webp' ? 'webp'
            : type === 'application/pdf' ? 'pdf'
              : type.startsWith('image/') ? 'png'
                : 'bin'
    name = `paste-${Date.now()}-${index}.${ext}`
  }
  if (file instanceof File && file.name === name) return file
  return new File([file], name, { type: type || 'application/octet-stream', lastModified: Date.now() })
}

/** 从 DataTransfer / Clipboard 收集文件（含截图）。 */
export function collectTransferFiles(dataTransfer) {
  if (!dataTransfer) return []
  const out = []
  const seen = new Set()
  const push = (raw, i) => {
    const file = normalizeIncomingFile(raw, i)
    if (!file || !file.size) return
    const key = `${file.name}:${file.size}:${file.type}`
    if (seen.has(key)) return
    seen.add(key)
    out.push(file)
  }
  if (dataTransfer.items && dataTransfer.items.length) {
    Array.from(dataTransfer.items).forEach((item, i) => {
      if (item.kind === 'file') {
        const f = item.getAsFile && item.getAsFile()
        if (f) push(f, i)
      }
    })
  }
  if (dataTransfer.files && dataTransfer.files.length) {
    Array.from(dataTransfer.files).forEach((f, i) => push(f, i + 100))
  }
  return out
}

export function assertAttachList(pending, nextFile) {
  const list = [...(pending || [])]
  if (nextFile) list.push(nextFile)
  if (list.length > MAX_FILE_COUNT) {
    throw new Error(`单次最多 ${MAX_FILE_COUNT} 个附件`)
  }
  let total = 0
  for (const item of list) {
    const kind = item.type || classifyLocalFile(item.file || item)
    const size = Number(item.size || (item.file && item.file.size) || 0)
    if (kind === 'image' && size > MAX_IMAGE_BYTES) throw new Error('单张图片不能超过 10MB')
    if (kind === 'document' && size > MAX_DOCUMENT_BYTES) throw new Error('单个文件不能超过 15MB')
    total += size
  }
  if (total > MAX_TOTAL_BYTES) throw new Error('附件总体积须小于 20MB')
}

export function toSendFiles(uploaded) {
  return (uploaded || []).map((item) => ({
    type: item.type,
    url: item.url,
    name: item.name,
    size: item.size,
    mime: item.mime || ''
  }))
}
