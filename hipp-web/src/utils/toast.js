export function toast(message, type = 'info') {
  window.dispatchEvent(new CustomEvent('hipp-toast', { detail: { message: String(message || ''), type } }))
}

export function confirmDialog({ title, message, confirmText = '确定', danger = false }) {
  return new Promise((resolve) => {
    window.dispatchEvent(new CustomEvent('hipp-confirm', {
      detail: { title, message, confirmText, danger, resolve }
    }))
  })
}

export function askText({ title, value = '', placeholder = '' }) {
  return new Promise((resolve) => {
    window.dispatchEvent(new CustomEvent('hipp-ask', {
      detail: { title, value, placeholder, resolve }
    }))
  })
}
