<template>
  <view v-if="params.url" class="page-with-nav webview-page">
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
    <web-view
      class="webview-fill"
      :webview-styles="webviewStyles"
      :src="`${params.url}`"
    ></web-view>
  </view>
</template>

<script>
import navBackMixin from '@/common/mixins/nav-back.js'

export default {
  mixins: [navBackMixin],
  props: {
    src: {
      type: [String],
      default: null
    }
  },
  data() {
    return {
      params: {},
      barTitle: '浏览网页',
      webviewStyles: {
        progress: {
          color: '#FF3333'
        }
      }
    }
  },
  onLoad(event) {
    this.params = event
    if (event.title) {
      this.barTitle = event.title
    }
  }
}
</script>

<style lang="scss">
page {
  height: 100%;
  box-sizing: border-box;
}
.webview-page {
  height: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}
.webview-fill {
  flex: 1;
  width: 100%;
  min-height: 0;
}
</style>
