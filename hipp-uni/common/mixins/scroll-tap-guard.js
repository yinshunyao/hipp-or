const MOVE_PX = 4
const SCROLL_DELTA_PX = 1
const TAP_MAX_MS = 280
const OPEN_DEFER_MS = 120
const SCROLL_SETTLE_MS = 180
const GESTURE_TAIL_MS = OPEN_DEFER_MS + 80

function touchPointXY(t) {
  if (!t) return null
  const x = t.clientX != null ? t.clientX : t.pageX
  const y = t.clientY != null ? t.clientY : t.pageY
  if (x == null || y == null) return null
  return { x, y }
}

/** 列表滚动时避免误触进入详情（松手前须先区分滑动与点击） */
export default {
  data() {
    return {
      _listScrollTop: 0,
      _scrollSettleTimer: null,
      _scrollTapGuard: {
        active: false,
        moved: false,
        x: 0,
        y: 0,
        t0: 0,
        scrollTop0: 0,
        scrolling: false,
        longPress: false,
        wasScroll: false
      }
    }
  },
  methods: {
    _gestureStillRelevant(g) {
      if (!g || !g.t0) return false
      return Date.now() - g.t0 <= TAP_MAX_MS + GESTURE_TAIL_MS
    },
    _markListFingerOrScrollMove(g, clientX, clientY) {
      if (!g || g.moved) return
      if (clientX != null && clientY != null) {
        const dx = Math.abs(clientX - g.x)
        const dy = Math.abs(clientY - g.y)
        if (dx > MOVE_PX || dy > MOVE_PX) {
          g.moved = true
          g.wasScroll = true
        }
      }
      const top = this._listScrollTop
      if (Math.abs(top - g.scrollTop0) > SCROLL_DELTA_PX) {
        g.moved = true
        g.wasScroll = true
      }
    },
    onListScroll(e) {
      const top = (e.detail && e.detail.scrollTop) || 0
      this._listScrollTop = top
      const g = this._scrollTapGuard
      if (this._gestureStillRelevant(g)) {
        this._markListFingerOrScrollMove(g)
      }
      g.scrolling = true
      clearTimeout(this._scrollSettleTimer)
      this._scrollSettleTimer = setTimeout(() => {
        g.scrolling = false
      }, SCROLL_SETTLE_MS)
    },
    onListTouchStart(e) {
      const t = e.touches && e.touches[0]
      const pt = touchPointXY(t)
      if (!pt) return
      const g = this._scrollTapGuard
      if (g && g.active) return
      clearTimeout(this._scrollSettleTimer)
      this._scrollTapGuard = {
        active: true,
        moved: false,
        x: pt.x,
        y: pt.y,
        t0: Date.now(),
        scrollTop0: this._listScrollTop,
        scrolling: false,
        longPress: false,
        wasScroll: false
      }
    },
    onListTouchMove(e) {
      this._markListTouchMove(e)
    },
    onRowTouchMove(e) {
      this._markListTouchMove(e)
    },
    _markListTouchMove(e) {
      const g = this._scrollTapGuard
      if (!g || !g.active || g.moved) return
      const t = e.touches && e.touches[0]
      const pt = touchPointXY(t)
      if (!pt) return
      this._markListFingerOrScrollMove(g, pt.x, pt.y)
    },
    onListTouchEnd(e) {
      const g = this._scrollTapGuard
      if (g && g.active) {
        const t = e && e.changedTouches && e.changedTouches[0]
        const pt = touchPointXY(t)
        if (pt) this._markListFingerOrScrollMove(g, pt.x, pt.y)
        else this._markListFingerOrScrollMove(g)
        if (g.moved) g.wasScroll = true
      }
      if (g) g.active = false
    },
    onRowTouchStart(e) {
      this.onListTouchStart(e)
    },
    _markListLongPress() {
      if (this._scrollTapGuard) this._scrollTapGuard.longPress = true
    },
    shouldIgnoreListTap() {
      const g = this._scrollTapGuard
      if (!g) return false
      if (g.active) return true
      if (g.t0 && Math.abs(this._listScrollTop - g.scrollTop0) > SCROLL_DELTA_PX) {
        g.moved = true
        g.wasScroll = true
      }
      if (g.wasScroll || g.moved || g.scrolling || g.longPress) {
        this._resetListTapGuardFlags()
        return true
      }
      const dt = g.t0 ? Date.now() - g.t0 : 0
      if (dt > TAP_MAX_MS) return true
      return false
    },
    _resetListTapGuardFlags() {
      const g = this._scrollTapGuard
      if (!g) return
      g.moved = false
      g.longPress = false
      g.wasScroll = false
    },
    _releaseListTapAction(fn) {
      this._deferListTapAction(fn)
    },
    _deferListTapAction(fn) {
      const started = this._scrollTapGuard && this._scrollTapGuard.t0
      setTimeout(() => {
        if (this.shouldIgnoreListTap()) return
        if (started && this._scrollTapGuard.t0 !== started) return
        if (typeof fn === 'function') fn()
      }, OPEN_DEFER_MS)
    }
  },
  beforeDestroy() {
    clearTimeout(this._scrollSettleTimer)
  }
}