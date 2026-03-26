# 安装依赖

```bash
cd hipp-admin
# 基于node22
nvm use 22
pnpm install
```

# 开发模式
```bash
pnpm run dev
```

# 发布打包
```bash
# 使用.env.pro配置
#pnpm run build:pro
# 使用 .env 配置
pnpm run build
```

# 特别说明
本项目基于 vue-element-plus-admin 和 kinit-admin进行二开
## 介绍
vue-element-plus-admin 是一个基于 `element-plus` 免费开源的中后台模版。使用了最新的`vue3`，`vite`，`TypeScript`等主流技术开发，开箱即用的中后台前端解决方案，可以用来作为项目的启动模版，也可用于学习参考。并且时刻关注着最新技术动向，尽可能的第一时间更新。

vue-element-plus-admin 的定位是后台集成方案，不太适合当基础模板来进行二次开发。因为集成了很多你可能用不到的功能，会造成不少的代码冗余。如果你的项目不关注这方面的问题，也可以直接基于它进行二次开发。

如需要基础模版，请切换到 `mini` 分支，`mini` 只简单集成了一些如：布局、动态菜单等常用布局功能，更适合开发者进行二次开发。

## 特性

- **最新技术栈**：使用 Vue3/vite4 等前端前沿技术开发
- **TypeScript**: 应用程序级 JavaScript 的语言
- **主题**: 可配置的主题
- **国际化**：内置完善的国际化方案
- **自定义数据** 内置 Mock 数据方案
- **权限** 内置完善的动态路由权限生成方案
- **组件** 二次封装了多个常用的组件
- **示例** 内置丰富的示例

