# 问题描述

小程序对话页中，助手回复当前按纯文本展示，导致 `**加粗**`、列表、代码块、链接等 Markdown 语法直接显示为源码，阅读体验差且不符合智能对话产品预期。

复现：进入 `pages/chat/chat`，发送一个会返回 Markdown 内容的问题（如包含标题、列表、代码示例），可见回复区直接展示原始标记符号。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【小程序对话】用户智能对话.md` |
| 开发设计 | `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/04 小程序对话/小程序用户对话测试设计.md` |

# 根因分析

`hipp-or/hipp-uni/pages/chat/chat.vue` 中消息正文统一通过 `<text>` 节点渲染，未对助手消息执行 Markdown 解析与格式化。  
因此服务端返回的 Markdown 文本会被当作普通字符串展示。

# 涉及文件

- `hipp-or/hipp-uni/pages/chat/chat.vue`：新增 Markdown 到安全 HTML 的前端转换，并对助手消息改为 `rich-text` 展示。
- `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md`：补充助手消息 Markdown 渲染设计约束。
- `hipp-or/doc/03-tr/04 小程序对话/小程序用户对话测试设计.md`：新增 Markdown 展示回归用例。
- `hipp-or/doc/01-or/【小程序对话】用户智能对话.md`：补充已完成问题记录。

# 设计约束更新

对话页消息渲染策略细化为：用户消息保持纯文本展示；助手消息支持 Markdown 渲染，且需要进行基础 HTML 转义与协议白名单控制（仅允许 `http/https` 链接），避免渲染注入风险。
