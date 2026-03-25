<template>
  <view class="redirect-wrap">
    <text class="redirect-text">正在打开对话…</text>
  </view>
</template>

<script>
/** 兼容旧入口：客服收件箱已合并至主包「对话」Tab（pages/chat/index） */
export default {
  onLoad() {
    uni.switchTab({ url: '/pages/chat/index' })
  }
}
</script>

<style scoped>
.redirect-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--t-root, #f5f5f4);
}
.redirect-text { font-size: 28rpx; color: #78716c; }
</style>
