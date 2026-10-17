# 问题描述

Web 需求对话中，Word 等附件已出现在用户气泡（说明 `POST /mp/chat/upload` 成功），助手侧立即显示「发送失败，请稍后重试。」，用户气泡旁有「重试」。同会话再发纯文字「继续分析」同样失败。

复现：已登录用户在 `/requirement` 选 `.docx` 上传后发送；或余额不足时发任意消息。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【对话】多模态附件与语音输入.md` |
| 原始需求 | `hipp-or/doc/01-or/【Web端】个人资金账户充值与订单.md` |
| 原始需求 | `hipp-or/doc/01-or/【Web端】用户对话与场景咨询.md` |
| 开发设计 | `hipp-or/doc/02-dr/06 Web端/Web用户端设计.md` |
| 开发设计 | `hipp-or/doc/02-dr/06 Web端/个人资金账户设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/06 Web端/Web用户端测试设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/06 Web端/个人资金账户测试设计.md` |

# 根因分析

1. **上传与发送校验不一致**：`POST /mp/chat/upload` 只做鉴权、类型与体积校验，**不**校验会话咨询费余额；发送（WS / blocking）会调用 `assert_dify_session_fee_affordable`。因此「附件已挂上气泡、点发送却失败」在余额不足时是预期业务拒绝，不是上传坏了。
2. **前端吞掉业务错误**：`useChatThread.js` 仅当错误文案含「免费试用 / 登录 / 删除 / 下架」时原样展示，其余一律换成「发送失败，请稍后重试。」。后端明确返回的「余额不足，请先前往账户充值后再发起咨询」等被盖掉，界面看起来像附件或通道故障。同会话后续纯文字也会因同一余额校验失败，且同样被盖成通用文案。

# 涉及文件

- `hipp-or/hipp-api/apps/mp_chat/biz_codes.py`：业务码表；余额不足 `46005`，扣费预检失败 `46006`。
- `hipp-or/hipp-api/apps/mp_chat/views.py`：WS `event=error` 增加 `code`。
- `hipp-or/hipp-web/src/utils/bizErrors.js`：按 `code` 解析文案与动作（如跳转钱包）。
- `hipp-or/hipp-web/src/api/stream.js`、`composables/useChatThread.js`：透传并处理 `code`。
- 码表设计：`hipp-or/doc/02-dr/04 小程序对话/mp_chat业务错误码.md`；全局规则：`.cursor/rules/rules-api-error-codes.mdc`。

# 设计约束更新

业务失败须 `code` + `message`；前端按码分支（`46005`→充值）。不得用通用「发送失败」覆盖已知业务码。上传成功仅表示媒体落盘，不代表本轮消息已受理。
