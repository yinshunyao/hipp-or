# 问题描述

访问 `http://hipp.site/or/manager/`（已登录态）浏览器落到 `/or/manager/404`，页面文案「抱歉，您访问的页面不存在。」，并可见「退出系统」。nginx 对 `/or/manager/` 返回 200，非静态资源丢失。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/`（管理后台子路径部署约定见 `study/配置信息/生产-yin/hipp-or/部署说明.md`） |
| 开发设计 | 待定位（前端常量路由） |
| 测试设计 | 待定位 |

# 根因分析

1. `hipp-admin` 根路由 `path: '/'` 的 `redirect` 写死为 `/dashboard/analysis`。
2. 当前 `asyncRouterMap` 仅注册 `/dashboard/workplace`，不再包含 `analysis`。
3. 有 token 时访问 `/or/manager/` → `/` → `/dashboard/analysis` → 通配路由 → `/404`。404 页因存在 token 显示「退出系统」。

# 涉及文件

- `hipp-or/hipp-admin/src/router/index.ts`：根路径 `redirect` 改为 `/dashboard/workplace`。

# 设计约束更新

- 根路径默认落地页必须指向当前已注册的 dashboard 子路由，禁止指向已下线路由名。
