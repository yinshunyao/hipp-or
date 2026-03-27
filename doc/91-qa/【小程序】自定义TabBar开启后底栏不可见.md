# 问题描述

`pages.json` 设置 `tabBar.custom: true` 并放置 `custom-tab-bar/index.vue`（内嵌 Vant `van-tabbar`）后，微信小程序底部 **整段 TabBar 不可见**，仅影响微信端（原生 TabBar 被关闭而自定义组件未正确渲染）。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/小程序整体设计.md` |
| 开发设计 | `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/04 小程序对话/小程序导航与我的页测试设计.md` |

# 根因分析

本次线上场景中，自定义 `van-tabbar` 已渲染，但未显式设置 `z-index`，沿用 Vant 默认值 `1`。  
需求/商业/话题页底部输入栏在部分机型和线上渲染链路中会形成更高层级（含 fixed/阴影层），把 TabBar 完整遮住，表现为“底栏消失”。

另一个根因是页面主容器 `.page-with-nav` 采用了 `height:100% + min-height:100vh` 叠加。在小程序自定义 TabBar + 安全区场景下，容易累计出超过一屏的高度，出现你截图里的顶部空白与必须滑动。

# 涉及文件

- `hipp-or/hipp-uni/custom-tab-bar/index.js`：新增 `tabBarZIndex`，统一为高层级渲染。
- `hipp-or/hipp-uni/custom-tab-bar/index.wxml`：为 `van-tabbar` 显式传入 `z-index`。
- `hipp-or/hipp-uni/pages/mine/index.vue`：移除额外底部留白，仅保留 tabBar + 安全区占位，并压缩退出区上边距，避免首页内容被挤出首屏。
- `hipp-or/hipp-uni/static/scss/global.scss`：移除 `.page-with-nav` 的 `min-height:100vh`，改为 `height:100% + flex` 并限制容器溢出，修复一屏超高。

# 设计约束更新

- 自定义 TabBar 使用 Vant 时，必须显式配置 `z-index`（建议 ≥ 1000），禁止依赖组件默认层级。
- 所有 Tab 页新增/调整底部固定输入区后，必须回归验证 TabBar 是否可见且可点击。
- Tab 页容器禁止 `height:100%` 与 `min-height:100vh` 叠加使用，统一使用 `flex` 布局控制一屏高度。
