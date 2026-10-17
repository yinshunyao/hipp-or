# 问题描述

Web 对话里，带深度思考的回复比较长。助手正文已经开始出现后，过一会儿整条变成「发送失败，请稍后重试。」，用户气泡旁出现「重试」。

复现：在需求或商业会话发送一条会触发较长深度思考的消息，等待超过约 90 秒。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【Web端】用户对话与场景咨询.md` |
| 开发设计 | `hipp-or/doc/02-dr/06 Web端/Web用户端设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/06 Web端/Web用户端测试设计.md` |

# 根因分析

中转链路上，生产 Nginx 的对话 WebSocket（`/or/api/.../messages/ws`）读超时已是 3600 秒，不是先断开的那一环。

先断开的是浏览器。`hipp-web/src/api/stream.js` 从连接建立起固定 90 秒结束，不因仍在收到增量而顺延。到点后前端关掉 WebSocket，并把这次当成可重试失败，改走同步接口 `POST /messages`。

同步转发在 `hipp-api` 里用 `httpx.Timeout(120)` 等 Dify 的整段答案。深度思考加上正文经常超过 120 秒，第二次请求也失败。失败处理会把已经显示的助手正文换成「发送失败，请稍后重试。」

# 涉及文件

- `hipp-or/hipp-web/src/api/stream.js`：改为有数据就顺延。5 分钟没有新数据，或整段超过 20 分钟，才超时。
- `hipp-or/hipp-web/src/composables/useChatThread.js`：已经收到助手正文时，不再改走同步请求，也不再用失败文案盖掉正文。
- `hipp-or/hipp-api/apps/mp_chat/dify_client.py`：流式与同步转发给 Dify 的读取等待改为 15 分钟。
- `hipp-or/doc/02-dr/06 Web端/Web用户端设计.md`、`hipp-or/doc/03-tr/06 Web端/Web用户端测试设计.md`：补充超时约定与 WEB-21。

# 设计约束更新

持续收到增量时不按 90 秒总时长断开。尚未收到助手正文时，连接失败才回退同步发送。已经在输出时保留已收到的内容。后端等待 Dify 的读取上限为 15 分钟。
