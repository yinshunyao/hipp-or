# 问题描述

在 **hipp-admin**「系统设置」中上传站点 **ICO 图标**时，用户已选择真实 `.ico` 文件，前端 `beforeUpload` 仍提示类似「上传ICO图标必须是 ico 格式」，导致无法上传。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | 待定位（继承上游 vadmin 系统配置/站点外观能力） |
| 开发设计 | 待定位 |
| 测试设计 | 待定位 |

# 根因分析

1. **前端**：`Basic.vue` 中 ICO 校验仅判断 `rawFile.type === 'image/x-icon'`。多数浏览器对 `.ico` 会报告 `image/vnd.microsoft.icon`，部分环境还会出现**空 MIME** 或 `application/octet-stream`，从而误判为非 ICO。
2. **后端**（顺带加固）：`FileBase.IMAGE_ACCEPT` 未包含 `image/vnd.microsoft.icon` 等常见 ICO MIME，`validate_file` 对 `content-type` 为**大小写敏感**且未对「`application/octet-stream` + `.ico` 文件名」做合理放行，存在与前端一致的拒收风险。

# 涉及文件

- `hipp-or/hipp-admin/src/views/Vadmin/System/Settings/components/Basic.vue`：ICO MIME 集合、空/octet-stream 时配合 `.ico` 扩展名校验；`accept` 补充常见类型与 `.ico`。
- `hipp-or/hipp-api/utils/file/file_base.py`：扩展 `IMAGE_ACCEPT`；`validate_file` 小写比较 MIME，并对 `.ico` + 空/octet-stream 放行。
- `hipp-or/hipp-api/utils/file/file_manage.py`：`async_copy_file` 兼容绝对路径、`/media/...`、项目相对路径，避免重复拼接 `BASE_DIR` 导致源文件不存在。
- `hipp-or/hipp-api/test/test_utils/test_file_base_validate.py`：ICO 校验回归用例。

# 设计约束更新

- 站点 ICO 上传：**浏览器报告的 MIME 不唯一**，校验须以「已知 ICO MIME 列表 + `.ico` 扩展名回退」与后端一致策略为准，避免误伤合法文件。
