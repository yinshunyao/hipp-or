# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【智能客服管理】Dify智能体接入管理.md` |
| 开发设计 | `hipp-or/doc/02-dr/03 智能客服管理/Dify智能体接入管理设计.md` |

# 测试范围

- 后端：智能客服 CRUD 接口、测试连通性接口、上架/下架接口
- 前端：列表页搜索与展示、配置弹窗表单交互、测试/保存/上架操作

# 测试用例

## 后端接口测试

| 编号 | 用例 | 前置条件 | 操作步骤 | 预期结果 | 自动化 |
|:---|:---|:---|:---|:---|:---|
| B01 | 创建智能客服 | 已登录管理员 | POST /vadmin/agent/agents，body: {api_server, app_key, remark, service_type?} | 201 返回新记录，status=draft, is_tested=False | pytest |
| B01b | 创建带类型 | 已登录管理员 | POST body 含 `service_type: 需求分析` | 返回记录含对应 `service_type` | pytest |
| B02 | 获取列表（无筛选） | 存在至少 1 条记录 | GET /vadmin/agent/agents | 返回列表和总数 | pytest |
| B03 | 关键词模糊查询 | 存在 name 含 "客服" 的记录 | GET /vadmin/agent/agents?keyword=客服 | 返回匹配记录 | pytest |
| B04 | 状态筛选 | 存在 draft 和 published 记录 | GET /vadmin/agent/agents?status=published | 仅返回 published | pytest |
| B04b | 类型筛选 | 存在不同 `service_type` 记录 | GET /vadmin/agent/agents?service_type=需求分析 | 仅返回该类型 | pytest |
| B05 | 编辑智能客服 | 记录存在 | PUT /vadmin/agent/agents/{id}，修改 remark | 返回更新后数据 | pytest |
| B06 | 测试连通性（成功，有 id） | Dify 服务可用 | POST /vadmin/agent/agents/test，Body 含 api_server、app_key、id、可选 service_type | is_tested=True，name/description/tags 已填充；有 id 时库内 `service_type` 同步 | pytest（mock httpx） |
| B06b | 测试连通性（成功，无 id） | 未保存 | POST /vadmin/agent/agents/test，id 为空 | 返回 data 含 id=null、is_tested=true，并回显 `service_type` | pytest（mock httpx） |
| B07 | 测试连通性（失败） | API 地址错误 | POST /vadmin/agent/agents/test | 返回错误信息 | pytest（mock httpx） |
| B08 | 上架（测试已通过） | is_tested=True | PUT /vadmin/agent/agents/{id}/publish | status=published | pytest |
| B09 | 上架（测试未通过） | is_tested=False | PUT /vadmin/agent/agents/{id}/publish | 返回错误：需先通过测试 | pytest |
| B10 | 下架 | status=published | PUT /vadmin/agent/agents/{id}/unpublish | status=draft | pytest |
| B11 | 软删除 | 记录存在 | DELETE /vadmin/agent/agents，body: [id] | is_delete=True，列表不再展示 | pytest |

## 前端页面测试

| 编号 | 用例 | 前置条件 | 操作步骤 | 预期结果 | 自动化 |
|:---|:---|:---|:---|:---|:---|
| F01 | 新增弹窗展示 | 在列表页 | 点击「新增智能客服」 | 弹窗弹出，表单为空 | Playwright |
| F02 | 填写并保存 | 弹窗已打开 | 输入 API 地址、APP_KEY、选择或输入类型、备注，点击「保存」 | 保存成功提示，弹窗关闭，列表刷新 | Playwright |
| F02b | 类型控件 | 弹窗已打开 | 打开类型下拉 | 可见「需求分析」「商业评估」，可输入新类型 | Playwright |
| F03 | 测试按钮 | 弹窗已打开并填写 | 点击「测试」 | 成功时下方展示智能客服信息；失败时提示错误 | Playwright |
| F04 | 上架按钮（未测试） | 弹窗中 is_tested=False | 点击「上架」 | 提示需先通过测试 | Playwright |
| F05 | 上架按钮（已测试） | 弹窗中 is_tested=True | 点击「上架」 | 上架成功，状态变为「已上架」 | Playwright |
| F06 | 编辑复用弹窗 | 列表中有记录 | 点击编辑按钮 | 弹窗弹出，已有数据回填 | Playwright |
| F07 | 关键词实时搜索 | 列表有数据 | 输入关键词 | 列表实时过滤 | Playwright |
| F08 | 状态下拉筛选 | 列表有数据 | 选择「已上架」 | 仅展示已上架记录 | Playwright |
| F09 | 头像展示 - emoji | 记录 icon 不为空 | 查看列表 | 展示 emoji + 背景色 | Playwright |
| F10 | 头像展示 - URL | 记录 icon 为空、icon_url 有值 | 查看列表 | 展示图片 | Playwright |
| F11 | 删除 | 列表中有记录 | 点击删除 | 确认后记录从列表消失 | Playwright |
| F12 | 列表操作 - 上架/下架 | 列表中有草稿/已上架记录 | 点击对应按钮 | 状态切换成功，列表刷新 | Playwright |
| F13 | 编辑智能体信息并保存生效 | 弹窗已测试成功（有智能体信息展示） | 修改名称/描述/标签，点击「保存」 | 保存成功，弹窗关闭；列表对应行展示为修改后的名称/描述/标签 | Playwright |
| F14 | 头像上传控件可用 | 弹窗已测试成功 | 看到头像上传控件与预览位 | 支持选择图片文件并触发上传请求；成功后预览更新 | 手工/Playwright（如具备测试图片文件） |

# 自动化测试标识

- 后端测试：使用 **pytest** + **httpx AsyncClient**，Dify 外部调用通过 **mock** 隔离
- 前端 E2E 测试：使用 **Playwright**，测试文件放置在 `hipp-or/test/e2e/agent-manager/`
