# 发布草稿（kinit）

## 2026-10-16（hipp-or）

- 电商短链次卡：管理台生成/作废短链；`/or/a/{token}` 打开短链后免登录做 1 次需求分析（不扣钱包）；小红书回调 `POST /commerce/channels/xhs/notify` 幂等出链；迁移 dev `c1d2e3f4a5b6`、pro `c1d2e3f4a5b7`。环境变量 `HIPP_OR_ACCESS_BASE`、`HIPP_XHS_*`。见 `doc/01-or/【电商履约】多渠道短链次卡.md`、`study/配置信息/小红书千帆-成都智臻善算/`。
- 管理端「电商履约 → 渠道订单」流水：状态已支付 / 已核销 / 已退费；咨询完成核销；管理端退费作废短链（资金在千帆）；迁移 dev `d2e3f4a5b6c7`、pro `d2e3f4a5b6c8`。
- 管理端「线下出链」：一键生成 1 次需求分析短链（`channel=offline`、已支付），便于线下收款后交付；接口 `POST /vadmin/commerce/orders/offline`。
- 2026-10-16 现网 hipp.site：已同步 API/web/admin，迁移至 pro `a1627d741ce8`（含电商表）；`HIPP_OR_ACCESS_BASE=http://hipp.site/or/a`；`HIPP_XHS_*` 未配，千帆联调待后续。
- 次卡短链交互：布局对齐分享页（无新会话/归档/分享）；完成后同一链接自动只读可转发；`GET /commerce/access/{token}` 在 used 时返回正文。
- 管理端次卡短链：短链基址 https；状态/渠道中文；操作「复制链接 / 退费」；Table 列 slots 修复；退费同步订单已退费。
- 余额不足提示前移：建会话（`POST /sessions`）与空草稿预检（`GET /session-fee-precheck`）即返回 `46005` 并引导 `/wallet`，避免写完长文再失败；发消息仍保留校验。见 `doc/02-dr/06 Web端/个人资金账户设计.md`。
- 修复：Word 等附件上传成功后界面只显示「发送失败」——业务错误码 `46005` 余额不足 / `46006` 扣费预检失败；WS 透传 `code`；Web 按码展示并跳转 `/wallet`。全局范式见 `.cursor/rules/rules-api-error-codes.mdc`。见 `doc/91-qa/【Web对话】附件上传成功但消息显示发送失败.md`、`doc/02-dr/04 小程序对话/mp_chat业务错误码.md`。
- hipp-web：深度思考标题显示用时，进行中为「深度思考中...(12.7s)」，结束后保留「深度思考 (13s)」；历史无本轮计时不显示秒数。见 `doc/01-or/【Web端】用户对话与场景咨询.md`。
- hipp-web 首版隐藏「商业评估」入口：侧栏只保留「需求」；`/business` 重定向到 `/requirement`。开关 `SHOW_BUSINESS_SCENE`（`hipp-web/src/config/features.js`）可恢复。见 `doc/01-or/【Web端】用户对话与场景咨询.md`。
- hipp-web：暂隐藏对话输入区「语音输入」麦克风按钮（`voiceInputEnabled = false`）；附件上传不受影响。现网已同步 `hipp-web` 静态。

## 2026-10-15（hipp-or）

