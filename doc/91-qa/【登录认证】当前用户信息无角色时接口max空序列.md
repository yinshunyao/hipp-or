## 问题描述

- 微信小程序或管理端在登录后请求 `GET /vadmin/auth/user/admin/current/info` 获取当前用户信息时，服务端进入全局 `value_exception_handler`，日志：`max() iterable argument is empty`，接口未向客户端返回有效业务数据（尽管 HTTP 可能仍为 200）。

## 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【小程序登录】登录功能.md` |
| 开发设计 | `hipp-or/doc/02-dr/02 登录认证与初始化.md` |
| 测试设计 | `hipp-or/doc/03-tr/02 登录认证与初始化测试设计.md` |

## 根因分析

- `FullAdminAuth.validate_user` 在非 `is_all` 路径会调用 `AuthValidation.get_user_data_range`。
- 该函数对非超级管理员用户使用 `data_range = max([i.data_range for i in user.roles])`。当用户**未关联任何角色**（`user.roles` 为空）时，列表推导得到空序列，`max()` 抛出 `ValueError`，被 `value_exception_handler` 捕获。
- 易出现场景：短信自动建号等流程创建 `is_staff=True` 用户后，若尚未在后台分配角色，即会触发。

## 涉及文件

- `hipp-or/hipp-api/apps/vadmin/auth/utils/validation/auth.py`：`get_user_data_range` 在 `role_ranges` 为空时使用 `data_range=0`（仅本人数据范围），与「无角色则最小数据范围」语义一致，避免 `max` 空序列。

## 设计约束更新

- 员工用户（非超级管理员）**零角色**时，数据权限范围按 **0（仅本人）** 处理，`dept_ids` 为空列表；权限集合仍由 `get_user_permissions` 对空角色自然得到空集（与既有逻辑一致）。
