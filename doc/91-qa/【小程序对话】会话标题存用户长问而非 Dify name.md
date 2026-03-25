# 问题描述

收件箱中会话标题显示为**整段用户首问**（或极长摘要），与 Dify 控制台中会话的短标题（`name`）不一致，用户预期列表展示 **Dify 会话名称**。

**复现条件**：话题归档或标题回退逻辑触发后，若未能正确取回 Dify `name`，曾将长用户 `query` 摘要写入 `vadmin_chat_session.title`。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【小程序对话】用户智能对话.md` |
| 原始需求 | `hipp-or/doc/01-or/【小程序对话】收件箱列表标题展示优化.md` |
| 开发设计 | `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/04 小程序对话/小程序用户对话测试设计.md` |

# 根因分析

1. 展示标题仅在「话题结束」等路径上集中更新，且 **`GET /v1/conversations` 与会话 `id` 比对**在部分环境下因格式差异未命中。
2. 回退策略将用户首问 `_preview` 过长（原 80 字）写入 `title`，易被误认为「会话名」。
3. 未优先解析 **blocking `chat-messages` 响应体**中可能携带的会话 `name`。

# 涉及文件

- `hipp-or/hipp-api/apps/mp_chat/dify_client.py`：`extract_conversation_name_from_chat_response`、会话 id 规范化比对。
- `hipp-or/hipp-api/apps/mp_chat/crud.py`：`_resolve_session_display_title`，每轮收发消息后同步 Dify `name`；归档回退改为短摘要。

# 设计约束更新

- 见 `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md`「话题归档」中关于标题落库的表述。
