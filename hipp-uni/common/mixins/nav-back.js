/** 自定义导航栏返回：栈深 >1 时后退，否则回「我的」Tab */
export default {
  methods: {
    navBack() {
      const pages = getCurrentPages()
      if (pages && pages.length > 1) {
        uni.navigateBack({ delta: 1 })
      } else {
        uni.switchTab({ url: '/pages/mine/index' })
      }
    }
  }
}
