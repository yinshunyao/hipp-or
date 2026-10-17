export function smartTitle(text) {
  let value = String(text || '').replace(/\s+/g, ' ').trim()
  value = value.replace(/^(你好|您好|请|帮我|麻烦)[，,：:\s]*/, '')
  const head = value.split(/[。！？!?；;\n]/)[0].trim()
  value = head || value
  if (value.length > 18) value = `${value.slice(0, 17)}…`
  return value || '新对话'
}
