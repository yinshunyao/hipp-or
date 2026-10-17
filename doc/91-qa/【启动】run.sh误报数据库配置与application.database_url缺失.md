# 问题描述

生产环境通过 `hipp-api/run.sh` 启动后端时，日志反复出现：

- `[run.sh] 数据库配置无效或未配置： No module named 'application.database_url'`
- 并提示在 `.env` 中设置 `HIPP_DATABASE_URL` 等。

复现条件（典型）：部署目录不完整（缺少 `application/database_url.py`）、或进程环境变量 `HIPP_RUN_ROOT` 指向非 `run.sh` 所在项目根、或 `PYTHONPATH` 未包含项目根；也可能在 supervisor/systemd 中误配工作目录。

# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【登录认证】账号与手机号登录及管理员初始化.md` |
| 开发设计 | `hipp-or/doc/02-dr/02 登录认证与初始化.md` |
| 测试设计 | `hipp-or/doc/03-tr/02 登录认证与初始化测试设计.md` |

# 根因分析

1. **真实错误为 `ModuleNotFoundError`**：Python 无法加载 `application.database_url`（代码路径或 `sys.path`/`PYTHONPATH` 问题），并非必然缺少数据库 URL 环境变量。
2. **`run.sh` 内嵌 `python -c` 将任意异常统一包装**为「数据库配置无效」，导致运维误判为仅 `.env` 问题。
3. **`application` 目录曾无 `__init__.py`**：在部分运行/打包环境下不利于稳定识别为常规包（与显式包相比）。

# 涉及文件

- `hipp-or/hipp-api/application/__init__.py`：新增，使 `application` 为显式包。
- `hipp-or/hipp-api/run.sh`：`export PYTHONPATH` 包含项目根；`require_database_url` / `check_core_tables_present` 子进程强制 `HIPP_RUN_ROOT="$ROOT"`；区分 `ModuleNotFoundError` 与数据库 URL 配置错误并输出对应提示。

# 设计约束更新

- `run.sh` 中用于校验数据库配置的内嵌 Python **必须以 `run.sh` 所在目录为项目根** 解析 `application.*`，且错误提示应区分「代码/路径不可导入」与「环境变量未配置」。
- 生产部署须保留 **完整 `hipp-api` 源码树**（含 `application/`），supervisor `directory` / systemd `WorkingDirectory` 与 `run.sh` 所在目录一致。
