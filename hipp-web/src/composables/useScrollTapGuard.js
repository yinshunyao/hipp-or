import { onBeforeUnmount, ref } from 'vue'

const MOVE_PX = 8
const SCROLL_DELTA_PX = 2
const TAP_MAX_MS = 280
const OPEN_DEFER_MS = 72
const SCROLL_SETTLE_MS = 120

/** 区分横向/纵向滑动与点击，避免滚动会话条时误进会话 */
export function useScrollTapGuard(enabled) {
  const guard = ref({
    active: false,
    moved: false,
    down: false,
    x: 0,
    y: 0,
    t0: 0,
    scrollLeft0: 0,
    scrolling: false
  })
  const scrollLeft = ref(0)
  let scrollSettleTimer = null
  let containerEl = null

  function bindScrollContainer(el) {
    containerEl = el || null
    if (containerEl) scrollLeft.value = containerEl.scrollLeft || 0
  }

  function onScroll() {
    if (!enabled.value || !containerEl) return
    const left = containerEl.scrollLeft || 0
    const g = guard.value
    if (g.active && Math.abs(left - g.scrollLeft0) > SCROLL_DELTA_PX) {
      g.moved = true
    }
    scrollLeft.value = left
    g.scrolling = true
    clearTimeout(scrollSettleTimer)
    scrollSettleTimer = setTimeout(() => {
      guard.value.scrolling = false
    }, SCROLL_SETTLE_MS)
  }

  function onPointerDown(e) {
    if (!enabled.value) return
    clearTimeout(scrollSettleTimer)
    guard.value = {
      active: true,
      moved: false,
      down: true,
      x: e.clientX,
      y: e.clientY,
      t0: Date.now(),
      scrollLeft0: containerEl ? containerEl.scrollLeft || 0 : 0,
      scrolling: false
    }
  }

  function onPointerMove(e) {
    const g = guard.value
    if (!enabled.value || !g.active || g.moved) return
    const dx = Math.abs(e.clientX - g.x)
    const dy = Math.abs(e.clientY - g.y)
    if (dx > MOVE_PX || dy > MOVE_PX) g.moved = true
  }

  function onPointerUp(e) {
    if (!enabled.value) return
    const g = guard.value
    if (g.active && e) {
      const dx = Math.abs(e.clientX - g.x)
      const dy = Math.abs(e.clientY - g.y)
      if (dx > MOVE_PX || dy > MOVE_PX) g.moved = true
      if (containerEl && Math.abs((containerEl.scrollLeft || 0) - g.scrollLeft0) > SCROLL_DELTA_PX) {
        g.moved = true
      }
    }
    g.active = false
    g.down = false
  }

  function onPointerCancel() {
    if (!enabled.value) return
    guard.value = {
      active: false,
      moved: false,
      down: false,
      x: 0,
      y: 0,
      t0: 0,
      scrollLeft0: 0,
      scrolling: false
    }
  }

  function shouldIgnoreTap() {
    if (!enabled.value) return false
    const g = guard.value
    if (g.down || g.active) return true
    if (g.moved || g.scrolling) {
      g.moved = false
      return true
    }
    const dt = g.t0 ? Date.now() - g.t0 : 0
    if (dt > TAP_MAX_MS) return true
    return false
  }

  function runTapAction(fn) {
    if (!enabled.value) {
      fn()
      return
    }
    if (shouldIgnoreTap()) return
    const t0 = guard.value.t0
    setTimeout(() => {
      if (shouldIgnoreTap()) return
      if (guard.value.t0 !== t0) return
      fn()
    }, OPEN_DEFER_MS)
  }

  onBeforeUnmount(() => {
    clearTimeout(scrollSettleTimer)
    onPointerCancel()
  })

  return {
    bindScrollContainer,
    onScroll,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onPointerCancel,
    shouldIgnoreTap,
    runTapAction
  }
}