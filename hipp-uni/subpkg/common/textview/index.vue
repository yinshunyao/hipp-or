<template>
  <view>
    <view class="view-title">
      <view class="view-header">{{ title }}</view>
      <text class="uni-body view-content">{{ content }}</text>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      title: '',
      content: ''
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
    uni.setNavigationBarTitle({
      title: options.title
    })
  }
}
</script>

<style scoped>
page {
  background-color: #ffffff;
}

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

.view-content {
  font-size: 26rpx;
  padding: 12px 5px 0;
  color: #333;
  line-height: 24px;
  font-weight: normal;
}
</style>
