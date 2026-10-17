# 问题描述

生产访问 `http://hipp.site/or/requirement` 为空白白屏。HTML 已返回，但脚本与样式请求指向站点根 `/assets/...`，在 `/or/` 子路径下 404，应用无法挂载。

复现：按错误环境变量 `VITE_BASE=/or/` 构建并同步到 `/data/or/hipp-web/` 后打开任意 `/or/` 路由。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【Web端】用户对话与场景咨询.md` |
| 开发设计 | `hipp-or/doc/02-dr/06 Web端/Web用户端设计.md` |
| 运维说明 | `study/配置信息/生产-yin/hipp-or/部署说明.md` |

# 根因分析

`hipp-web/vite.config.js` 读取的是 `process.env.VITE_BASE_PATH`，不是 `VITE_BASE`。误用 `VITE_BASE=/or/` 时 `base` 仍为 `/`，产物 `index.html` 中资源路径为 `/assets/...`，nginx 在 `/or/` 下无法命中。

# 涉及文件

| 文件 | 摘要 |
|:---|:---|
| `hipp-or/hipp-web/vite.config.js` | 同时接受 `VITE_BASE_PATH` 与 `VITE_BASE` |
| `hipp-or/hipp-web/dist/` | 用 `VITE_BASE_PATH=/or/` 重新构建并部署 |

# 设计约束更新

构建用户端子路径时必须使用 `VITE_BASE_PATH=/or/`（或等价的 `VITE_BASE`）；发布前检查 `dist/index.html` 是否含 `/or/assets/`。
