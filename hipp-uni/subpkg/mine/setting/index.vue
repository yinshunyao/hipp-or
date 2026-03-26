<template>
  <view class="page-with-nav">
    <uni-nav-bar
      title="应用设置"
      fixed
      status-bar
      :border="false"
      :background-color="navBg"
      :color="navText"
      left-icon="left"
      @clickLeft="navBack"
    />
    <view :class="themeClass" class="setting-container page-with-nav__body">
    <view class="menu-list">
      <view class="list-cell" @click="toggleTheme">
        <view class="menu-item-box">
          <view class="iconfont icon-shezhi2 menu-icon"></view>
          <view>深色模式</view>
          <view class="theme-switch" :class="{ 'theme-switch--on': isDarkMode }">
            <view class="theme-switch-thumb"></view>
          </view>
        </view>
      </view>
    </view>
    </view>
  </view>
</template>

<script>
import { themeMixin } from '@/common/mixins/theme.js'
import navBackMixin from '@/common/mixins/nav-back.js'
export default {
  mixins: [themeMixin, navBackMixin],
  computed: {
    isDarkMode() { return this.$store.state.theme.mode === 'dark' },
    navBg() { return this.isDarkMode ? '#1C1B22' : '#FFFFFF' },
    navText() { return this.isDarkMode ? '#F0ECE2' : '#1F1F1F' }
  },
  methods: {
    toggleTheme() { this.$store.dispatch('theme/toggle') }
  }
}
</script>

<style lang="scss" scoped>
.setting-container { background: var(--t-root); padding-bottom: 40rpx; }

.theme-switch {
  margin-left: auto;
  margin-right: 16rpx;
  width: 96rpx;
  height: 52rpx;
  border-radius: 26rpx;
  background: var(--t-elevated);
  border: 2rpx solid var(--t-border);
  position: relative;
  transition: background 0.3s ease, border-color 0.3s ease;
  flex-shrink: 0;
}
.theme-switch--on {
  background: var(--t-accent);
  border-color: var(--t-accent);
}
.theme-switch-thumb {
  position: absolute;
  top: 4rpx;
  left: 4rpx;
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: var(--t-surface);
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease;
}
.theme-switch--on .theme-switch-thumb {
  transform: translateX(44rpx);
  background: var(--t-accent-text);
}

</style>
