<template>
  <view :class="themeClass" class="page-with-nav">
    <uni-nav-bar
      title="关于我们"
      fixed
      status-bar
      :border="false"
      :background-color="'var(--t-nav-bg)'"
      :color="'var(--t-nav-text)'"
      left-icon="left"
      @clickLeft="navBack"
    />
    <view class="about-container page-with-nav__body">
    <view class="header-section">
      <view class="logo-ring"><image class="about-logo" :src="logoImage" mode="aspectFill" /></view>
      <text class="about-title">{{ title }}</text>
    </view>
    <view class="content-section">
      <view class="menu-list">
        <view class="list-cell list-cell-arrow"><view class="menu-item-box"><view>版本信息</view><view class="text-right">v{{ version }}</view></view></view>
        <view class="list-cell list-cell-arrow"><view class="menu-item-box"><view>官方邮箱</view><view class="text-right">{{ WXEmail }}</view></view></view>
        <view class="list-cell list-cell-arrow"><view class="menu-item-box"><view>服务热线</view><view class="text-right">{{ WXPhone }}</view></view></view>
        <view class="list-cell list-cell-arrow"><view class="menu-item-box"><view>公司网站</view><text class="text-right site-link" @click="openSite">{{ siteUrl }}</text></view></view>
      </view>
    </view>
    <view class="copyright"><view>{{ footerContent }}</view></view>
    </view>
  </view>
</template>

<script>
import { themeMixin } from '@/common/mixins/theme.js'
import navBackMixin from '@/common/mixins/nav-back.js'
export default {
  mixins: [themeMixin, navBackMixin],
  computed: {
    version() { return this.$store.state.app.version },
    title() { return this.$store.state.app.title },
    logoImage() { return this.$store.state.app.logoImage },
    siteUrl() { return this.$store.state.app.siteUrl },
    WXEmail() { return this.$store.state.app.WXEmail },
    WXPhone() { return this.$store.state.app.WXPhone },
    footerContent() { return this.$store.state.app.footerContent }
  },
  methods: {
    openSite() { if (this.siteUrl) this.$tab.navigateTo(`/subpkg/common/webview/index?title=公司网站&url=${this.siteUrl}`) }
  }
}
</script>

<style lang="scss" scoped>
.about-container { min-height: 100vh; background: var(--t-root); }
.header-section { display: flex; flex-direction: column; align-items: center; padding: 60rpx 0 40rpx; }
.logo-ring {
  width: 160rpx; height: 160rpx; border-radius: 40rpx;
  background: linear-gradient(145deg, var(--t-ring-from), var(--t-ring-to));
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--t-shadow-heavy), 0 0 40rpx var(--t-ring-shadow-glow), inset 0 1rpx 0 var(--t-logo-inset);
  border: 1rpx solid var(--t-ring-border);
}
.about-logo { width: 120rpx; height: 120rpx; border-radius: 24rpx; }
.about-title { margin-top: 24rpx; font-size: 40rpx; font-weight: 700; color: var(--t-text-1); letter-spacing: 2rpx; }
.site-link { color: var(--t-accent) !important; }
.copyright { margin-top: 60rpx; text-align: center; line-height: 60rpx; color: var(--t-text-4); font-size: 24rpx; padding: 0 40rpx; }
</style>
