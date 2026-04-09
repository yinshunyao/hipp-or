#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除「小程序服务端微信 openid」绑定（vadmin_auth_user），便于测试游客/正式登录切换。

说明（与微信调试里 sid / token / hash 的关系）
----------------------------------------------
- 本项目的微信绑定只认数据库字段：wx_server_openid + is_wx_server_openid。
- 微信开发者工具或 webview 里看到的 sid、session_key、hash 等**不会**写入本表；
  它们多为会话/调试标识，与 hipp 后端 JWT（Authorization）也不是同一套东西。
- 若要从「已绑定微信」回到可测游客流，应清空上述两字段（或按 openid / 手机号定位用户后清空）。

用法（在 hipp-api 目录、已配置 .env 数据库）::

    .venv/bin/python scripts/clear_wx_server_openid.py --telephone 13800138000 --dry-run
    .venv/bin/python scripts/clear_wx_server_openid.py --user-id 12
    .venv/bin/python scripts/clear_wx_server_openid.py --wx-openid-exact oXXXX...
    .venv/bin/python scripts/clear_wx_server_openid.py --wx-openid-contains 5nXLGvm7lM --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

# 保证以「hipp-api 为工作目录」运行时能 import application / core
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_API_ROOT = os.path.dirname(_SCRIPT_DIR)
if _API_ROOT not in sys.path:
    sys.path.insert(0, _API_ROOT)

os.environ.setdefault("HIPP_RUN_ROOT", _API_ROOT)

from sqlalchemy import text  # noqa: E402

from core.database import session_factory  # noqa: E402


def _build_where(args: argparse.Namespace) -> tuple[str, dict]:
    if args.user_id is not None:
        return "id = :user_id", {"user_id": int(args.user_id)}
    if args.telephone:
        return "telephone = :telephone", {"telephone": str(args.telephone).strip()}
    if args.wx_openid_exact:
        return "wx_server_openid = :oid", {"oid": str(args.wx_openid_exact).strip()}
    if args.wx_openid_contains:
        return "wx_server_openid LIKE :pat", {"pat": f"%{str(args.wx_openid_contains).strip()}%"}
    raise SystemExit("内部错误：未指定匹配条件")


async def _run(args: argparse.Namespace) -> None:
    where_sql, params = _build_where(args)
    sel_sql = f"""
        SELECT id, telephone, user_type, wx_server_openid, is_wx_server_openid
        FROM vadmin_auth_user
        WHERE is_delete = 0 AND ({where_sql})
        """

    async with session_factory() as session:
        r = await session.execute(text(sel_sql), params)
        rows = r.mappings().all()
        if not rows:
            print("未找到匹配用户（is_delete=0）。")
            return
        print(f"将处理 {len(rows)} 行：")
        for row in rows:
            print(
                f"  id={row['id']} telephone={row['telephone']} user_type={row['user_type']} "
                f"is_wx_server_openid={row['is_wx_server_openid']} wx_server_openid={row['wx_server_openid']!r}"
            )
        if args.dry_run:
            print("(--dry-run 未写入数据库)")
            return
        upd_sql = f"""
            UPDATE vadmin_auth_user
            SET wx_server_openid = NULL, is_wx_server_openid = 0
            WHERE is_delete = 0 AND ({where_sql})
            """
        await session.execute(text(upd_sql), params)
        await session.commit()
        print("已清空 wx_server_openid，并将 is_wx_server_openid 置为 0。")


def main() -> None:
    p = argparse.ArgumentParser(description="清除用户的小程序 wx_server_openid 绑定（测试用）")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--user-id", type=int, metavar="ID", help="按用户主键 id")
    g.add_argument("--telephone", type=str, help="按手机号（11 位）")
    g.add_argument("--wx-openid-exact", type=str, help="按 wx_server_openid 精确匹配")
    g.add_argument("--wx-openid-contains", type=str, help="按 wx_server_openid 子串 LIKE 匹配（慎用，可能多行）")
    p.add_argument("--dry-run", action="store_true", help="只查询将要更新的行，不执行 UPDATE")
    args = p.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
