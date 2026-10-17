# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【Web端】用户对话与场景咨询.md` |
| 关联设计 | `hipp-or/doc/02-dr/04 小程序对话/小程序用户对话设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/06 Web端/Web用户端测试设计.md` |
| 关联设计 | `hipp-or/doc/02-dr/04 小程序对话/多模态附件与语音输入设计.md`（附件/语音，待实现） |

# 功能设计

浏览器用户端位于 `hipp-web`，Vue 3 + Vite。页面消费现有 `hipp-api`，不新增后端路由，不持有 Dify `api_server` / `app_key`。

开发服务器把 `/api` 反代到 `http://127.0.0.1:46000` 并去掉前缀，把 `/media` 原样反代。请求基址为 `VITE_API_BASE`（默认 `/api`）。WebSocket 使用同一前缀：`/api/mp/chat/sessions/{id}/messages/ws?token=`。

## 路由

| 路径 | 登录 | 说明 |
|:---|:---|:---|
| `/` | — | 未登录到 `/login`，已登录到 `/requirement` |
| `/login` | 否 | 短信 / 密码登录 |
| `/legal/:kind` | 否 | `agreement` 用户协议，`privacy` 隐私政策 |
| `/topics` | 是 | 归档话题；角色含「人工客服」时为客服接待列表 |
| `/chat/:id` | 是 | 单会话 |
| `/requirement` | 是 | 需求会话页，`scene=requirement`。登录后的默认页 |
| `/business` | 是 | **首版**：重定向到 `/requirement`，不渲染商业场景页。开关 `SHOW_BUSINESS_SCENE` 打开后恢复 `scene=business` |
| `/wallet` | 是 | 个人资金账户（余额/充值/订单/流水），透传 manager；见 `个人资金账户设计.md` |

未登录访问需登录页面或 `/` 时进入 `/login?redirect=`。已登录打开登录页时进入原目标，没有目标则进入 `/requirement`。`/mine` 及下级路径不再作为页面，打开时回到需求会话并展开对应资料区。

## 登录与资料

- `POST /auth/sms/send`，body `{ telephone }`。
- `POST /auth/login`，body `{ telephone, password, method, platform: "1" }`。短信登录时 `password` 传验证码，`method` 为 `"1"`；密码登录 `method` 为 `"0"`。
- 令牌存本地，请求头 `Authorization` 为 `{token_type} {access_token}`。
- 用户信息：`GET /vadmin/auth/user/admin/current/info`。
- 更新资料：`POST /vadmin/auth/user/current/update/info`。
- 头像：`POST /vadmin/auth/user/current/update/avatar`，字段名 `file`。
- 改密：`POST /vadmin/auth/user/current/reset/password`。成功后用新密码再登录以更换 JWT。
- 刷新：`POST /auth/token/refresh`，body 为 JSON 字符串形式的 refresh token。响应头 `if-refresh: 1` 时触发。
- HTTP 401，或 403 且文案要求重新登录时，清除本地登录态并回到登录页。

协议文案与 `hipp-uni/common/legal/static-texts.js` 一致。两项都在弹层中滚到底确认后，登录页自动勾选同意；用户取消勾选后，本次停留登录页不再自动勾选。

## 话题与对话

