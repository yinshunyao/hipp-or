<template>
  <view :class="themeClass" class="page-with-nav">
    <uni-nav-bar
      title="我的"
      fixed
      status-bar
      :border="false"
      :background-color="'var(--t-nav-bg)'"
      :color="'var(--t-nav-text)'"
    />
    <view class="mine-container page-with-nav__body">
    <view class="mine-header">
      <view class="mine-avatar">
        <image
          v-if="avatarUrl"
          class="mine-avatar-img"
          :src="avatarUrl"
          mode="aspectFill"
        />
        <text v-else class="mine-avatar-icon">👤</text>
      </view>
      <text class="mine-greeting">{{ displayName }}</text>
    </view>
    <view class="content-section">
      <view class="menu-list">
        <view class="list-cell list-cell-arrow" @click="handleToEditInfo">
          <view class="menu-item-box"><view class="iconfont icon-user menu-icon"></view><view>编辑资料</view></view>
        </view>
        <view class="list-cell list-cell-arrow" @click="handleToPwd">
          <view class="menu-item-box">
            <van-icon name="lock" class="menu-icon menu-icon--van" />
            <view>修改密码</view>
          </view>
        </view>
        <view class="list-cell" @click="toggleTheme">
          <view class="menu-item-box">
            <van-icon name="setting-o" class="menu-icon menu-icon--van" />
            <view>深色模式</view>
            <view class="theme-switch" :class="{ 'theme-switch--on': isDarkMode }">
              <view class="theme-switch-thumb"></view>
            </view>
          </view>
        </view>
        <view class="list-cell list-cell-arrow" @click="handleAbout">
          <view class="menu-item-box">
            <van-icon name="info-o" class="menu-icon menu-icon--van" />
            <view>关于我们</view>
          </view>
        </view>
      </view>
    </view>
    <view class="logout-wrap">
      <button class="logout-btn" hover-class="logout-btn--hover" @click="handleLogout">
        <text class="logout-text">退出登录</text>
      </button>
    </view>
    </view>
  </view>
</template>

<script>
import { themeMixin } from '@/common/mixins/theme.js'
export default {
  mixins: [themeMixin],
  computed: {
    isDarkMode() {
      return this.$store.state.theme.mode === 'dark'
    },
    avatarUrl() {
      const avatar = this.$store.state.auth.avatar
      return avatar && String(avatar).trim() ? avatar : ''
    },
    displayName() {
      const nickname = this.$store.state.auth.nickname
      const name = this.$store.state.auth.name
      if (nickname && String(nickname).trim()) return nickname
      if (name && String(name).trim()) return name
      return '我的'
    }
  },
  methods: {
    handleToEditInfo() { this.$tab.navigateTo('/subpkg/mine/info/edit') },
    handleToPwd() { this.$tab.navigateTo('/subpkg/mine/pwd/index') },
    toggleTheme() { this.$store.dispatch('theme/toggle') },
    handleAbout() { this.$tab.navigateTo('/subpkg/mine/about/index') },
    handleLogout() { this.$modal.confirm('确定注销并退出系统吗？').then(() => this.$store.dispatch('auth/LogOut')) }
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

.mine-container {
  width: 100%; background: var(--t-root);
  padding-bottom: calc(#{$mp-account-tab-extra} + var(--custom-tabbar-height) + env(safe-area-inset-bottom));
  box-sizing: border-box;
}
.mine-header {
  display: flex; flex-direction: column; align-items: center;
  padding: $mp-account-header-pt 0 $mp-account-header-pb; background: var(--t-surface); position: relative;
}
.mine-header::after {
  content: ''; position: absolute; top: 0; left: 20%; width: 60%; height: $mp-gap-micro;
  background: linear-gradient(90deg, transparent, var(--t-accent-bg), transparent);
}
.mine-avatar {
  width: $mp-account-avatar; height: $mp-account-avatar; border-radius: 50%;
  background: linear-gradient(145deg, var(--t-ring-from), var(--t-ring-to));
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--t-shadow-heavy), inset 0 1rpx 0 var(--t-logo-inset);
  border: $mp-border solid var(--t-ring-border);
  overflow: hidden;
}
.mine-avatar-img { width: 100%; height: 100%; border-radius: 50%; }
.mine-avatar-icon { font-size: $mp-font-emoji; }
.mine-greeting {
  margin-top: $mp-gap-6; font-size: $mp-font-title; font-weight: 600;
  color: var(--t-text-1); letter-spacing: $mp-account-greet-track;
}
.content-section { padding: 0; }
.logout-wrap { padding: 60rpx 30rpx 0; }
.menu-icon--van {
  font-size: 40rpx;
  color: inherit;
  line-height: 1;
}
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