- 修复：助手「正在回复…」与用户「发送中」叠显——乐观占位出现即标已发送，界面层也屏蔽同屏「发送中」。见 `doc/91-qa/【Web对话】回复已返回时用户消息仍显示发送中.md`。
- 媒体清理：待发取消调 `DELETE /mp/chat/upload` 删盘；全站孤儿 GC：每日约 03:00（`HIPP_OR_MEDIA_GC*`）。**结题不再删除消息 attachments 媒体**（修复历史/分享裂图）。manager：`DELETE /api/media`、`POST /api/s2s/media/delete`、`/api/s2s/media/gc`。
- 对话附件上传改走 hipp-manager 公共媒体（`POST /api/media/upload` → `/media/...`），修复生产 OSS 占位配置导致 `bucket.endpoint` 解析失败；门面仍为 `POST /mp/chat/upload`。见多模态 OR/DR 与 manager `【平台】公共媒体上传与访问`。
- 修复：管理端侧栏「智能客服」菜单丢失——上线人客服时误用 `/mp-staff` 覆盖了 `asyncRouterMap` 的 `/agent`；已恢复与人工客服、计费并存。见 `doc/91-qa/【管理后台】智能客服菜单被人工客服路由覆盖.md`。
- 对话多模态：`POST /mp/chat/upload`（平台媒体）、`POST /mp/chat/audio-to-text`；发送 blocking/SSE/WS 支持 `files`（优先 Dify `remote_url`）；消息表 `attachments`（迁移 dev `a9b0c1d2e3f4`、pro `a9b0c1d2e3f5`）；合计 &lt;20MB、单图≤10MB、单文档≤15MB、最多 3 个。hipp-web / hipp-uni 输入区附件与语音转写；Web 输入区支持粘贴/拖拽入附。Dify 导出 yml 已开 file_upload/vision/STT（控制台须同步发布）。见 `doc/01-or/【对话】多模态附件与语音输入.md`。
- 修复：`/chat/:id` 话题结束后续开会新建会话但地址栏仍停在旧 id——改为 `replace` 到新 id，同 id 不重复加载。场景页不再复用「已扣费且无消息」的空壳，解析/新建时软删此类遗留会话。见 `doc/91-qa/【Web对话】话题续开URL未更新与已扣费空会话复用.md`。
- 修复：已登录访问 `/or/manager/` 落到 `/404`——根路由误重定向到已下线的 `/dashboard/analysis`，改为 `/dashboard/workplace`。见 `doc/91-qa/【管理后台】根路径重定向到已移除的analysis导致404.md`。
- 会话费率与扣费：管理端侧栏「计费配置」；**话题结束**时 S2S 扣费（`consume_session`）；发消息前余额校验；已结束未扣费打开详情补扣；`/wallet` 流水与充值单默认 `product=or`。方案见 `doc/02-dr/05 系统管理/会话费率配置与扣费实施方案.md`。
- 需求/商业场景页：话题结束后右上角展示分享与归档（与独立会话页一致）。
- `/wallet` 交易流水：展示会话标题，隐藏产品列（本产品页隐含 or）。


- 产品码 `or` + 平台管理员：充值/短信登录带 `product=or`；管理端密码登录优先校验 hipp-manager ops，失败回落本地；在线校验兼容 ops 令牌（`/api/ops/auth/me`）。
- hipp-admin / hipp-api：会话咨询费用配置——全局默认金额 + 按用户搜索设定/清除专属；接口 `/vadmin/billing/session-fee/*`；管理页 `views/Vadmin/Billing/SessionFee`（菜单 `/billing/session-fee`）。迁移 dev `e7f8a9b0c1d2`、pro `e7f8a9b0c1d3`。见 `doc/01-or/【管理后台】会话咨询费用配置.md`。
- hipp-web / hipp-api：个人资金账户——`/wallet` 余额、充值（支付码弹窗）、充值订单与流水；后端 `/wallet/*` 透传 hipp-manager。资料层入口「账户余额」。会话扣费按配置解析金额另交付。见 `doc/01-or/【Web端】个人资金账户充值与订单.md`。
- 侧栏与登录页品牌文案不再跳转公司首页；「联系我们」弹窗仍含备案号等公司信息，并按需求端黄铜风格重排。
- 修复：生产 `/or/` 空白页——构建须用 `VITE_BASE_PATH=/or/`（误用 `VITE_BASE` 时资源落到 `/assets/`）。见 `doc/91-qa/【Web端】子路径构建变量错误导致空白页.md`。
- 业务鉴权二次校验 manager：登录/SSO 服务端缓存 `manager_token`；需鉴权接口（含 WS）向 manager `/me` 校验在线（短缓存）。`mp_guest`/纯微信会话跳过。配置了 `HIPP_MANAGER_BASE` 时管理端密码登录也必须拿到 manager 令牌。