- 普通用户：`GET /mp/chat/inbox?kind=session&q=`。
- 人工客服：`GET /mp/chat/inbox?kind=staff&q=`，列表不提供置顶/改名/删除。
- 置顶、改名、继续对话：`PATCH /mp/chat/sessions/{id}`，字段分别为 `is_pinned`、`title`、`resume_topic`。
- 删除：`DELETE /mp/chat/sessions/{id}`。
- 详情与消息：`GET /mp/chat/sessions/{id}`、`GET /mp/chat/sessions/{id}/messages?page&limit`。
- 发送优先走 WebSocket。服务端 `ready` 后发送 `{ query }`；`delta` / `message` / `agent_message` 累积助手文本；`done.topic_closed` 表示话题结束；`error` 在还没有助手正文时直接展示，不再重发。连接在持续收到数据时不按固定 90 秒断开：5 分钟没有新数据，或整段超过 20 分钟，才算超时。尚未收到助手正文时，连接失败或超时回退 `POST /mp/chat/sessions/{id}/messages`。已经在输出时保留已收到的内容，不再另发一条同步请求把正文盖成失败。
- 后端把这条对话转给 Dify。流式和同步的读取等待都是 15 分钟（流式按两次数据的间隔计，同步按整段答案到达计），避免深度思考被 120 秒读超时切断。
- 助手气泡在发送后立即出现。已收到的文本按增量直接显示；若一次到达的片段较长，则在页面上逐字补上，末尾保留闪烁光标，直到显示追上全文。用户停在底部时跟随滚动。
- 用户消息发出时可标「发送中」。助手「正在回复」占位与用户气泡同帧出现后即改为已发送，二者不同时展示；`ready`/正文/流结束仍作兜底。发送失败仍可重试。
- 发送失败须带业务 **`code` + `message`**（WS `event=error` 亦含 `code`）。前端按 `code` 分支：`46005` 展示余额不足文案并跳转 `/wallet`；其它已知码展示对应文案；瞬时通道错误用「发送失败，请稍后重试。」。禁止用 `message.includes` 作为主路径。码表见 `hipp-or/doc/02-dr/04 小程序对话/mp_chat业务错误码.md`。附件上传成功不等于本轮消息已受理（上传不校验咨询费余额）。
- 场景页进入空草稿或点「新会话」复用空草稿前调用 `GET /mp/chat/session-fee-precheck`；`POST /mp/chat/sessions` 创建前服务端同样校验。余额不足时在可输入前跳转 `/wallet`。
- 话题已结束且智能体仍为 `active` 时，发送前 `POST /mp/chat/sessions` 创建新会话再发送。智能体 `offline` / `deleted` 时只读。
- 在 `/chat/:id` 上续开成功后，须 `router.replace` 到新会话 id，使地址栏与侧栏高亮与当前 `meta.id` 一致；若路由 id 已是当前会话则不再重复加载消息。
- 人工会话（`session_kind=human_support`）只用同步发送。客服视角下，用户消息在左、客服回复在右。
- 话题已结束且智能体仍为 `active` 时，输入区上方展示「联系我们」。点击后弹出关于我们，不调用人工客服接口。

## 场景页

- **首版入口**：`hipp-web/src/config/features.js` 中 `SHOW_BUSINESS_SCENE = false`。侧栏只展示「需求」及下属「最近 / 归档」；不展示「商业」。访问 `/business` 重定向到 `/requirement`。打开开关后恢复侧栏与路由。
- `/requirement` 与（开关打开时的）`/business` 共用 `SceneView`（仅 `scene` 不同）；会话创建、发送、话题结束、分享、用户归档、扣费均走同一套 `mp/chat` 与计费逻辑，不按场景分叉。
- `GET /mp/chat/scene-agent?scene=requirement|business`（映射 `service_type` 为「需求分析」/「商业评估」）。首版前端只请求 `requirement`。
- 进行中会话：仅返回未结束且（已有用户/助手消息，或未扣费的空草稿）的最近一条。旧版「创建即扣」留下的空壳（`fee_charged=true` 且无用户/助手消息）在解析时软删，不再复用。
- 无进行中会话时 `POST /mp/chat/sessions` 创建。场景页提供「新会话」：当前会话已有用户或助手消息时再创建一条，未结束的旧会话保留；当前还是空草稿时不重复创建。
- 左侧「需求」的「最近」使用 `GET /mp/chat/inbox?kind=session&include_open=1`。该参数只给 Web 用，小程序仍只取已归档话题。首版侧栏只展示需求分析会话；商业评估会话不出现在导航（开关打开后再分组展示）。人工客服会话不进入列表。已归档会话，以及未归档但已有用户或助手消息的会话，各占一行。没有交互记录的草稿不出现。
- 列表标题用接口返回的 `display_title`。服务端在标题仍是智能体默认名，或只是用户原文开头（以 `#` 开头、以省略号结尾，或较长且与原文开头相同）时重新生成：先取 Dify 会话名，若仍是原文开头，则另请模型概括 8 到 18 字的标题，例如「Veo停车识别算法需求」。概括与回复并行，不把原文截断写进标题。用户改过、且不是原文开头的标题保持不变。打开 Web 列表时在响应返回之后改写，每次最多两条，页面随后再取一次列表。
- 「最近」只放 `is_archived` 为假的会话。其下有「归档」目录，点开后列出已归档会话，每行有时间（`update_datetime`）、标题和累计 `token_usage`。行上和会话标题旁都可以把会话标为归档，`PATCH /mp/chat/sessions/{id}` 传 `is_archived: true`。归档不改变 `is_topic_closed`，也不禁止再打开。每轮回复把 Dify `metadata.usage.total_tokens` 累加到 `token_usage`。会话表增加 `is_archived`、`token_usage`，迁移 `c4d5e6f7a8b1`（dev）与 `c4d5e6f7a8b2`（pro）。
- 点击某一条进入 `/chat/:id`；点击当前正在场景页里的那条回到该场景页。
- 助手消息用自有 Markdown 渲染（标题、列表、引用、表格、代码、链接），先转义再插入标签。
- 助手正文里的 `<think>…</think>` 先拆出，不进入 Markdown。界面标题为「深度思考」，默认收起，点击标题展开或再收起。流式过程中尚未出现结束标记时，标题为「深度思考中...(Ns)」，约每 100ms 刷新用时；结束后标题为「深度思考 (Ns)」，本会话内保留该秒数。历史消息若无本轮计时起点，只显示「深度思考」。代码块内的同名文字不拆。用户手动展开后，后续文字增长不把它重新收起。

