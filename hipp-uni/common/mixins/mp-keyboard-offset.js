/**
 * 微信小程序键盘避让 mixin
 *
 * 关闭 textarea adjust-position（防止整页上推顶掉顶栏），改用
 * 「键盘高度占位 view」让输入条自然上移：
 *
 *   msg-list (flex:1, 自动收缩)
 *   input-bar (flex-shrink:0)
 *   kb-spacer (flex-shrink:0, height = keyboardHeight)  ← 键盘遮住的区域
 *
 * 使用方式：
 *  1. mixins 引入本文件
 *  2. textarea 绑定 :adjust-position="adjustPositionForInput"
 *     及 @keyboardheightchange="onKbHeightChange"
 *  3. input-bar 后追加:
 *     <view v-if="keyboardHeight > 0" class="kb-spacer"
 *           :style="{ height: keyboardHeight + 'px' }"></view>
 *  4. input-bar 加 :class="{ 'input-bar--kb-up': keyboardHeight > 0 }"
 *     在 scss 里为该 class 去掉 tabbar / safe-area 额外高度
 */
export default {
  data() {
    return {
      keyboardHeight: 0,
      _mpKbCb: null
    }
  },
  computed: {
    adjustPositionForInput() {
      // #ifdef MP-WEIXIN
      return false
      // #endif
      // #ifndef MP-WEIXIN
      return true
      // #endif
    }
  },
  onLoad() {
    // #ifdef MP-WEIXIN
    this._mpKbCb = (res) => {
      this._setKbHeight(res && res.height)
    }
    uni.onKeyboardHeightChange(this._mpKbCb)
    // #endif
  },
  onUnload() {
    // #ifdef MP-WEIXIN
    if (this._mpKbCb) {
      uni.offKeyboardHeightChange(this._mpKbCb)
      this._mpKbCb = null
    }
    this.keyboardHeight = 0
    // #endif
  },
  methods: {
    onKbHeightChange(e) {
      // #ifdef MP-WEIXIN
      const d = e && e.detail
      this._setKbHeight(d && d.height)
      // #endif
    },
    _setKbHeight(h) {
      const val = typeof h === 'number' && h > 0 ? h : 0
      if (val === this.keyboardHeight) return
      this.keyboardHeight = val
      if (val > 0 && typeof this.scrollToBottom === 'function') {
        this.$nextTick(() => this.scrollToBottom())
      }
    }
  }
}
