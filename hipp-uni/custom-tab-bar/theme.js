/**
 * 自定义 tabBar 专用色板（JS 无法 import uni.scss）。
 * 修改主色时请同步：hipp-uni/uni.scss、static/scss/theme-css-vars.scss、pages.json tabBar
 */
module.exports = {
  ACTIVE_COLOR: '#183B63',
  INACTIVE_COLOR: '#8C95A3',
  SURFACE_BG: '#FFFFFF',
  /** 与 uni.scss $mp-tabbar-icon-px 一致 */
  TAB_ICON_PX: 28,
  /** 与 uni.scss $mp-tabbar-label-px 一致（约对齐 32rpx 列表标题） */
  TAB_FONT_PX: 16
}
