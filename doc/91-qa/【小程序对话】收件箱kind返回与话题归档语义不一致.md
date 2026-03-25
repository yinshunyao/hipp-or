# 问题描述

收件箱接口在存在进行中会话时返回 `kind=session`，无会话时返回 `kind=agent`。这导致小程序侧「智能体入口」与「会话入口」语义混用，不符合当前业务规则：**智能体入口应固定为 `kind=agent`，仅话题归档后才显示 `kind=session`**。

复现：用户与某已上架智能体完成至少一轮但未归档，会在收件箱看到该条为 `kind=session`；预期应仍是该智能体的 `kind=agent` 行。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【小程序对话】用户智能对话.md` |
| 开发设计 | `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/04 小程序对话/小程序用户对话测试设计.md` |

# 根因分析

1. `apps/mp_chat/crud.py` 的 `build_inbox` 将未归档会话直接组装为 `kind=session`，仅在无会话时补一个 `kind=agent` 虚拟行。
2. 小程序 `pages/chat/index.vue` 对 `kind=agent` 点击逻辑固定为「创建会话」，未兼容「agent 行附带已有进行中会话」的直达场景。

# 涉及文件

- `hipp-or/hipp-api/apps/mp_chat/crud.py`：收件箱组装逻辑改为进行中统一 `kind=agent`，归档/不可归类历史为 `kind=session`。
- `hipp-or/hipp-uni/pages/chat/index.vue`：点击 `kind=agent` 时若含 `row.session` 则直达既有会话，否则创建新会话；预览文案兼容 `agent+session`。
- `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md`：更新收件箱合并规则语义。
- `hipp-or/doc/03-tr/04 小程序对话/小程序用户对话测试设计.md`：更新 TC22/TC30 预期。

# 设计约束更新

收件箱 `GET /mp/chat/inbox` 返回约束：
- 已上架智能体固定返回 `kind=agent`；
- 仅 `is_topic_closed=true`（或非 active 无法归入智能体入口的历史）返回 `kind=session`；
- 进行中会话通过 `kind=agent` 的 `row.session` 承载最近会话上下文。
