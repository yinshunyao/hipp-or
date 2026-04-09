# 发布草稿（kinit）

## 2026-04-09（hipp-or）

- **需求变更 + 实现**：小程序去掉微信登录；默认改为手机号 + 短信验证码登录；验证码校验通过后若手机号不存在则自动创建账号。`POST /auth/sms/send` 发码（不要求已注册）；`POST /auth/login` 在 `platform=1` 且 `method=1` 时先验码再登录/建号。见 `hipp-uni/pages/login/login.vue`、`hipp-api/apps/vadmin/auth/utils/login.py`、`login_manage.py`、`crud.py`；设计见 `doc/01-or/【小程序登录】登录功能.md` 等。

## 2026-04-08（hipp-or）

- hipp-api：阿里云短信 **AccessKey、签名、模板** 改为从 `.env` 读取（`HIPP_SMS_*`），不再从系统设置 Redis 缓存 `aliyun_sms` 读取上述项；发送间隔与验证码有效期支持 `HIPP_SMS_SEND_INTERVAL` / `HIPP_SMS_VALID_TIME`。重置密码短信使用 `HIPP_SMS_TEMPLATE_CODE_RESET`（及可选 `HIPP_SMS_SIGN_NAME_RESET`）。见 `hipp-api/.env.example`、`application/settings.py`、`utils/sms/aliyun.py`。
- hipp-uni：企业宣传**首页**页脚增加备案号展示 `备案号：蜀ICP备2026013590号-2X`。见 `hipp-uni/pages/home/index.vue`、`doc/01-or/【小程序】企业宣传首页与未登录体验咨询.md`。
- hipp-uni：企业宣传**首页**右侧增加「需求咨询」悬浮气泡（固定于视口、滚动不消失），点击 `switchTab` 至需求页，与首页 CTA 行为一致。见 `hipp-uni/pages/home/index.vue`、`doc/02-dr/04 小程序对话/企业宣传首页与访客体验设计.md`。
- hipp-admin / hipp-uni / hipp-api：**登录发码**统一走 `POST /auth/sms/send`（JSON body）；管理端登录页不再请求 `/vadmin/system/sms/send?telephone=`（该接口要求手机号已注册）。见 `hipp-admin/src/api/login/index.ts`、`hipp-uni/common/request/api/login.js`、`hipp-api/apps/vadmin/system/views.py`、`doc/91-qa/【登录发码】小程序误用管理端短信接口.md`。
- hipp-uni（修复）：**游客态**点击「手机号登录」时被路由守卫误判为「已登录」而 `replace` 回首页；现仅非 `mp_guest` 且持有 token 时从登录页踢回首页。见 `hipp-uni/permission.js`、`doc/91-qa/【小程序】游客态点击手机号登录被踢回首页.md`。
- hipp-uni（修复）：「我的」页在**游客态**（`user_type=mp_guest`）下不再展示「退出登录」按钮，与同页游客提示语义一致。见 `hipp-uni/pages/mine/index.vue`、`doc/91-qa/【小程序我的页】游客态仍显示退出登录.md`。
- hipp-uni：HTTP 403 或业务 `code=403` 且文案为需重新登录时，统一走 `auth/LogOut` 跳转登录页，不再 Toast「拒绝访问」。见 `hipp-uni/common/request/request.js`。
- hipp-api / hipp-uni：**访客体验配额按场景分别计数**——「需求分析」「商业评估」各自最多 2 次已归档话题（`is_topic_closed`），不再两场景合计 2 次；`scene-agent` 的 `guest_scene_archived_count` / `guest_need_login` 与 `46004` 校验均按当前 `service_type` 统计；首页与需求/商业页提示文案同步。见 `doc/01-or/【小程序】企业宣传首页与未登录体验咨询.md`、`doc/02-dr/04 小程序对话/企业宣传首页与访客体验设计.md`。
- hipp-api / hipp-uni：**修复退出登录后从首页进入需求/商业咨询又恢复正式登录态**——`get_or_create_mp_guest` 不再对已绑定正式/微信用户（非 `mp_guest`）的 openid 签发游客 token；小程序游客换票请求对预期失败静默 Toast；`storage.clean()` 同步清空内存缓存。见 `doc/91-qa/【小程序】退出登录后进入需求商业咨询恢复登录态.md`。

## 2026-03-26（hipp-or）

