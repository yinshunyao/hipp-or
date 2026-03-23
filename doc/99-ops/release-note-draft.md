# 发布草稿（kinit）

## 2026-03-23

- hipp-api（设计/迁移）：`vadmin_chat_session` / `vadmin_chat_message` 改为**逻辑 ID、无数据库外键**；ORM 用 `relationship`+`foreign()` 做 JOIN；迁移 `f7a91b2c3d4e` 删除既有 FK 约束。

- hipp-api（新功能）：小程序对话 `apps/mp_chat`——收件箱、会话 CRUD、消息列表与 `POST .../messages` 转发 Dify `/v1/chat-messages`（blocking）；新增表 `vadmin_chat_session`、`vadmin_chat_message`。路由前缀 `/mp/chat`，需执行 Alembic 迁移 `d4f2a1b3c8e0_mp_chat_session_message`（`versions_dev`）。
- hipp-uni：对话 Tab（`pages/chat/index`）、聊天页（`pages/chat/chat`）对接上述 API；TabBar 增加「对话」入口。
- hipp-uni：`pages/chat/chat` 底部输入区改版——多行 `textarea` 自适应高度、键盘避让与安全区留白、圆角白底输入壳 + 圆形图标发送（`uni-icons` 向上箭头），对齐豆包类对话体验。
- hipp-uni（修复）：对话列表搜索框聚焦时占位提示与光标重叠——聚焦时清空 `placeholder`、失焦恢复。见 `doc/91-qa/【小程序对话】对话列表搜索框占位符与光标重叠.md`。
- hipp-api / hipp-uni：对话消息 **SSE 流式**——`POST /mp/chat/sessions/{id}/messages/stream` 透传 Dify `streaming` 响应；小程序 `enableChunked` + `onChunkReceived` 增量展示，否则回退 blocking；收件箱搜索框加高与 flex 列表区布局。
- hipp-uni（修复）：`pages/chat/chat` 用户消息改用 `<text>` 展示，修复微信端 `rich-text` 非法节点导致「有气泡无正文」；乐观消息带 `localId`；发送中/失败与失败重试。
- hipp-api / hipp-uni（完善）：历史会话支持「智能体下架/删除后可查看、不可继续发送」。后端 `inbox` 改为保留历史会话并返回 `agent_status`，新增发送前可用性校验（下架/删除直接拦截，不再转发 Dify）；`vadmin_chat_session` 新增 `agent_name_snapshot`、`agent_avatar_snapshot` 快照字段（迁移 `9a2c1d7e4b11_mp_chat_session_agent_snapshot`）。前端会话列表新增状态标识，对话页只读提示并禁用输入与发送；SSE 非流式错误响应改为显式失败处理。
- hipp-uni（修复）：`pages/chat/chat` 助手消息支持 Markdown 渲染（标题、列表、引用、代码、链接），修复回复内容以源码直出的问题；渲染前增加 HTML 转义与 `http/https` 链接白名单。见 `doc/91-qa/【小程序对话】助手回复Markdown源码直出.md`。
- hipp-uni：`pages/chat/chat` 助手消息气泡横向铺满屏幕可视宽度（抵消消息列表左右内边距），用户消息仍为右侧限宽；长文阅读时右侧不留大块空白。

- hipp-api（新功能）：智能客服管理模块 `apps/vadmin/agent_manager`——支持 Dify 智能体注册、连通性测试（调用 /v1/info 和 /v1/site 同步信息）、上架/下架、软删除、关键词模糊搜索和状态筛选。新增 `vadmin_agent` 表。
- hipp-admin（新功能）：智能客服管理页面——列表展示（头像/名称/描述/标签/状态）、配置弹窗（API 服务器 + APP_KEY + 备注）、测试/保存/上架操作、emoji 与图片头像展示。路由 `/agent/manager`。

## 2025-03-22

- kinit-api：登录 `/login` 密码方式支持「手机号或账号（`vadmin_auth_user.name`，须含字母）」，字段名仍为 `telephone`；短信登录仍为手机号；`/api/login`（OAuth2）同步；密码登录用户不存在与密码错误统一提示「账号或密码错误」；初始化脚本对 `vadmin_auth_user` 表中非 `$2` 前缀的 `password` 自动 bcrypt。详见 `doc/02-dr/02 登录认证与初始化.md`。
- kinit-api（修复）：初始化用户密码未哈希问题——支持 Excel `密码` 等表头别名、数字型密码单元格；`init.xlsx` sheet 名可与表名去分隔符后匹配。见 `doc/91-qa/【登录认证】初始化用户密码仍为明文.md`。
- kinit-api（修复）：`InitializeData.migrate_model` / `main.py init|migrate` 中 Alembic 顺序改为先 `upgrade head` 再 `revision --autogenerate` 再 `upgrade head`，避免库未追上已有迁移时出现 `Target database is not up to date`。
- kinit-api（修复）：密码登录账号标识除匹配 `name` 外，增加对 `nickname` 的匹配（与常见种子数据中 `admin` 落在昵称字段一致）。
- kinit-admin / kinit-uni：登录页去掉默认演示账号密码；密码登录占位与标签改为「手机号或账号」。
- kinit-api / kinit-task：`MONGO_DB_ENABLE` 可在项目根 `.env` 中设置（如 `false`），覆盖 `application/config/*.py` 默认值（`application/env_config.env_bool`）。
- kinit-api：支持 `MONGO_DB_ENABLE=False` 时操作审计与定时任务数据落 MySQL；新增表及 Alembic 迁移 `mongo_off_mysql_01`；操作日志中间件在关闭 Mongo 时仍可按 `OPERATION_LOG_RECORD` 写入。
- kinit-task：同配置下使用 `SQLAlchemyJobStore` 与 MySQL 读写任务定义及调度记录；依赖增加 SQLAlchemy、PyMySQL。
- 运行要求：与 API 相同设置 `KINIT_DATABASE_URL`；关闭 Mongo 时 API 与 task 进程须同时配置 `MONGO_DB_ENABLE=False` 并执行迁移。
