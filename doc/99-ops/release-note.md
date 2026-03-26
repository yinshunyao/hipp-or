# 发布说明

## hipp-or（hipp-api / hipp-uni / hipp-admin）

### 2026-03-26

- 修复小程序「我的」页深色模式适配：`修改密码`、`关于我们` 页面顶部导航栏改为主题变量，避免固定白底导致的显示异常。
- 完善修改密码安全校验：新增「当前密码」必填与后端旧密码正确性校验（`ResetPwd.old_password` + `reset_current_password`），防止未验证旧密码直接改密。

### 2026-03-25

- 智能客服管理新增「服务类型（`service_type`）」配置与筛选，支持需求分析/商业评估及自定义类型，类型信息同步下发到小程序。
- 上线人工客服承接链路：新增人工会话模型与接口（`kind=staff`），管理端提供客服工作台，小程序对话入口统一到「对话」Tab。
- 人工客服会话改为“单会话承接多归档话题”：已有未结束人工会话时复用会话并追加系统提示，不重复建会话与分配客服。
- 对话 Tab 收件箱明确为“仅已归档话题”（`kind=session`），并优化置顶分区与最近活跃排序，减少进行中与归档混杂。
- 需求/商业场景页归档话题改为分页时间线（旧→新），支持触顶加载更旧记录，修复顺序错误与缺分页问题。
- 会话展示与可读性优化：会话标题优先使用 Dify 会话名，管理端改名后小程序可实时刷新展示，长标题两行省略。
- 小程序稳定性修复：导航/TabBar 显示异常治理、会话只读提示组件统一、场景页与详情页 Markdown 表格渲染修复。
- 管理后台系统设置放宽 ICO 上传校验，兼容常见 MIME 与空类型场景。

### 2026-03-23

**数据与迁移**

- 会话与消息表 `vadmin_chat_session`、`vadmin_chat_message` 改为逻辑 ID、无数据库外键；ORM 使用 `relationship` + `foreign()` 做 JOIN；迁移 `f7a91b2c3d4e` 删除既有外键约束。

**小程序对话（`apps/mp_chat`）**

- 收件箱、会话 CRUD、消息列表；`POST .../messages` 转发 Dify `/v1/chat-messages`（blocking）；新增表 `vadmin_chat_session`、`vadmin_chat_message`。路由前缀 `/mp/chat`，需执行 Alembic 迁移 `d4f2a1b3c8e0_mp_chat_session_message`（`versions_dev`）。
- 消息 **SSE 流式**：`POST /mp/chat/sessions/{id}/messages/stream` 透传 Dify `streaming`；小程序 `enableChunked` + `onChunkReceived` 增量展示，否则回退 blocking。
- 历史会话在智能体下架/删除后可查看、不可继续发送：`inbox` 保留历史并返回 `agent_status`，发送前校验；会话表新增 `agent_name_snapshot`、`agent_avatar_snapshot`（迁移 `9a2c1d7e4b11_mp_chat_session_agent_snapshot`）。前端列表状态标识，对话页只读并禁用输入；SSE 错误显式失败处理。

**hipp-uni**

- 对话 Tab（`pages/chat/index`）、聊天页（`pages/chat/chat`）对接上述 API；TabBar 增加「对话」。
- 底部输入区：多行 `textarea`、键盘与安全区、圆角输入壳与发送按钮；收件箱搜索框布局优化。
- 用户消息用 `<text>` 展示（修复微信 `rich-text` 问题）；乐观消息 `localId`；发送中/失败与重试。
- 助手消息 Markdown 渲染（标题、列表、引用、代码、链接），HTML 转义与 `http/https` 链接白名单；助手气泡横向铺满可视宽度。
- 修复：对话列表搜索框聚焦时占位与光标重叠（聚焦清空 placeholder）；见 `doc/91-qa/【小程序对话】对话列表搜索框占位符与光标重叠.md`。
- 修复：助手回复源码直出；见 `doc/91-qa/【小程序对话】助手回复Markdown源码直出.md`。

**智能客服管理（`apps/vadmin/agent_manager`）**

- Dify 智能体注册、连通性测试（`/v1/info`、`/v1/site`）、上架/下架、软删除、关键词搜索与状态筛选；新增 `vadmin_agent` 表。
- hipp-admin 管理页：列表、配置弹窗、测试/保存/上架；路由 `/agent/manager`。

---

## kinit（kinit-api / kinit-admin / kinit-task）

### 2025-03-22

- 登录 `/login` 密码方式支持「手机号或账号（`vadmin_auth_user.name`，须含字母）」；短信仍为手机号；`/api/login` 同步；密码错误统一提示；初始化脚本对非 `$2` 前缀密码做 bcrypt。详见 `doc/02-dr/02 登录认证与初始化.md`。
- 初始化：Excel 密码别名与数字单元格；`init.xlsx` sheet 名匹配；`migrate` 顺序先 `upgrade head` 再 autogenerate。密码登录匹配 `nickname`。登录页去掉默认演示账号。
- `MONGO_DB_ENABLE` 可由根目录 `.env` 覆盖；关闭 Mongo 时审计与任务落 MySQL（迁移 `mongo_off_mysql_01`）；kinit-task 使用 `SQLAlchemyJobStore`。运行需统一 `KINIT_DATABASE_URL` 与 `MONGO_DB_ENABLE=False` 时双端配置一致。