## 2026-10-14（hipp-or）

- 同站登录态互通：用户侧与管理端登录回写 `manager_token`；`POST /auth/sso`；hipp-web / hipp-admin 启动换票。与 `/mgr/`、`/cert/`、`/vf/` 免重复登录。
- hipp-web：最近列表、归档列表和已打开话题上的「分享」「复制链接」「停止分享」改为图标。悬停或键盘聚焦显示操作名称，点击行为不变。列表里的图标按钮收成一组，组内间距小于标题和按钮组之间的空隙。见 `doc/01-or/【Web对话】消息时间与归档分享.md`。

## 2026-10-13（hipp-or）

- hipp-web / hipp-api：会话消息展示日期时间。已完成话题可分享，不必先归档；已分享的只复制原链接，并可停止分享。链接免登录只读，页面只有聊天内容和「联系我们」。会话表增加 `share_token`（迁移 dev `d5e6f7a8b9c1`、pro `d5e6f7a8b9c2`）。见 `doc/01-or/【Web对话】消息时间与归档分享.md`。

- hipp-web：重做图标、按钮和界面样式。导航、新会话、归档、联系我们、发送和资料行改为统一线性图标；主按钮为黄铜实心，次按钮用浅底填充，不再加描边。没有自选头像，或仍是系统占位图时，侧栏和资料层显示姓氏圆印。业务流程不变。见 `doc/01-or/【Web端】用户对话与场景咨询.md`。

## 2026-10-11（hipp-or）

- hipp-web / hipp-api：会话标题改为大模型概括，不再把用户原文开头截成标题。仍是原文开头的旧标题会在打开列表时改写。「最近」下增加「归档」，归档后可看到时间、标题和 token 消耗。会话表增加 `is_archived`、`token_usage`（迁移 dev `c4d5e6f7a8b1`、pro `c4d5e6f7a8b2`）。见 `doc/01-or/【Web端】用户对话与场景咨询.md`。
- hipp-web / hipp-api：长回复不再被浏览器 90 秒总超时掐断。持续有数据时保持连接，5 分钟无新数据或整段超过 20 分钟才超时。转给 Dify 的读取等待改为 15 分钟。已经输出的正文不再改走同步请求并盖成失败。见 `doc/91-qa/【Web对话】深度思考回复被90秒超时掐断.md`。
- hipp-web：助手回复一开始出现，用户消息就不再显示「发送中」，不必等整段生成结束。见 `doc/91-qa/【Web对话】回复已返回时用户消息仍显示发送中.md`。
- hipp-web：助手回复中的深度思考改为中文标题「深度思考」，默认收起，点击后展开；思考未结束时标题为「深度思考中」。不再把英文 think 标签摊在正文里。见 `doc/01-or/【Web端】用户对话与场景咨询.md`、`doc/02-dr/06 Web端/Web用户端设计.md`。
- hipp-web / hipp-api：未结束的会话也可以新开一条；有用户或助手消息的会话留在「最近」，空草稿不列出。未归档会话也会生成短标题（Dify 会话名，否则首条用户问题），不用最新一句原话。助手回复在页面上逐字出现并带光标。`GET /mp/chat/inbox?kind=session&include_open=1` 仅 Web 使用，小程序收件箱仍只返回已归档话题。见 `doc/01-or/【Web端】用户对话与场景咨询.md`、`doc/02-dr/06 Web端/Web用户端设计.md`。

## 2026-10-10（hipp-or）

- **hipp-web**：话题结束后的按钮改为「联系我们」，点击弹出关于我们。点「需求」或「商业」时，另一侧的最近会话清单收起。
- **hipp-web**：「需求」「商业」菜单下各自列出最近会话，每条归档单独一行。去掉接待和客户对话。头像下方增加「联系我们」，点击只弹出关于我们。

