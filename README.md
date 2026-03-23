# hipp-or

hipp 需求对接工程：在 [kinit](https://github.com/vvandk/kinit) 基础上扩展 **管理端（hipp-admin）**、**后端 API（hipp-api）** 与 **小程序端（hipp-uni）**。

![对话列表.png](images/%E5%AF%B9%E8%AF%9D%E5%88%97%E8%A1%A8.png)  ![对话主界面](images/%E5%AF%B9%E8%AF%9D%E4%B8%BB%E7%95%8C%E9%9D%A2.png)


## 仓库结构（简要）

| 目录 | 说明 |
|:---|:---|
| `hipp-api/` | FastAPI 后端：认证、管理端业务、**小程序对话 `/mp/chat`** |
| `hipp-admin/` | Web 管理端（Vue）：含 **智能客服 / Dify 智能体** 配置与上架 |
| `hipp-uni/` | uni-app 小程序：默认进入 **对话收件箱**，调用后端对话接口 |
| `doc/` | 需求（01-or）、设计（02-dr）、测试设计（03-tr）、运维（99-ops） |

---

## 智能体服务（当前实现）

智能体能力由 **管理端维护 Dify 接入信息** + **后端代持密钥并调用 Dify** + **小程序仅持会话与消息** 三部分组成。

### 1. 数据与配置（管理端 → 数据库）

- 智能体记录在表 **`vadmin_agent`**（见设计文档），核心字段包括：
  - **`api_server`**：Dify API 基准地址（须含 `/v1`，如 `https://your-dify/v1`）
  - **`app_key`**：Dify 应用密钥（仅服务端使用，**不下发小程序**）
  - **`status`**：`draft` / `published`；小程序侧仅对 **已上架（published）** 的智能体展示「可开聊」；未上架或已删除时历史会话只读
- 管理端接口前缀：**`/vadmin/agent`**（列表、创建、编辑、测试连通、上架/下架等），详见 `doc/02-dr/03 智能客服管理/Dify智能体接入管理设计.md`。

### 2. 小程序对话 API（后端）

- 路由前缀：**`/mp/chat`**（在 `hipp-api/application/urls.py` 注册）
- 鉴权：与现有移动端一致，请求头 **`Authorization: Bearer <access_token>`**（登录接口 `/auth/login` 等颁发的 JWT）
- **安全约定**：`api_server`、`app_key` **仅由服务端在发消息时按 `agent_id` 从库中读取**；客户端不得传 Dify 地址或密钥
- 与 Dify 交互：使用官方 Chat 应用 **`POST {api_server}/v1/chat-messages`**；主路径为 **`response_mode=streaming`**（SSE），同步 **`blocking`** 作为降级；Dify 侧用户标识为 **`user-{vadmin_auth_user.id}`**，多轮通过会话表中的 **`dify_conversation_id`** 对齐
- 主要能力：收件箱合并、会话 CRUD、消息列表、**流式/非流式发送**；智能体不可发送时返回业务错误（如 **`46001`**），详见 `doc/02-dr/04 小程序对话/小程序用户对话设计.md`

### 3. 小程序端（hipp-uni）

- 默认进入：**`pages/chat/index`**（对话收件箱）；登录成功与路由守卫中已登录访问登录页时，统一重定向到该页
- API 封装：`hipp-uni/common/request/api/mp/chat.js`（含微信小程序 `enableChunked` + `onChunkReceived` 解析 SSE 增量）
- TabBar：当前为 **对话 / 工作台 / 我的**（已下线「首页」Tab）

### 4. 环境变量（与 Dify 相关）

在 `hipp-api/.env` 中可参考 `hipp-api/.env.example`：

- **`HIPP_DIFY_HTTPX_VERIFY`**：后端调用 Dify 时是否校验 HTTPS 证书；内网自签可设为 `false`（仅建议开发/内网）

---

## 详细文档索引

| 主题 | 路径 |
|:---|:---|
| Dify 智能体管理（管理端） | `doc/02-dr/03 智能客服管理/Dify智能体接入管理设计.md` |
| 小程序用户对话（含 `/mp/chat` 与 Dify 流式） | `doc/02-dr/04 小程序对话/小程序用户对话设计.md` |
| 测试设计 | `doc/03-tr/03 智能客服管理/`、`doc/03-tr/04 小程序对话/` |

---

## 特别感谢 kinit

本项目基于 [kinit](https://github.com/vvandk/kinit) 二次开发。
