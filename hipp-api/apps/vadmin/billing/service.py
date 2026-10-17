# -*- coding: utf-8 -*-
"""会话费用解析（全局 + 用户专属）。"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.vadmin.billing.models.session_fee import DEFAULT_SESSION_FEE, SESSION_FEE_KEY


def normalize_amount(value) -> Decimal:
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("金额格式不正确") from exc
    if amount < 0:
        raise ValueError("金额不能为负数")
    if amount > Decimal("999999.99"):
        raise ValueError("金额过大")
    return amount


async def get_global_session_fee(db: AsyncSession) -> Decimal:
    row = (
        await db.execute(
            text(
                "SELECT config_value FROM vadmin_or_billing_setting "
                "WHERE config_key = :key AND is_delete = 0 LIMIT 1"
            ),
            {"key": SESSION_FEE_KEY},
        )
    ).first()
    if not row or row[0] in (None, ""):
        return DEFAULT_SESSION_FEE
    try:
        return normalize_amount(row[0])
    except ValueError:
        return DEFAULT_SESSION_FEE


async def set_global_session_fee(db: AsyncSession, amount: Decimal) -> Decimal:
    amount = normalize_amount(amount)
    existing = (
        await db.execute(
            text(
                "SELECT id FROM vadmin_or_billing_setting "
                "WHERE config_key = :key AND is_delete = 0 LIMIT 1"
            ),
            {"key": SESSION_FEE_KEY},
        )
    ).first()
    if existing:
        await db.execute(
            text(
                "UPDATE vadmin_or_billing_setting "
                "SET config_value = :val, update_datetime = NOW() "
                "WHERE id = :id"
            ),
            {"val": f"{amount:.2f}", "id": existing[0]},
        )
    else:
        await db.execute(
            text(
                "INSERT INTO vadmin_or_billing_setting "
                "(config_key, config_value, is_delete, create_datetime, update_datetime) "
                "VALUES (:key, :val, 0, NOW(), NOW())"
            ),
            {"key": SESSION_FEE_KEY, "val": f"{amount:.2f}"},
        )
    return amount


async def get_user_override(db: AsyncSession, user_id: int) -> Decimal | None:
    row = (
        await db.execute(
            text(
                "SELECT amount FROM vadmin_or_user_session_fee "
                "WHERE user_id = :uid AND is_delete = 0 LIMIT 1"
            ),
            {"uid": user_id},
        )
    ).first()
    if not row:
        return None
    return normalize_amount(row[0])


async def resolve_session_fee(db: AsyncSession, user_id: int) -> tuple[Decimal, bool]:
    """返回 (生效金额, 是否专属)。"""
    override = await get_user_override(db, user_id)
    if override is not None:
        return override, True
    return await get_global_session_fee(db), False


async def set_user_session_fee(db: AsyncSession, user_id: int, amount: Decimal) -> Decimal:
    amount = normalize_amount(amount)
    existing = (
        await db.execute(
            text(
                "SELECT id FROM vadmin_or_user_session_fee "
                "WHERE user_id = :uid ORDER BY is_delete ASC, id DESC LIMIT 1"
            ),
            {"uid": user_id},
        )
    ).first()
    if existing:
        await db.execute(
            text(
                "UPDATE vadmin_or_user_session_fee "
                "SET amount = :amt, is_delete = 0, delete_datetime = NULL, "
                "update_datetime = NOW() WHERE id = :id"
            ),
            {"amt": f"{amount:.2f}", "id": existing[0]},
        )
    else:
        await db.execute(
            text(
                "INSERT INTO vadmin_or_user_session_fee "
                "(user_id, amount, is_delete, create_datetime, update_datetime) "
                "VALUES (:uid, :amt, 0, NOW(), NOW())"
            ),
            {"uid": user_id, "amt": f"{amount:.2f}"},
        )
    return amount


async def clear_user_session_fee(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        text(
            "UPDATE vadmin_or_user_session_fee "
            "SET is_delete = 1, delete_datetime = NOW(), update_datetime = NOW() "
            "WHERE user_id = :uid AND is_delete = 0"
        ),
        {"uid": user_id},
    )


async def search_users_with_fee(
    db: AsyncSession,
    *,
    q: str = "",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict], int]:
    page = max(1, int(page or 1))
    limit = min(100, max(1, int(limit or 20)))
    offset = (page - 1) * limit
    global_fee = await get_global_session_fee(db)
    where = "u.is_delete = 0"
    params: dict = {"limit": limit, "offset": offset, "gfee": f"{global_fee:.2f}"}
    if (q or "").strip():
        where += (
            " AND (u.telephone LIKE :kw OR u.name LIKE :kw OR IFNULL(u.nickname,'') LIKE :kw)"
        )
        params["kw"] = f"%{q.strip()}%"

    count_row = (
        await db.execute(
            text(f"SELECT COUNT(1) FROM vadmin_auth_user u WHERE {where}"),
            params,
        )
    ).first()
    total = int(count_row[0] if count_row else 0)

    rows = (
        await db.execute(
            text(
                f"""
                SELECT u.id, u.name, u.nickname, u.telephone, f.amount AS override_amount
                FROM vadmin_auth_user u
                LEFT JOIN vadmin_or_user_session_fee f
                  ON f.user_id = u.id AND f.is_delete = 0
                WHERE {where}
                ORDER BY u.id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
    ).all()

    items = []
    for r in rows:
        override = None
        if r.override_amount is not None:
            try:
                override = float(normalize_amount(r.override_amount))
            except ValueError:
                override = None
        effective = override if override is not None else float(global_fee)
        items.append(
            {
                "user_id": int(r.id),
                "name": r.name or "",
                "nickname": r.nickname or "",
                "telephone": r.telephone or "",
                "override_amount": override,
                "effective_amount": effective,
                "is_override": override is not None,
            }
        )
    return items, total
