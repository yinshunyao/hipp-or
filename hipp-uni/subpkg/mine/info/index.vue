<template>
  <view class="page-with-nav">
    <uni-nav-bar
      title="个人信息"
      fixed
      status-bar
      :border="false"
      background-color="#FFFFFF"
      color="#1F1F1F"
      left-icon="left"
      @clickLeft="navBack"
    />
    <view class="container page-with-nav__body">
    <u-cell-group>
      <u-cell title="姓名" :value="name">
        <u-icon slot="icon" class="iconfont icon-user"></u-icon>
      </u-cell>
      <u-cell title="昵称" :value="nickname">
        <u-icon slot="icon" class="iconfont icon-user"></u-icon>
      </u-cell>
      <u-cell title="手机号码" :value="telephone">
        <u-icon slot="icon" class="iconfont icon-dianhua"></u-icon>
      </u-cell>
      <u-cell title="角色" :value="roles.join(',')">
        <u-icon slot="icon" class="iconfont icon-xitongjiaose"></u-icon>
      </u-cell>
      <u-cell title="创建日期" :value="createDatetime">
        <u-icon slot="icon" class="iconfont icon-jiaofuriqi"></u-icon>
      </u-cell>
    </u-cell-group>
    </view>
  </view>
</template>

<script>
import navBackMixin from '@/common/mixins/nav-back.js'

export default {
  mixins: [navBackMixin],
  computed: {
    name() {
      return this.$store.state.auth.name
    },
    nickname() {
      return this.$store.state.auth.nickname
    },
    telephone() {
      return this.$store.state.auth.telephone
    },
    roles() {
      return this.$store.state.auth.roles
    },
    createDatetime() {
      return this.$store.state.auth.createDatetime
    }
  }
}
</script>

<style lang="scss">
page {
  background-color: #ffffff;
}
</style>
