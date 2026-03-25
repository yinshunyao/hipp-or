<template>
  <view :class="themeClass" class="mine-container" :style="{ minHeight: `${windowHeight}px` }">
    <view class="mine-header">
      <view class="mine-avatar"><text class="mine-avatar-icon">👤</text></view>
      <text class="mine-greeting">个人中心</text>
    </view>
    <view class="content-section">
      <view class="menu-list">
        <view class="list-cell list-cell-arrow" @click="handleToEditInfo">
          <view class="menu-item-box"><view class="iconfont icon-user menu-icon"></view><view>编辑资料</view></view>
        </view>
        <view class="list-cell list-cell-arrow" @click="handleToSetting">
          <view class="menu-item-box"><view class="iconfont icon-shezhi2 menu-icon"></view><view>应用设置</view></view>
        </view>
        <view class="list-cell list-cell-arrow" @click="handleAbout">
          <view class="menu-item-box"><view class="iconfont icon-aixin menu-icon"></view><view>关于我们</view></view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { themeMixin } from '@/common/mixins/theme.js'
export default {
  mixins: [themeMixin],
  computed: { windowHeight() { return uni.getSystemInfoSync().windowHeight - 50 } },
  methods: {
    handleToEditInfo() { this.$tab.navigateTo('/subpkg/mine/info/edit') },
    handleToSetting() { this.$tab.navigateTo('/subpkg/mine/setting/index') },
    handleAbout() { this.$tab.navigateTo('/subpkg/mine/about/index') }
  }
}
</script>

<style lang="scss" scoped>
.mine-container { width: 100%; background: var(--t-root); padding-bottom: 40rpx; }
.mine-header {
  display: flex; flex-direction: column; align-items: center;
  padding: 60rpx 0 48rpx; background: var(--t-surface); position: relative;
}
.mine-header::after {
  content: ''; position: absolute; top: 0; left: 20%; width: 60%; height: 2rpx;
  background: linear-gradient(90deg, transparent, var(--t-accent-bg), transparent);
}
.mine-avatar {
  width: 120rpx; height: 120rpx; border-radius: 50%;
  background: linear-gradient(145deg, var(--t-ring-from), var(--t-ring-to));
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--t-shadow-heavy), inset 0 1rpx 0 var(--t-logo-inset);
  border: 2rpx solid var(--t-ring-border);
}
.mine-avatar-icon { font-size: 48rpx; }
.mine-greeting { margin-top: 24rpx; font-size: 32rpx; font-weight: 600; color: var(--t-text-1); letter-spacing: 2rpx; }
.content-section { padding: 0; }
</style>
