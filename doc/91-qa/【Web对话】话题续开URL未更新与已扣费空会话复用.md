# 问题描述

1. 在 `/or/chat/{id}` 话题结束后继续发送，服务端已新建会话，地址栏仍停在旧 id，侧栏高亮也跟着旧 id，易误判为「同 chatid 覆盖」。
2. 旧版「创建即扣」留下的空会话（`fee_charged=true`、无消息、未结束）会被场景页当作进行中会话复用。例：会话 70 在 14:27 创建并扣费但无消息，15:29 才写入首条，结束时间晚于正常会话 71。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【Web端】用户对话与场景咨询.md` |
| 开发设计 | `hipp-or/doc/02-dr/06 Web端/Web用户端设计.md` |
| 扣费方案 | `hipp-or/doc/02-dr/05 系统管理/会话费率配置与扣费实施方案.md` |
| 测试设计 | `hipp-or/doc/03-tr/06 Web端/Web用户端测试设计.md`（若无对应用例则随设计补） |

# 根因分析

1. `useChatThread.ensureWritable` 会 `POST /mp/chat/sessions` 并 `open(新id)`，但 `ChatView.onRenewed` 只刷新侧栏，未 `router.replace`；`activeId` 取自 `route.params.id`。
2. `resolve_scene_agent` 返回任意 `is_topic_closed=false` 的最近会话，未排除「已扣费且无用户/助手消息」的空壳。

# 涉及文件

- `hipp-or/hipp-web/src/views/ChatView.vue`：续开后 `replace` 到新 id；同 id 不重复 `open`。
- `hipp-or/hipp-api/apps/mp_chat/crud.py`：场景解析前软删空已扣费壳；进行中会话不再返回此类壳。

# 设计约束更新

- 话题续开后浏览器路径须与当前 `meta.id` 一致。
- 场景「进行中会话」不得复用已扣费且无交互的空会话。
