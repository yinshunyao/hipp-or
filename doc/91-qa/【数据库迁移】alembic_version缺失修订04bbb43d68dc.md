# 问题描述

在生产（或共享）MySQL 上执行 `hipp-api` 迁移时失败：

- `Can't locate revision identified by '04bbb43d68dc'`
- 命令示例：`.venv/bin/python main.py migrate --env dev`（日志为 `online` 模式，实际连的是 `HIPP_DATABASE_URL` 所指向的库）

复现条件：`alembic_version` 表中当前版本号为 `04bbb43d68dc`，但部署包内的 `alembic/versions_dev`（或对应 `version_locations`）中不存在该 revision 的脚本文件（常见于库由旧模板/其他分支迁移过、或历史脚本被删未同步）。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【kinit-api】MongoDB关闭时MySQL兼容适配.md` |
| 开发设计 | `hipp-or/doc/02-dr/02 登录认证与初始化.md` |
| 测试设计 | `hipp-or/doc/03-tr/02 登录认证与初始化测试设计.md` |

# 根因分析

Alembic 启动时会根据 `alembic_version.version_num` 在**当前配置的** `version_locations` 中解析迁移图。若数据库里记录的 revision id 在磁盘上不存在任何 `revision = "..."` 定义，则在 `upgrade head` 的第一步就会报错，**不会执行**任何 DDL。

`04bbb43d68dc` 在本仓库历史中未保留对应文件时，即触发上述错误。

# 涉及文件

- `hipp-or/hipp-api/alembic/versions_dev/04bbb43d68dc_placeholder_missing_revision.py`：占位修订（`upgrade`/`downgrade` 为空），使迁移图可解析。
- `hipp-or/hipp-api/alembic/versions_dev/c146cc30b075_3_10_1.py`：`down_revision` 由 `None` 调整为 `04bbb43d68dc`，与占位修订衔接为单链。

# 设计约束更新

- 与既有 `8fb508aa2dd3_placeholder_missing_revision.py` 同类问题：**优先在仓库中补全缺失 revision**（no-op），避免仅改库内 `alembic_version` 却无脚本可追溯。
- **部署前**应保证 `migrate` 所用 `--env`（`dev` / `pro`）与当初写入该库的迁移集一致；`dev` 与 `pro` 使用不同的 `version_locations`，混用会导致版本号与脚本集不匹配。

# 运维处理说明（升级前必读）

1. **备份**数据库。
2. 拉取包含占位修订的代码后，在 `hipp-api` 目录执行迁移前，可先确认：
   - `SELECT version_num FROM alembic_version;`
   - 若仍为 `04bbb43d68dc`，且占位脚本已就位，则 `upgrade head` 会继续从 `c146cc30b075` 起应用后续脚本。
3. **若**当前库表结构**已经**与目标 `head` 一致（例如曾手工建表或从备份恢复），仅版本号悬空，可改用 **stamp** 将版本直接标到目标修订，避免重复建表失败（需在运维窗口由熟悉表结构的人员执行）：
   - `alembic --name <env> stamp <revision>`  
   具体 `<revision>` 以 `alembic heads` 与现场表结构核对为准。