## 界面

- 登录、协议为独立版式。登录后的页面使用左侧导航；窄屏改为底部导航。**首版导航只有「需求」**；`SHOW_BUSINESS_SCENE` 打开后才出现「商业」。不出现首页、话题、接待和客户对话。
- 左上角标识文案是「需求」，旁边名称是「智臻善算」。仅为展示，**不**跳转到公司首页 `http://hipp.site/`。登录页品牌文案同样不外链首页。
- 「需求」菜单正下方有「最近」，其下是「归档」。开关打开后「商业」同样各有一组，且只展开当前场景那一组。窄屏时把当前场景的列表放到对话区上方横向滚动，其中同样有「归档」。
- 左下角头像打开资料层，盖在对话区上，再点一次收起。编辑资料、修改密码在该层内展开表单。头像下方是「联系我们」，只弹出关于我们，不打开资料层。文案固定为成都智臻善算科技有限公司：联系人殷先生，电话 17302868369，统一社会信用代码 91510106MAKFR2T55W，地址四川省成都市金牛区光荣西路 67 号 1 栋 4 楼 517 号，网站 `http://hipp.site/`，备案号蜀ICP备2024076719号-1。深色模式仍写本地 `hipp_web_theme`。
- 首次登录须设密码时，进入会话页并展开修改密码，不要求旧密码。
- 浅色为纸色底与墨蓝字，强调色为黄铜。导航、新会话、归档、联系我们、发送和资料行使用同一套线性图标。主操作（登录、提交、发送）为黄铜实心按钮，次操作为浅底填充或文字，按钮不加描边。
- 个人头像：用户上传的图片照常显示。头像为空、图片加载失败，或地址仍是系统占位图 `DEFAULT_AVATAR`（文件名 `1674820804e81e7631.png`）时，侧栏与资料层改用站内默认头像：墨色圆印，中心为显示名首字，外圈细黄铜环。
- 对话输入：Enter 发送，Shift+Enter 换行。归档话题不再插在消息流里。

# 约束与边界

- 不实现微信一键登录与小程序游客 `wx.login`。未登录不能进入场景咨询。
- 不实现管理端智能体配置。
- 不在前端保存或传递 Dify 地址与密钥。
- **首版不做**：Web 用户端不提供商业评估导航与场景页入口；不删除后端 `scene=business` 与小程序商业能力。
