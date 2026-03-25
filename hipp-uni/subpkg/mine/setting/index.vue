<template>
  <view :class="themeClass" class="setting-container" :style="{ minHeight: `${windowHeight}px` }">
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
      <view class="list-cell list-cell-arrow" @click="handleToPwd">
        <view class="menu-item-box"><view class="iconfont icon-password menu-icon"></view><view>修改密码</view></view>
      </view>
      <view class="list-cell list-cell-arrow" @click="handleToUpgrade">
        <view class="menu-item-box"><view class="iconfont icon-refresh menu-icon"></view><view>检查更新</view></view>
      </view>
      <view class="list-cell list-cell-arrow" @click="handleCleanTmp">
        <view class="menu-item-box"><view class="iconfont icon-clean menu-icon"></view><view>清理缓存</view></view>
      </view>
    </view>
    <view class="logout-wrap">
      <button class="logout-btn" hover-class="logout-btn--hover" @click="handleLogout">
        <text class="logout-text">退出登录</text>
      </button>
    </view>
  </view>
</template>

<script>
import { themeMixin } from '@/common/mixins/theme.js'
export default {
  mixins: [themeMixin],
  data() { return { windowHeight: uni.getSystemInfoSync().windowHeight } },
  computed: {
    isDarkMode() { return this.$store.state.theme.mode === 'dark' }
  },
  methods: {
    toggleTheme() { this.$store.dispatch('theme/toggle') },
    handleToPwd() { this.$tab.navigateTo('/subpkg/mine/pwd/index') },
    handleToUpgrade() { this.$modal.showToast('模块建设中~') },
    handleCleanTmp() { this.$modal.showToast('模块建设中~') },
    handleLogout() { this.$modal.confirm('确定注销并退出系统吗？').then(() => this.$store.dispatch('auth/LogOut')) }
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

.logout-wrap { padding: 60rpx 30rpx 0; }
.logout-btn {
  width: 100%; height: 96rpx; border-radius: 48rpx;
  background: var(--t-error-bg); border: 2rpx solid var(--t-error-border);
  display: flex; align-items: center; justify-content: center;
  transition: background-color 0.2s ease;
}
.logout-btn::after { border: none; }
.logout-btn--hover { opacity: 0.85; }
.logout-text { font-size: 32rpx; font-weight: 500; color: var(--t-error); }
</style>