- **hipp-web**：站点默认进登录页，已登录进需求会话。会话页左侧「最近」下列归档会话。去掉首页和「我的」菜单；品牌改为「需求 / 智臻善算」，链到 `http://hipp.site/`。资料在头像层就地展开，关于我们弹窗对齐成都智臻善算科技有限公司信息。

## 2026-10-09（hipp-or）

- **hipp-web**：新增浏览器用户端（Vue 3）。覆盖首页、短信/密码登录、归档话题、流式对话、需求与商业场景、资料/密码/关于。接口复用 `/auth` 与 `/mp/chat`，开发时由 Vite 将 `/api` 反代到 `127.0.0.1:46000`。见 `doc/01-or/【Web端】用户对话与场景咨询.md`、`doc/02-dr/06 Web端/Web用户端设计.md`。

## 2026-04-09（hipp-or）

- **修复（hipp-api / Alembic）**：补全缺失修订 `04bbb43d68dc` 占位脚本，并将 `c146cc30b075` 的 `down_revision` 与其衔接，避免已有 `alembic_version=04bbb43d68dc` 的环境报 `Can't locate revision`。见 `doc/91-qa/【数据库迁移】alembic_version缺失修订04bbb43d68dc.md`。
- **修复（hipp-api）**：`GET /vadmin/auth/user/admin/current/info` 在员工用户**未分配角色**时不再因 `max()` 空序列异常导致无效响应；无角色时数据范围按「仅本人」处理。见 `doc/91-qa/【登录认证】当前用户信息无角色时接口max空序列.md`。
- **hipp-admin（体验）**：`GET /auth/getMenuList` 未返回成功数据时进入 `/no-access` 说明页，可「退出并更换账号」；抽取 `loadDynamicMenuRoutes` 供登录与路由守卫共用；404 页在已登录时增加「退出系统」。见 `doc/01-or/【管理后台】无权限与菜单失败说明页及退出换账号.md`。
- **修复（小程序）**：短信/密码登录写入 `SET_TELEPHONE`；改密成功后先 `Login` 换新 JWT 再 `switchTab` 进首页，避免无手机号跳过 `Login`、旧 token 与库不一致导致反复进改密页。
- **需求 + 实现**：短信验证码**首次自动注册**用户设置登录密码时识别「无当前密码」：`must_set_password_without_old` 字段、登录/刷新 token 返回标志、重置密码接口在该场景跳过旧密码校验；管理端批量初始化密码时清除该标志。小程序改密页条件隐藏「当前密码」。迁移 `b3c4d5e6f7a8`（dev）/`b3c4d5e6f7a9`（pro）。
- **修复（启动）**：`run.sh` 将 `No module named 'application.database_url'` 误判为「数据库未配置」的问题——现 `export PYTHONPATH` 包含项目根、内嵌 Python 强制 `HIPP_RUN_ROOT` 与脚本目录一致、区分导入错误与连接串缺失；新增 `application/__init__.py`。见 `doc/91-qa/【启动】run.sh误报数据库配置与application.database_url缺失.md`。
- **需求变更 + 实现**：小程序去掉微信登录；默认改为手机号 + 短信验证码登录；验证码校验通过后若手机号不存在则自动创建账号。`POST /auth/sms/send` 发码（不要求已注册）；`POST /auth/login` 在 `platform=1` 且 `method=1` 时先验码再登录/建号。见 `hipp-uni/pages/login/login.vue`、`hipp-api/apps/vadmin/auth/utils/login.py`、`login_manage.py`、`crud.py`；设计见 `doc/01-or/【小程序登录】登录功能.md` 等。
- **小程序登录页**：用户协议、隐私政策改为**内置文案 + 弹窗滚动阅读**（滚动到底后方可确认返回），不再使用 webview 跳转外部 URL。文案见 `doc/99-ops/luo/*.txt` 与 `hipp-uni/common/legal/static-texts.js`。
- **小程序登录页**：协议首次确认后**本地缓存**已读状态，再次打开同一协议仅显示「返回」；两项均确认后**自动勾选**同意（用户可手动取消；取消后本页不再自动勾选直至再次完成弹窗确认）。

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
