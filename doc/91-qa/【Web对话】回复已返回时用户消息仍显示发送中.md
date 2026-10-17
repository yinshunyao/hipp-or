# 问题描述

Web 对话里，助手侧已出现「正在回复…」，对应用户消息下方仍显示「发送中…」。深度思考或首包正文尚未到达时尤其明显。

复现：在需求或商业会话发送一条会流式回复的消息，等助手出现「正在回复…」（尚无正文）时查看该用户气泡。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【Web端】用户对话与场景咨询.md` |
| 开发设计 | `hipp-or/doc/02-dr/06 Web端/Web用户端设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/06 Web端/Web用户端测试设计.md` |

# 根因分析

首轮修复只在流式回调收到**非空正文**时把 `sendStatus` 改为 `sent`。助手乐观气泡同帧出现「正在回复…」（`live`、尚无正文），与「发送中」叠在一起。

次轮改为 WebSocket `ready` 后 `markSent`，但「正在回复」在 `ready` 之前就已渲染，首屏现象仍像未修好；若线上未重新构建部署，也会继续看到旧行为。

「发送中」与「正在回复」不应同时出现：助手占位一出现即视为已进入回复通道，立即 `markSent`；界面层若下一则助手已是 `live`/有正文，也不再渲染「发送中」。

# 涉及文件

- `hipp-or/hipp-web/src/composables/useChatThread.js`：乐观助手气泡创建后立即 `markSent`；`ready`/正文/结束仍作兜底。
- `hipp-or/hipp-web/src/api/stream.js`：`ready` 投递成功后回调 `onAccepted`。
- `hipp-or/hipp-web/src/components/ChatPane.vue`：下一则助手已在回复时不显示「发送中」。
- `hipp-or/doc/02-dr/06 Web端/Web用户端设计.md`：发送状态结束时机。
- `hipp-or/doc/03-tr/06 Web端/Web用户端测试设计.md`：WEB-20。

# 设计约束更新

用户消息可短暂标「发送中」。一旦出现助手「正在回复」占位（或已有正文），即改为已发送，二者不同时展示。发送失败仍可重试。
