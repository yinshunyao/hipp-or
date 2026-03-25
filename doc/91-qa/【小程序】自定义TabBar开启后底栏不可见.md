# 问题描述

`pages.json` 设置 `tabBar.custom: true` 并放置 `custom-tab-bar/index.vue`（内嵌 Vant `van-tabbar`）后，微信小程序底部 **整段 TabBar 不可见**，仅影响微信端（原生 TabBar 被关闭而自定义组件未正确渲染）。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/小程序整体设计.md` |
| 开发设计 | `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md` |

# 根因分析

开启 `custom` 后微信不再绘制原生底栏；自定义栏依赖 `custom-tab-bar` 组件在编译产物中正确注册 `usingComponents` 并渲染。当前 uni-app（Vue2）将该目录编译为自定义组件时，**Vant 原生组件未稳定挂载**，导致底栏区域空白。

# 涉及文件

- 已关闭 `tabBar.custom`，删除 `hipp-uni/custom-tab-bar/` 与 `common/mixins/mpTabBar.js`，恢复 `theme.js` 内 `uni.setTabBarStyle`（含 `MP-WEIXIN`）。

# 设计约束更新

- 在 uni-app 侧未验证「自定义 TabBar + 同目录 Vant 原生组件」可稳定编译前，**不得**再次打开 `tabBar.custom`。若需 Vant 样式底栏，可改为：原生 TabBar + 自绘 PNG 图标，或采用微信原生 `custom-tab-bar` 四件套（`index.js/json/wxml/wxss`）并显式 `usingComponents`。