- hipp-uni / hipp-api：**企业首页与游客体验**——新增主包 `pages/home/index`（对标 `爱宝喜宝/luo/index.html` 信息架构与配色）；TabBar 首项「首页」；`POST /auth/mp/guest`（`wx.login` code）签发 `user_type=mp_guest`；需求/商业场景下按 `service_type` **分别**统计已归档会话，各场景 ≥2 次后在该场景禁止新建会话与发消息（`46004`），`scene-agent` 返回 `guest_need_login` 等字段；路由无 token 时先尝试游客登录。见 `doc/01-or/【小程序】企业宣传首页与未登录体验咨询.md`、`doc/02-dr/04 小程序对话/企业宣传首页与访客体验设计.md`。
- hipp-uni（修复）：微信小程序键盘弹起时输入框被遮挡、顶栏消失——关闭 `textarea` 默认整页上推，改用「键盘高度占位 view」方案：在 `input-bar` 下方插入 `kb-spacer`（`height = keyboardHeight`），flex 布局自动收缩消息列表、上移输入条，顶栏与胶囊始终可见。三页（需求/商业/对话）统一接入 `mp-keyboard-offset` mixin。见 `doc/91-qa/【小程序对话】键盘弹起顶栏与菜单消失.md`。
- hipp-api / hipp-uni：小程序对话流式新增 WebSocket（WSS）链路：后端增加 `WS /mp/chat/sessions/{id}/messages/ws`（token 鉴权、增量 `delta` / 完成 `done` / 错误 `error` 事件）；前端 `MP-WEIXIN` 分支改用 `uni.connectSocket` 实时渲染，连接失败自动回退 blocking 发送，保留现有非小程序发送逻辑。
- hipp-uni：优化自定义底部 TabBar 真机视觉密度，统一下调栏高（`56px -> 50px`）、图标（`28px -> 24px`）与文案字号（`16px -> 13px`），并同步 `custom-tab-bar/theme.js` 与 `uni.scss` 设计令牌，改善「底栏过大不协调」观感。
- hipp-api（修复）：`run.sh` 首次启动（无 `.venv`）分支改为复用统一的 `ensure_db_schema_before_run` 流程，不再直接 `init`；当目标库不存在时可先自动建库，再执行迁移/初始化，避免 Ubuntu 生产环境报 `Unknown database 'hipp'` 导致启动失败。见 `doc/91-qa/【登录认证】Ubuntu首次启动Unknown database导致初始化失败.md`。
- hipp-uni / hipp-api：修复「我的」页两处问题——`修改密码`、`关于我们` 页面顶部导航栏改为主题变量，深色模式下不再固定白底；修改密码流程新增「当前密码」必填与后端旧密码正确性校验（`ResetPwd.old_password` + `reset_current_password` 校验），防止未验证旧密码直接改密。见 `doc/91-qa/【小程序我的页】修改密码与关于我们未适配深色模式且缺少当前密码校验.md`。

## 2026-03-24（hipp-or）

