# -*- coding: utf-8 -*-
"""
业务数据全量导出 / 导入（ZIP + JSON）。

导入策略：在单事务内 SET FOREIGN_KEY_CHECKS=0，按表顺序清空后按序插入，
恢复导出包中的主键与关联，等价于「整库替换为包内快照」（默认策略）。
"""
from __future__ import annotations

import base64
import io
import json
import zipfile
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.exception import CustomException

FORMAT_VERSION = "1.0"
APP_ID = "hipp-or"

# 插入顺序（父表在前）；删除时逆序
TABLES_ORDER: list[str] = [
    "vadmin_system_settings_tab",
    "vadmin_system_settings",
    "vadmin_system_dict_type",
    "vadmin_system_dict_details",
    "vadmin_auth_dept",
    "vadmin_auth_menu",
    "vadmin_auth_role",
    "vadmin_auth_user",
    "vadmin_auth_user_roles",
    "vadmin_auth_role_menus",
    "vadmin_auth_user_depts",
    "vadmin_auth_role_depts",
    "vadmin_agent",
    "vadmin_resource_images",
    "vadmin_help_issue_category",
    "vadmin_help_issue",
    "vadmin_chat_session",
    "vadmin_chat_message",
    "vadmin_system_task_group",
    "vadmin_system_task",
    "scheduler_task_record",
    "apscheduler_jobs",
    "vadmin_record_operation",
    "vadmin_record_login",
    "vadmin_record_sms_send",
]


def _fix_import_value(v: Any) -> Any:
    if isinstance(v, dict) and "__binary__" in v and len(v) == 1:
        return base64.b64decode(v["__binary__"])
    return v


async def _fetch_table_rows(session: AsyncSession, table: str) -> list[dict[str, Any]]:
    sql = text(f"SELECT * FROM `{table}`")
    result = await session.execute(sql)
    rows = []
    for row in result.mappings().all():
        d = dict(row)
        fixed = {}
        for k, val in d.items():
            if isinstance(val, bytes):
                fixed[k] = {"__binary__": base64.b64encode(val).decode("ascii")}
            elif isinstance(val, (datetime, date)):
                fixed[k] = val.isoformat() if hasattr(val, "isoformat") else val
            elif isinstance(val, Decimal):
                fixed[k] = str(val)
            elif val is None:
                fixed[k] = None
            else:
                fixed[k] = val
        rows.append(fixed)
    return rows


async def build_export_zip(session: AsyncSession, exported_by: str) -> tuple[bytes, str]:
    manifest = {
        "format_version": FORMAT_VERSION,
        "app": APP_ID,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "exported_by": exported_by,
        "import_strategy": "full_replace",
        "tables": TABLES_ORDER,
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for table in TABLES_ORDER:
            try:
                rows = await _fetch_table_rows(session, table)
            except Exception as e:
                raise CustomException(
                    msg=f"导出表 `{table}` 失败：{e!s}",
                    desc="data_export",
                ) from e
            zf.writestr(
                f"data/{table}.json",
                json.dumps(rows, ensure_ascii=False),
            )
    buf.seek(0)
    name = f"hipp-or-data-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    return buf.getvalue(), name


def _read_manifest(zf: zipfile.ZipFile) -> dict[str, Any]:
    try:
        raw = zf.read("manifest.json").decode("utf-8")
    except KeyError as e:
        raise CustomException(msg="无效的导出包：缺少 manifest.json", desc="data_import") from e
    try:
        m = json.loads(raw)
    except json.JSONDecodeError as e:
        raise CustomException(msg=f"manifest.json 解析失败：{e!s}", desc="data_import") from e
    if m.get("format_version") != FORMAT_VERSION:
        raise CustomException(
            msg=f"不支持的导出格式版本：{m.get('format_version')!r}，需要 {FORMAT_VERSION}",
            desc="data_import",
        )
    if m.get("app") != APP_ID:
        raise CustomException(
            msg=f"导出包 app 标识不匹配：期望 {APP_ID!r}，实际 {m.get('app')!r}",
            desc="data_import",
        )
    return m


async def run_import(session: AsyncSession, file_bytes: bytes) -> dict[str, Any]:
    buf = io.BytesIO(file_bytes)
    try:
        zf = zipfile.ZipFile(buf, "r")
    except zipfile.BadZipFile as e:
        raise CustomException(msg="不是有效的 ZIP 文件", desc="data_import") from e

    with zf:
        manifest = _read_manifest(zf)
        tables_in_manifest = manifest.get("tables") or []
        if set(tables_in_manifest) != set(TABLES_ORDER):
            raise CustomException(
                msg="manifest 中表清单与当前系统不一致，请使用同版本系统导出的包",
                desc="data_import",
            )

        # 预读所有表数据并校验存在 data/*.json
        loaded: dict[str, list[dict[str, Any]]] = {}
        for table in TABLES_ORDER:
            path = f"data/{table}.json"
            try:
                raw = zf.read(path).decode("utf-8")
            except KeyError as e:
                raise CustomException(
                    msg=f"无效的导出包：缺少 {path}",
                    desc="data_import",
                ) from e
            try:
                rows = json.loads(raw)
            except json.JSONDecodeError as e:
                raise CustomException(
                    msg=f"{path} JSON 解析失败：{e!s}",
                    desc="data_import",
                ) from e
            if not isinstance(rows, list):
                raise CustomException(msg=f"{path} 必须为 JSON 数组", desc="data_import")
            loaded[table] = rows

        await session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        try:
            for table in reversed(TABLES_ORDER):
                await session.execute(text(f"DELETE FROM `{table}`"))

            total_inserted = 0
            for table in TABLES_ORDER:
                rows = loaded[table]
                if not rows:
                    continue
                for row in rows:
                    fixed_row = {k: _fix_import_value(v) for k, v in row.items()}
                    cols = list(fixed_row.keys())
                    placeholders = ", ".join(f":{c}" for c in cols)
                    col_sql = ", ".join(f"`{c}`" for c in cols)
                    stmt = text(f"INSERT INTO `{table}` ({col_sql}) VALUES ({placeholders})")
                    await session.execute(stmt, fixed_row)
                    total_inserted += 1
        finally:
            await session.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    return {
        "import_strategy": manifest.get("import_strategy", "full_replace"),
        "tables": TABLES_ORDER,
        "rows_inserted": total_inserted,
        "message": "导入完成：已按「全量替换」策略写入当前库",
    }
