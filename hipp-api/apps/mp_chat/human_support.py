# -*- coding: utf-8 -*-
"""人工客服会话：角色名、随机分配。"""

from __future__ import annotations

from sqlalchemy import false, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from apps.vadmin.auth.models import VadminRole, VadminUser, vadmin_auth_user_roles

HUMAN_SUPPORT_ROLE_NAME = "人工客服"


async def pick_random_human_staff_user_id(db: AsyncSession) -> int | None:
    """随机 1 名可用人工客服（角色名称为「人工客服」）。"""
    sql = (
        select(VadminUser.id)
        .join(vadmin_auth_user_roles, vadmin_auth_user_roles.c.user_id == VadminUser.id)
        .join(VadminRole, VadminRole.id == vadmin_auth_user_roles.c.role_id)
        .where(
            VadminRole.name == HUMAN_SUPPORT_ROLE_NAME,
            VadminRole.disabled == false(),
            VadminUser.is_active == true(),
            VadminUser.is_delete == false(),
        )
        .order_by(func.rand())
        .limit(1)
    )
    r = await db.execute(sql)
    row = r.first()
    return int(row[0]) if row else None