- hipp-api：`run.sh` 增加数据库自愈能力——连接检查阶段遇到 MySQL `1049 (Unknown database)` 时，自动创建目标数据库（`utf8mb4`）后继续执行核心表检查；缺表仍按原逻辑执行 `main.py init`，其余连接错误保持失败退出。见 `doc/02-dr/02 登录认证与初始化.md`、`doc/03-tr/02 登录认证与初始化测试设计.md`。
- hipp-api / hipp-admin：**用户管理定制**——`vadmin_auth_user` 增加 `is_system_created`、`is_blocked`；列表/详情返回 `user_tags`（系统创建/微信用户）；`PUT /vadmin/auth/users/{id}/blocked`；登录与 `token/refresh` 拦截拉黑。管理端用户表展示标签与拉黑操作。迁移 `a1b2c3d4e5f6_user_system_created_blocked`。见 `doc/01-or/【后台管理】用户管理定制功能.md`、`doc/02-dr/05 系统管理/后台用户管理定制设计.md`。
- hipp-api / hipp-admin：**智能客服类型**——`vadmin_agent.service_type`（可空）；列表查询参数 `service_type`；连通性测试与保存写入类型。管理端配置弹窗 `ElSelect` 可选项「需求分析」「商业评估」并支持 `allow-create` 自定义；列表列与搜索区类型筛选。Alembic：`b2c4e6d8a0f1_vadmin_agent_service_type`。小程序 `AgentSnippetOut` 增加 `service_type` 字段。见 `doc/01-or/【智能客服管理】Dify智能体接入管理.md`、`doc/02-dr/03 智能客服管理/Dify智能体接入管理设计.md`。
- hipp-uni：角色为 **`人工客服`** 时，「对话」Tab 展示客服收件箱（`kind=staff`），导航栏标题「客服接待」；「我的」中移除「客服接待」菜单；`subpkg/chat/staff-inbox` 改为跳转「对话」Tab。见 `doc/02-dr/05 人工客服/需求类话题人工客服设计.md`。
- hipp-api：**人工客服单会话合并多归档**——`POST /mp/chat/human-support/sessions` 在已存在未结束（`is_topic_closed=false`）的人工会话时，向该会话追加 `system` 归档提示，不新建会话、不重新分配客服；同一归档来源复用仍按会话行或历史 `system` 中 `来源会话 ID：{id}` 判断。见 `doc/02-dr/05 人工客服/需求类话题人工客服设计.md`、`doc/01-or/【人工客服】 需求类话题响应.md`。
- hipp-api / hipp-uni / hipp-admin：**人工客服（需求类归档话题）**——`vadmin_chat_session` 增加 `session_kind` / `assigned_human_user_id` / `source_archive_session_id`，`agent_id` 可空；`vadmin_chat_message.role` 支持 `system`。新接口 `POST /mp/chat/human-support/sessions`、`GET /mp/chat/inbox?kind=staff`；人工会话使用同步 `POST .../messages`。小程序归档会话页悬浮「联系人工客服」、对话 Tab 展示人工会话标签、「我的 → 客服接待」；管理端 `/mp-staff/chat-workbench`。迁移 `c8d9e0f1a2b4_mp_chat_human_support`。需存在角色名 **`人工客服`** 的账号。见 `doc/02-dr/05 人工客服/需求类话题人工客服设计.md`。
- hipp-api / hipp-uni：**对话 Tab 收件箱仅展示已归档话题**——`GET /mp/chat/inbox?kind=session` 不返回 `kind=agent`，仅 `is_topic_closed=true` 的 `kind=session`；**省略 `kind`** 时仍为合并列表（智能体+会话）便于调试。`hipp-uni` 的 `getChatInbox` 固定传 `kind=session`。置顶分区整体在前，分区内按最近活跃倒序。见 `doc/01-or/【小程序对话】用户智能对话.md`、`doc/02-dr/04 小程序对话/小程序用户对话设计.md`。
- hipp-uni（修复）：`pages/requirement/index`、`pages/business/index`、`subpkg/chat/chat`、`pages/chat/index` 避免根布局 `100vh` 与微信原生导航栏叠层；`theme.js` 在 `MP-WEIXIN` 下不再调用 `uni.setTabBarStyle`（自定义 TabBar 无效且可能干扰导航）。见 `doc/91-qa/【小程序】需求页左上角返回不可见.md`。
- hipp-uni（回退）：关闭 `tabBar.custom`，移除 `custom-tab-bar` 与 `mpTabBarMixin`；恢复微信原生底栏与 `theme.js` 中 `uni.setTabBarStyle`（自定义 Vant TabBar 在 uni-app 编译后未稳定挂载，导致底栏整段不可见）。底栏仍用 `pages.json` 中 `iconPath` PNG。
- hipp-uni：按 `doc/01-or/【前段UI】 UI需求.md` 将底部导航改为自定义 TabBar：`pages.json` 启用 `tabBar.custom=true`，新增 `custom-tab-bar/index.vue`（纯自绘，不使用 Vant tabbar），并为话题/需求/商业/我的四页补齐底部安全间距，避免输入区和内容被遮挡。
- hipp-uni：`pages/chat/index` 收件箱搜索栏改为 Vant `van-search`（`input-align="center"`、占位「请输入搜索关键词」），移除原自定义搜索框样式；`pages.json` 注册 `/static/wxcomponents/vant-weapp/search/index`。
- hipp-uni（微信小程序）：会话只读时底部说明使用 Vant `van-notice-bar`，仅 `wrapable` + `scrollable=false` + `text`，沿用组件默认样式（不绑主题色、不加 `custom-class`）；`@vant/weapp/lib` 在 `static/wxcomponents/vant-weapp`，`pages.json` 注册 `/static/wxcomponents/vant-weapp/notice-bar/index`。升级 Vant 时执行 `scripts/sync-vendor-vant-weapp.sh`。非微信端仍为原 `readonly-tip` 样式。见 `doc/01-or/【小程序对话】用户智能对话——话题归档功能.md`。
- hipp-uni：`subpkg/chat/chat` 话题已结束时「联系人工客服」与底部 `NoticeBar` 提示改为纵向栈布局，去掉按钮 `fixed` 叠层，避免提示文案被遮挡；提示区不再重复叠加底部安全区内边距，并缩小消息列表底部留白，避免提示与输入框之间过高空白。见 `doc/91-qa/【小程序对话】话题已结束提示与人工客服按钮重叠.md`。
- hipp-uni：`subpkg/chat/chat` 助手 Markdown 表格表体补全每行 `<tr>`，修复归档会话详情中表格多行错位为「多列竖条」的问题。见 `doc/91-qa/【小程序对话】归档会话详情Markdown表格行错位.md`。
- hipp-api / hipp-uni：场景页（需求/商业）归档话题改为 `GET /mp/chat/agents/{agent_id}/archived-topics` 分页；时间线旧→新再接当前消息，`scrolltoupper` 加载更旧归档。见 `doc/91-qa/【小程序对话】场景页归档话题顺序错误与缺分页.md`。
- hipp-api / hipp-uni：收件箱返回语义调整——进行中会话不再单独返回 `kind=session`，统一挂到 `kind=agent` 的 `row.session`；仅归档话题返回 `kind=session`。小程序点击 `kind=agent` 行优先直达已有进行中会话，否则创建新会话。见 `doc/91-qa/【小程序对话】收件箱kind返回与话题归档语义不一致.md`。
- hipp-admin / hipp-api：系统设置「ICO 图标」上传放宽校验——支持 `image/vnd.microsoft.icon` 等常见 MIME、空类型或 `application/octet-stream` 时以 `.ico` 扩展名判定；后端 `IMAGE_ACCEPT` 与 `validate_file` 对齐。见 `doc/91-qa/【管理后台】系统设置ICO上传误报格式错误.md`。
- hipp-api / hipp-uni：管理端更新智能体名称等资料后，小程序收件箱与对话页通过 `display_title` 与 `onShow` 刷新展示当前智能体名称（用户自改会话标题时仍以 `title` 为准）。见 `doc/91-qa/【小程序对话】后台更新智能体后对话页信息不刷新.md`。
- hipp-uni：收件箱长按会话菜单中置顶操作按 `is_pinned` 展示「置顶」或「取消置顶」（默认非置顶显示「置顶」），替代合并文案「置顶/取消置顶」。见 `doc/01-or/【小程序对话】用户智能对话.md`、`pages/chat/index.vue`。
- hipp-api：`GET /mp/chat/inbox` 合并顺序按 OR 调整——置顶会话 → `kind=agent` → 未置顶未归档会话 → 未置顶已归档会话；实现见 `apps/mp_chat/crud.py` 与 `apps/mp_chat/inbox_order.py`。
- hipp-api：`mp_chat` 会话展示标题优先取 Dify 会话 `name`（blocking 响应解析 + `GET /v1/conversations`，id 比对忽略大小写/连字符）；每轮消息成功后同步；归档回退不再写入长用户首问摘要。见 `doc/91-qa/【小程序对话】会话标题存用户长问而非 Dify name.md`。
- hipp-uni：`pages/chat/index` 收件箱会话标题最多两行省略，避免长标题撑满列表；状态标签与标题同行展示。见 `doc/91-qa/【小程序对话】收件箱会话标题过长撑满列表.md`。
- hipp-uni：按 `doc/01-or/小程序整体设计.md` 隐藏工作台 Tab 与主包工作台页；「我的」页移除个人信息区、四宫格快捷入口、常见问题，菜单顺序为编辑资料 → 应用设置 → 关于我们。
- hipp-api：小程序对话 `mp_chat` 话题归档——`vadmin_chat_session.is_topic_closed`；流式结束 SSE 追加 `mp_topic`；`POST` 拦截已归档会话（`46002`）；`PATCH` 支持 `resume_topic`；收件箱合并规则改为仅「进行中会话」占用智能体虚拟行。
- hipp-uni：对话页与收件箱支持话题已结束、继续对话、列表「已结束」标识。
- hipp-api：话题归档标题优先从 Dify `GET /v1/conversations` 取会话 `name`，失败再回退用户问题摘要/原标题。

## 2026-03-23

- hipp-uni（小程序）：通过代码质量检查——`manifest.json` 启用 `lazyCodeLoading: requiredComponents`；非 Tab 页面拆到分包 `subpkg/*`（我的子页、公共 webview/文本、独立聊天页、原 `pages/index`）；删除未引用的 `static/images/avatar.jpg`（超 200KB 限制）；「我的」Tab 预下载 `subpkg/mine` 分包。导航路径已改为 `/subpkg/...`。后续继续瘦身：移除 `main.js` 中 uView 全量注入、将剩余 `uni-*` 页面组件改为原生/uView 组件并清理 `hipp-uni/uni_modules`。

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
- hipp-uni（修复）：登录页 uView 组件（`u-button`/`u-checkbox-group`/`u-checkbox`）在微信小程序中报 "Component is not found"——`main.js` 缺少 `import uView from 'uview-ui'` 和 `Vue.use(uView)` 注册；同步补回 `uni_modules/zb-tooltip` 等依赖。

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
