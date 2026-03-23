# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【智能客服管理】Dify智能体接入管理.md` |
| 测试设计 | `hipp-or/doc/03-tr/03 智能客服管理/Dify智能体接入管理测试设计.md` |

# 功能设计

## 后端

### 数据模型

表名：`vadmin_agent`

| 字段 | 类型 | 约束 | 说明 |
|:---|:---|:---|:---|
| id | Integer | PK | 主键 |
| api_server | String(500) | NOT NULL | Dify API 服务器地址 |
| app_key | String(500) | NOT NULL | Dify APP_KEY |
| remark | String(500) | nullable | 备注 |
| name | String(255) | nullable | 智能体名称（来自 Dify /v1/info） |
| description | Text | nullable | 智能体描述（来自 Dify） |
| tags | Text | nullable | 标签 JSON 数组字符串（来自 Dify） |
| mode | String(50) | nullable | 应用模式（来自 Dify） |
| icon_type | String(20) | nullable | 图标类型：emoji / image |
| icon | String(255) | nullable | 图标内容（emoji 字符） |
| icon_background | String(20) | nullable | 图标背景色 |
| icon_url | String(500) | nullable | 图标图片 URL |
| webapp_config | Text | nullable | Dify /v1/site 完整 JSON |
| status | String(20) | NOT NULL, default='draft' | 上架状态：draft / published |
| is_tested | Boolean | default=False | 是否通过测试 |
| create_user_id | Integer | FK → vadmin_auth_user.id | 创建人 |
| create_datetime | DateTime | server_default=now() | 继承 BaseModel |
| update_datetime | DateTime | onupdate=now() | 继承 BaseModel |
| delete_datetime | DateTime | nullable | 继承 BaseModel |
| is_delete | Boolean | default=False | 继承 BaseModel |

### API 接口

基础前缀：`/vadmin/agent`

| 方法 | 路径 | 说明 | 权限 |
|:---|:---|:---|:---|
| GET | /agents | 获取智能客服列表（分页、搜索） | FullAdminAuth |
| POST | /agents | 创建智能客服 | FullAdminAuth |
| PUT | /agents/{id} | 编辑智能客服（请求体中 **null 表示不修改** 该字段；仅非 null 字段参与 UPDATE） | FullAdminAuth |
| DELETE | /agents | 批量软删除 | FullAdminAuth |
| POST | /agents/test | 测试连通性（Body：`api_server`、`app_key`、`remark`、`id` 可选；有 `id` 时更新该条并落库） | FullAdminAuth |
| PUT | /agents/{id}/publish | 上架 | FullAdminAuth |
| PUT | /agents/{id}/unpublish | 下架 | FullAdminAuth |
| GET | /agents/{id} | 获取单条详情 | FullAdminAuth |

#### 测试接口逻辑（POST /agents/test）

1. 使用请求体中的 `api_server`、`app_key`（及可选 `remark`、`id`）调用 Dify，**不再**仅按 id 读库（避免表单已改未保存时仍用旧配置）。
2. 若 `id` 有值：更新该记录的配置字段并写入 Dify 同步结果；若 `id` 为空：不落库，仅返回同步结果供前端展示。
3. 使用 httpx 异步调用 `GET {api_server}/info`（Header: `Authorization: Bearer {app_key}`），其中 `api_server` 须为含 `/v1` 的基准地址（如 `http://host/v1`）。
4. 使用 httpx 异步调用 `GET {api_server}/site`（同上）
5. 将 info / site 响应写入模型字段（与现有一致），`is_tested = True`
6. 有 `id` 时返回更新后的完整记录；无 `id` 时返回不含 `create_datetime` 等库字段的展示对象

#### 上架接口逻辑（PUT /agents/{id}/publish）

- 检查 `is_tested == True`，否则返回错误
- 更新 `status = 'published'`

#### 列表查询参数

- `keyword`：模糊匹配 name、description、tags（OR 条件）
- `status`：精确匹配上架状态

## 前端

### 页面结构

智能客服管理为单页面，包含两部分：

1. **列表页**（`AgentManager.vue`）
   - 搜索区：关键词输入框（搜索名称/描述/标签）+ 上架状态下拉（全部/草稿/已上架）
   - 工具栏：「新增智能客服」按钮
   - 数据表格列：头像、名称、描述、标签、备注、上架状态、操作
   - 操作列按钮：编辑、上架/下架、测试、删除

2. **配置弹窗**（`components/Write.vue`，使用 ElDialog）
   - 表单区：API 服务器地址、APP_KEY、备注
   - 操作按钮：测试、保存、上架
   - 信息展示区（测试成功后显示）：头像、名称、描述、标签、备注、状态

### 头像展示逻辑

- 优先展示 `icon`（emoji）配合 `icon_background` 背景色
- 若 `icon` 为空，展示 `icon_url` 图片
- 两者均为空则展示默认图标

### 路由

组件路径：`src/views/Vadmin/AgentManager/AgentManager.vue`

- 前端在 `router/index.ts` 的 `asyncRouterMap` 中声明了 `/agent` → `/agent/manager`。`permission` 在生成动态路由时**始终用前端的 `/agent` 覆盖**后台同 path（避免后台 component/path 与子路由不一致时落入通配路由 → 404）。
- **后台菜单（`vadmin_auth_menu`）配置要点**（与框架 `generateRoutesByServer` + `import.meta.glob` 一致）：
  - **目录（menu_type=0）**：`path` 填 `/agent`（带前导 `/`），`component` 填 **`#`**（表示 Layout），勿填页面组件路径。
  - **页面（menu_type=1）**：`path` 填 **`manager`**（相对父级，不要写成 `/agent/manager`），`component` 填 **`views/Vadmin/AgentManager/AgentManager`**（无 `.vue`；也可填 `Vadmin/AgentManager/AgentManager`，前端已做 `views/` 前缀兼容）。
  - 填错 `component` 会导致动态 import 失败，路由匹配后无组件，最终进入 **404**。

完整访问地址：`/agent/manager`

### API 客户端

文件路径：`src/api/vadmin/agent_manager/index.ts`

# 约束与边界

- Dify 接口调用超时设置为 10 秒
- APP_KEY 在数据库中明文存储（当前阶段不加密）
- 标签（tags）以 JSON 数组字符串存储，前端解析展示为 Tag 组件
- 本期不涉及智能客服的对话功能，仅做接入管理
