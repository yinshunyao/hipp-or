<template>
  <view class="page-with-nav">
    <uni-nav-bar
      :title="barTitle"
      fixed
      status-bar
      :border="false"
      background-color="#FFFFFF"
      color="#1F1F1F"
      left-icon="left"
      @clickLeft="navBack"
    />
    <view class="page-with-nav__body">
      <view class="view-title">
        <view class="view-header">{{ title }}</view>
        <text class="uni-body view-content">{{ content }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import navBackMixin from '@/common/mixins/nav-back.js'

export default {
  mixins: [navBackMixin],
  data() {
    return {
      title: '',
      content: '',
      barTitle: '浏览文本'
    }
  },
  onLoad(options) {
    if (options.query) {
      this.title = options.query.title
      this.content = options.query.content
    } else {
      this.title = options.title
      this.content = options.content
    }
    const t = options.title || this.title
    if (t) this.barTitle = t
  }
}
</script>

<style lang="scss">
page {
  height: 100%;
  box-sizing: border-box;
  background-color: #ffffff;
}
</style>

<style scoped>

.view-title {
  font-weight: bold;
  margin: 24rpx;
  padding: 24rpx;
  border-radius: 16rpx;
  background: #fff;
}

.view-header {
  font-size: 34rpx;
  line-height: 48rpx;
  margin-bottom: 12rpx;
}
</style>

<style>
.view-content {
  font-size: 26rpx;
  padding: 12px 5px 0;
  color: #333;
  line-height: 24px;
  font-weight: normal;
}
</style>
