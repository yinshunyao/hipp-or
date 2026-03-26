<template>
  <view class="page-with-nav">
    <uni-nav-bar
      title="客服接待"
      fixed
      status-bar
      :border="false"
      background-color="#FFFFFF"
      color="#1F1F1F"
    />
    <view class="redirect-wrap page-with-nav__body">
      <text class="redirect-text">正在打开对话…</text>
    </view>
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

<style lang="scss">
page {
  height: 100%;
  box-sizing: border-box;
}
</style>

<style lang="scss" scoped>
@import '@/uni.scss';

.redirect-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--t-root, #{$t-page-root});
}
.redirect-text { font-size: $mp-font-body; color: var(--t-text-2, #{$t-text-secondary}); }
</style>
