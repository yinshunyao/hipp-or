# 问题描述

在 Ubuntu 生产环境首次部署 `hipp-api` 时，执行 `hipp-or/hipp-api/run.sh` 报错：

- `pymysql.err.OperationalError: (1049, "Unknown database 'hipp'")`
- 随后 `alembic upgrade head` 失败，`main.py init` 中断。

复现条件：目标 MySQL 实例可连通，但 `HIPP_DATABASE_URL`（或分项变量）指向的数据库尚未创建，且当前是首次运行（会先创建 `.venv` 并进入 `bootstrap` 分支）。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【小程序登录】登录功能.md` |
| 开发设计 | `hipp-or/doc/02-dr/02 登录认证与初始化.md` |
| 测试设计 | `hipp-or/doc/03-tr/02 登录认证与初始化测试设计.md` |

# 根因分析

`run.sh` 中存在两条启动路径：

1. **首次启动（无 `.venv`）**：进入 `bootstrap()`，此前逻辑在安装依赖后直接执行 `run_db_init`。
2. **非首次启动（已有 `.venv`）**：走 `ensure_db_schema_before_run`，其中包含 `1049` 自动建库分支。

问题在于首次启动路径未复用统一的“建库 + 核心表检查”逻辑，导致数据库不存在时，`alembic upgrade head` 先执行并失败。

# 涉及文件

- `hipp-or/hipp-api/run.sh`：`bootstrap()` 将直接 `run_db_init` 调整为 `ensure_db_schema_before_run`，首次启动也先触发自动建库/缺表检测。

# 设计约束更新

- 启动脚本的首次运行路径与常规运行路径必须使用同一套数据库前置检查逻辑，避免分支行为不一致。
