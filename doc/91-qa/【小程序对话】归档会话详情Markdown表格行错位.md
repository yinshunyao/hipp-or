# 问题描述

在独立对话页（`subpkg/chat/chat`）查看**已归档话题**的历史助手消息时，若正文含 Markdown 表格（如「维度 / 评分 / 理由简述」多行），表格体未按行展开：多行数据被挤在同一视觉行上，形成多列极窄竖条，长文案逐字折行，几乎无法阅读。

复现：进入 `is_topic_closed=true` 的会话，加载含 GFM 风格 `|` 表格的助手回复，观察表头与表体布局。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【小程序对话】用户智能对话.md` |
| 原始需求 | `hipp-or/doc/01-or/【小程序对话】用户智能对话——话题归档功能.md` |
| 开发设计 | `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/04 小程序对话/小程序用户对话测试设计.md` |

# 根因分析

`hipp-or/hipp-uni/subpkg/chat/chat.vue` 中 `renderAssistantMarkdown` 将 Markdown 表头正确生成为 `<thead><tr><th>…</th></tr></thead>`，但表体循环内仅输出 `<td>…</td>` 与行尾 `</tr>`，**缺少每行开头的 `<tr>`**。HTML 结构不完整；微信小程序 `rich-text` 对表格的容错与浏览器不一致，导致表体行/列关系错乱，表现为「多行数据横排成多列」。

# 涉及文件

- `hipp-or/hipp-uni/subpkg/chat/chat.vue`：表体每行在输出 `<td>` 前补全 `<tr>`。
- `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md`：补充表格 HTML 结构约束说明。
- `hipp-or/doc/03-tr/04 小程序对话/小程序用户对话测试设计.md`：新增 Markdown 表格展示回归用例。

# 设计约束更新

助手消息 Markdown 转 HTML 时，表格数据行必须使用完整 `<tr><td>…</td></tr>`，禁止省略起始 `<tr>`，以兼容小程序 `rich-text`。
