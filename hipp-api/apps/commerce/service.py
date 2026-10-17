# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from application import settings
from apps.commerce.biz_codes import (
    ENTITLEMENT_INVALID_CODE,
    ENTITLEMENT_INVALID_MSG,
    ENTITLEMENT_SCENE_DENIED_CODE,
    ENTITLEMENT_SCENE_DENIED_MSG,
    ENTITLEMENT_USED_CODE,
    ENTITLEMENT_USED_MSG,
    ENTITLEMENT_VOID_CODE,
    ENTITLEMENT_VOID_MSG,
)
from apps.commerce.models import VadminOrChannelOrder, VadminOrEntitlement
from apps.vadmin.auth.crud import UserDal
from apps.vadmin.auth.models import VadminUser
from apps.vadmin.auth.utils.login_manage import LoginManage
from apps.vadmin.auth.utils.password_flags import user_must_set_password_without_old
from core.exception import CustomException
from datetime import timedelta as Td

USER_TYPE_ENTITLEMENT = "entitlement"
SERVICE_TYPE_REQUIREMENT = "需求分析"
STATUS_UNUSED = "unused"
STATUS_BOUND = "bound"
STATUS_USED = "used"
STATUS_VOID = "void"
STATUS_EXPIRED = "expired"

ORDER_PAID = "paid"
ORDER_REDEEMED = "redeemed"
ORDER_REFUNDED = "refunded"

ORDER_STATUS_LABEL = {
    ORDER_PAID: "已支付",
    ORDER_REDEEMED: "已核销",
    ORDER_REFUNDED: "已退费",
}

ENTITLEMENT_STATUS_LABEL = {
    STATUS_UNUSED: "未使用",
    STATUS_BOUND: "已绑定",
    STATUS_USED: "已核销",
    STATUS_VOID: "已作废",
    STATUS_EXPIRED: "已过期",
}

CHANNEL_LABEL = {
    "manual": "手工",
    "offline": "线下",
    "xhs": "小红书",
}


def channel_label(channel: str | None) -> str:
    c = (channel or "").strip()
    return CHANNEL_LABEL.get(c, c or "-")


def entitlement_status_label(status: str | None) -> str:
    s = (status or "").strip()
    return ENTITLEMENT_STATUS_LABEL.get(s, s or "-")


def access_base() -> str:
    return (getattr(settings, "OR_ACCESS_BASE", None) or "").rstrip("/")


def short_url_for(token: str) -> str:
    base = access_base()
    tok = (token or "").strip()
    if not base:
        return f"/a/{tok}"
    return f"{base}/{tok}"


def _new_token() -> str:
    return secrets.token_urlsafe(18)


async def _get_by_token(db: AsyncSession, token: str) -> VadminOrEntitlement | None:
    tok = (token or "").strip()
    if not tok:
        return None
    q = await db.execute(
        select(VadminOrEntitlement).where(
            VadminOrEntitlement.token == tok,
            VadminOrEntitlement.is_delete == false(),
        )
    )
    return q.scalar_one_or_none()


def _touch_expired(ent: VadminOrEntitlement) -> bool:
    if ent.status in (STATUS_USED, STATUS_VOID, STATUS_EXPIRED):
        return ent.status == STATUS_EXPIRED
    if ent.expires_at and ent.expires_at < datetime.now():
        ent.status = STATUS_EXPIRED
        return True
    return False


def _raise_for_status(ent: VadminOrEntitlement) -> None:
    if _touch_expired(ent):
        raise CustomException(ENTITLEMENT_INVALID_MSG, code=ENTITLEMENT_INVALID_CODE)
    if ent.status == STATUS_VOID:
        raise CustomException(ENTITLEMENT_VOID_MSG, code=ENTITLEMENT_VOID_CODE)
    if ent.status == STATUS_USED:
        raise CustomException(ENTITLEMENT_USED_MSG, code=ENTITLEMENT_USED_CODE)
    if ent.status == STATUS_EXPIRED:
        raise CustomException(ENTITLEMENT_INVALID_MSG, code=ENTITLEMENT_INVALID_CODE)
    if ent.status not in (STATUS_UNUSED, STATUS_BOUND):
        raise CustomException(ENTITLEMENT_INVALID_MSG, code=ENTITLEMENT_INVALID_CODE)


async def create_entitlement(
    db: AsyncSession,
    *,
    channel: str = "manual",
    external_order_id: str | None = None,
    service_type: str = SERVICE_TYPE_REQUIREMENT,
    expires_days: int | None = None,
    remark: str | None = None,
) -> VadminOrEntitlement:
    ch = (channel or "manual").strip() or "manual"
    oid = (external_order_id or "").strip() or None
    if oid:
        existing = await db.execute(
            select(VadminOrEntitlement).where(
                VadminOrEntitlement.channel == ch,
                VadminOrEntitlement.external_order_id == oid,
                VadminOrEntitlement.is_delete == false(),
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            await _ensure_paid_order_for_entitlement(db, row, sku_code=None, raw_event=None)
            return row
    token = _new_token()
    # manual 无订单号时用占位，满足唯一约束且互不冲突
    store_oid = oid if oid else f"m-{token}"
    expires_at = None
    if expires_days is not None and int(expires_days) > 0:
        expires_at = datetime.now() + timedelta(days=int(expires_days))
    ent = VadminOrEntitlement(
        token=token,
        status=STATUS_UNUSED,
        service_type=(service_type or SERVICE_TYPE_REQUIREMENT).strip() or SERVICE_TYPE_REQUIREMENT,
        channel=ch,
        external_order_id=store_oid,
        expires_at=expires_at,
        remark=(remark or None),
    )
    db.add(ent)
    await db.flush()
    await _ensure_paid_order_for_entitlement(db, ent, sku_code=None, raw_event=None)
    return ent


async def _ensure_paid_order_for_entitlement(
    db: AsyncSession,
    ent: VadminOrEntitlement,
    *,
    sku_code: str | None,
    raw_event: str | None,
) -> VadminOrChannelOrder:
    ch = ent.channel
    oid = (ent.external_order_id or "").strip()
    q = await db.execute(
        select(VadminOrChannelOrder).where(
            VadminOrChannelOrder.channel == ch,
            VadminOrChannelOrder.external_order_id == oid,
            VadminOrChannelOrder.is_delete == false(),
        )
    )
    order = q.scalar_one_or_none()
    url = short_url_for(ent.token)
    now = datetime.now()
    if order is None:
        order = VadminOrChannelOrder(
            channel=ch,
            external_order_id=oid,
            sku_code=sku_code,
            status=ORDER_PAID,
            entitlement_id=ent.id,
            short_url=url,
            paid_at=now,
            raw_event=raw_event,
        )
        db.add(order)
    else:
        order.entitlement_id = ent.id
        order.short_url = url
        order.sku_code = sku_code or order.sku_code
        if raw_event:
            order.raw_event = raw_event
        if order.status not in (ORDER_REDEEMED, ORDER_REFUNDED):
            order.status = ORDER_PAID
            if not order.paid_at:
                order.paid_at = now
    await db.flush()
    return order


async def fulfill_channel_order(
    db: AsyncSession,
    *,
    channel: str,
    external_order_id: str,
    sku_code: str | None = None,
    raw_event: str | None = None,
    remark: str | None = None,
) -> tuple[VadminOrChannelOrder, VadminOrEntitlement]:
    ch = (channel or "").strip()
    oid = (external_order_id or "").strip()
    if not ch or not oid:
        raise CustomException("订单信息不完整", code=400)
    q = await db.execute(
        select(VadminOrChannelOrder).where(
            VadminOrChannelOrder.channel == ch,
            VadminOrChannelOrder.external_order_id == oid,
            VadminOrChannelOrder.is_delete == false(),
        )
    )
    order = q.scalar_one_or_none()
    if order and order.entitlement_id:
        ent = await db.get(VadminOrEntitlement, order.entitlement_id)
        if ent and not ent.is_delete:
            if raw_event:
                order.raw_event = raw_event
                await db.flush()
            return order, ent
    # create_entitlement 已挂 paid 订单；再对齐 sku/raw
    ent = await create_entitlement(
        db,
        channel=ch,
        external_order_id=oid,
        remark=remark,
    )
    order = await _ensure_paid_order_for_entitlement(
        db, ent, sku_code=sku_code, raw_event=raw_event
    )
    return order, ent


async def mark_order_delivered(
    db: AsyncSession,
    order: VadminOrChannelOrder,
    *,
    deliver_ok: bool,
    payload: str | None = None,
) -> None:
    # 发货回写成功与否不影响业务三态；订单仍为已支付直至核销/退费
    if order.status not in (ORDER_REDEEMED, ORDER_REFUNDED):
        order.status = ORDER_PAID
        if not order.paid_at:
            order.paid_at = datetime.now()
    order.deliver_ok = bool(deliver_ok)
    order.deliver_payload = payload
    await db.flush()


async def void_entitlement(
    db: AsyncSession,
    entitlement_id: int,
    *,
    remark: str | None = None,
    operator: str | None = None,
) -> VadminOrEntitlement:
    """未消费（unused/bound）短链退费作废：权益作废，并同步渠道订单为已退费。"""
    ent = await db.get(VadminOrEntitlement, entitlement_id)
    if not ent or ent.is_delete:
        raise CustomException("权益不存在", code=404)
    if ent.status == STATUS_USED:
        raise CustomException("已核销的权益请走订单退费", code=400)
    if ent.status == STATUS_VOID:
        raise CustomException("短链已作废", code=400)
    now = datetime.now()
    ent.status = STATUS_VOID
    ent.void_at = now
    await db.flush()
    oq = await db.execute(
        select(VadminOrChannelOrder).where(
            VadminOrChannelOrder.entitlement_id == ent.id,
            VadminOrChannelOrder.is_delete == false(),
        )
    )
    order = oq.scalar_one_or_none()
    if order and order.status != ORDER_REFUNDED:
        order.status = ORDER_REFUNDED
        order.refunded_at = now
        order.refund_remark = (remark or "").strip() or "管理端短链退费作废（未消费）"
        order.refund_operator = (operator or "").strip() or None
        await db.flush()
    return ent


async def _void_entitlement_force(db: AsyncSession, ent: VadminOrEntitlement) -> None:
    if ent.status != STATUS_VOID:
        ent.status = STATUS_VOID
        ent.void_at = datetime.now()
        await db.flush()


async def refund_channel_order(
    db: AsyncSession,
    order_id: int,
    *,
    remark: str | None = None,
    operator: str | None = None,
) -> dict:
    order = await db.get(VadminOrChannelOrder, order_id)
    if not order or order.is_delete:
        raise CustomException("订单不存在", code=404)
    if order.status == ORDER_REFUNDED:
        raise CustomException("订单已退费", code=400)
    if order.entitlement_id:
        ent = await db.get(VadminOrEntitlement, order.entitlement_id)
        if ent and not ent.is_delete:
            await _void_entitlement_force(db, ent)
    order.status = ORDER_REFUNDED
    order.refunded_at = datetime.now()
    order.refund_remark = (remark or "").strip() or None
    order.refund_operator = (operator or "").strip() or None
    await db.flush()
    return _order_dict(order, entitlement=None)


async def void_by_channel_order(db: AsyncSession, channel: str, external_order_id: str) -> bool:
    q = await db.execute(
        select(VadminOrChannelOrder).where(
            VadminOrChannelOrder.channel == (channel or "").strip(),
            VadminOrChannelOrder.external_order_id == (external_order_id or "").strip(),
            VadminOrChannelOrder.is_delete == false(),
        )
    )
    order = q.scalar_one_or_none()
    if not order:
        return False
    if order.status == ORDER_REFUNDED:
        return True
    await refund_channel_order(db, order.id, remark="渠道售后回调", operator="xhs_notify")
    return True


async def _session_transcript(db: AsyncSession, session_id: int | None) -> dict:
    """公开只读：按会话 ID 取标题与消息（次卡短链完成后复用同一链接分享）。"""
    if not session_id:
        return {"title": "需求分析", "messages": []}
    from apps.mp_chat import models as chat_models
    from apps.mp_chat.crud import ChatMessageDal
    from apps.mp_chat.schemas import ShareMessageOut

    sess = await db.get(chat_models.VadminChatSession, session_id)
    if not sess or sess.is_delete:
        return {"title": "需求分析", "messages": []}
    dal_m = ChatMessageDal(db)
    rows: list = []
    page = 1
    total = 0
    while len(rows) < 500:
        datas, count = await dal_m.list_for_session(sess.id, page, 200)
        total = count or 0
        if not datas:
            break
        rows.extend(datas)
        if len(rows) >= total:
            break
        page += 1
    messages = []
    for item in rows[:500]:
        if isinstance(item, dict):
            role = item.get("role") or ""
            content = item.get("content") or ""
            created = item.get("create_datetime")
            atts = item.get("attachments")
        else:
            role = item.role
            content = item.content or ""
            created = item.create_datetime
            atts = getattr(item, "attachments", None)
        messages.append(
            ShareMessageOut(
                role=role,
                content=content,
                attachments=atts,
                create_datetime=created,
            ).model_dump()
        )
    title = (sess.title or "").strip() or "需求分析"
    return {"title": title, "messages": messages}


async def preview_entitlement(db: AsyncSession, token: str) -> dict:
    """短链预检：未完成可聊；已核销返回只读正文（任何人打开同一链接可看）。"""
    ent = await _get_by_token(db, token)
    if not ent:
        raise CustomException(ENTITLEMENT_INVALID_MSG, code=ENTITLEMENT_INVALID_CODE)
    _touch_expired(ent)
    await db.flush()
    if ent.status == STATUS_VOID:
        raise CustomException(ENTITLEMENT_VOID_MSG, code=ENTITLEMENT_VOID_CODE)
    if ent.status == STATUS_EXPIRED:
        raise CustomException(ENTITLEMENT_INVALID_MSG, code=ENTITLEMENT_INVALID_CODE)
    base = {
        "status": ent.status,
        "service_type": ent.service_type,
        "expires_at": ent.expires_at.isoformat(sep=" ", timespec="seconds") if ent.expires_at else None,
        "bound_session_id": ent.bound_session_id,
    }
    if ent.status == STATUS_USED:
        transcript = await _session_transcript(db, ent.bound_session_id)
        return {
            **base,
            "mode": "readonly",
            "title": transcript["title"],
            "messages": transcript["messages"],
        }
    if ent.status not in (STATUS_UNUSED, STATUS_BOUND):
        raise CustomException(ENTITLEMENT_INVALID_MSG, code=ENTITLEMENT_INVALID_CODE)
    return {**base, "mode": "chat"}


async def _ensure_entitlement_user(db: AsyncSession, ent: VadminOrEntitlement) -> VadminUser:
    if ent.bound_user_id:
        u = await db.get(VadminUser, ent.bound_user_id)
        if u and not u.is_delete:
            return u
    dal = UserDal(db)
    for _ in range(100):
        telephone = f"198{secrets.randbelow(10**8):08d}"
        clash = await dal.get_data(telephone=telephone, v_return_none=True)
        if clash:
            continue
        pwd_plain = secrets.token_urlsafe(32)
        user = VadminUser(
            telephone=telephone,
            name="次卡用户",
            nickname="次卡用户",
            password=VadminUser.get_password_hash(pwd_plain),
            is_staff=True,
            is_active=True,
            is_system_created=True,
            user_type=USER_TYPE_ENTITLEMENT,
            avatar=settings.DEFAULT_AVATAR,
        )
        await dal.flush(user)
        ent.bound_user_id = user.id
        if ent.status == STATUS_UNUSED:
            ent.status = STATUS_BOUND
        await db.flush()
        return user
    raise CustomException("创建临时用户失败", code=500)


def _token_payload(user: VadminUser) -> dict:
    access_token = LoginManage.create_token(
        {"sub": user.telephone, "is_refresh": False, "password": user.password}
    )
    refresh_token = LoginManage.create_token(
        payload={"sub": user.telephone, "is_refresh": True, "password": user.password},
        expires=Td(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "is_reset_password": user.is_reset_password,
        "must_set_password_without_old": user_must_set_password_without_old(user),
        "is_wx_server_openid": user.is_wx_server_openid,
        "user_type": user.user_type,
        "service_type": SERVICE_TYPE_REQUIREMENT,
    }


async def redeem(db: AsyncSession, token: str) -> dict:
    ent = await _get_by_token(db, token)
    if not ent:
        raise CustomException(ENTITLEMENT_INVALID_MSG, code=ENTITLEMENT_INVALID_CODE)
    _raise_for_status(ent)
    user = await _ensure_entitlement_user(db, ent)
    if getattr(user, "is_blocked", False) or not user.is_active:
        raise CustomException(ENTITLEMENT_INVALID_MSG, code=ENTITLEMENT_INVALID_CODE)
    data = _token_payload(user)
    data["entitlement_status"] = ent.status
    data["bound_session_id"] = ent.bound_session_id
    data["mode"] = "chat"
    return data


async def get_active_for_user(db: AsyncSession, user_id: int) -> VadminOrEntitlement | None:
    q = await db.execute(
        select(VadminOrEntitlement).where(
            VadminOrEntitlement.bound_user_id == user_id,
            VadminOrEntitlement.is_delete == false(),
            VadminOrEntitlement.status.in_((STATUS_UNUSED, STATUS_BOUND)),
        )
    )
    ent = q.scalar_one_or_none()
    if ent and _touch_expired(ent):
        await db.flush()
        return None
    return ent


async def assert_entitlement_may_use_agent(
    db: AsyncSession, user: VadminUser, service_type: str
) -> VadminOrEntitlement:
    if getattr(user, "user_type", "") != USER_TYPE_ENTITLEMENT:
        raise CustomException(ENTITLEMENT_SCENE_DENIED_MSG, code=ENTITLEMENT_SCENE_DENIED_CODE)
    ent = await get_active_for_user(db, user.id)
    if not ent:
        # 可能已 used
        q = await db.execute(
            select(VadminOrEntitlement).where(
                VadminOrEntitlement.bound_user_id == user.id,
                VadminOrEntitlement.is_delete == false(),
            )
        )
        any_ent = q.scalar_one_or_none()
        if any_ent and any_ent.status == STATUS_USED:
            raise CustomException(ENTITLEMENT_USED_MSG, code=ENTITLEMENT_USED_CODE)
        if any_ent and any_ent.status == STATUS_VOID:
            raise CustomException(ENTITLEMENT_VOID_MSG, code=ENTITLEMENT_VOID_CODE)
        raise CustomException(ENTITLEMENT_SCENE_DENIED_MSG, code=ENTITLEMENT_SCENE_DENIED_CODE)
    st = (service_type or "").strip()
    if st != (ent.service_type or "").strip():
        raise CustomException(ENTITLEMENT_SCENE_DENIED_MSG, code=ENTITLEMENT_SCENE_DENIED_CODE)
    return ent


async def bind_session(db: AsyncSession, user_id: int, session_id: int) -> None:
    ent = await get_active_for_user(db, user_id)
    if not ent:
        return
    if ent.bound_session_id and ent.bound_session_id != session_id:
        raise CustomException(ENTITLEMENT_USED_MSG, code=ENTITLEMENT_USED_CODE)
    ent.bound_session_id = session_id
    if ent.status == STATUS_UNUSED:
        ent.status = STATUS_BOUND
    await db.flush()


async def mark_used_on_topic_close(db: AsyncSession, session_id: int, user_id: int) -> None:
    q = await db.execute(
        select(VadminOrEntitlement).where(
            VadminOrEntitlement.bound_user_id == user_id,
            VadminOrEntitlement.is_delete == false(),
            or_(
                VadminOrEntitlement.bound_session_id == session_id,
                VadminOrEntitlement.bound_session_id.is_(None),
            ),
            VadminOrEntitlement.status.in_((STATUS_BOUND, STATUS_UNUSED)),
        )
    )
    ent = q.scalar_one_or_none()
    if not ent:
        return
    now = datetime.now()
    ent.status = STATUS_USED
    ent.used_at = now
    ent.bound_session_id = session_id
    await db.flush()
    oq = await db.execute(
        select(VadminOrChannelOrder).where(
            VadminOrChannelOrder.entitlement_id == ent.id,
            VadminOrChannelOrder.is_delete == false(),
        )
    )
    order = oq.scalar_one_or_none()
    if order and order.status != ORDER_REFUNDED:
        order.status = ORDER_REDEEMED
        order.redeemed_at = now
        await db.flush()


def _fmt_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.isoformat(sep=" ", timespec="seconds")


def _order_dict(order: VadminOrChannelOrder, entitlement: VadminOrEntitlement | None = None) -> dict:
    ent = entitlement
    url = short_url_for(ent.token) if ent and ent.token else order.short_url
    return {
        "id": order.id,
        "channel": order.channel,
        "channel_label": channel_label(order.channel),
        "external_order_id": order.external_order_id,
        "sku_code": order.sku_code,
        "status": order.status,
        "status_label": ORDER_STATUS_LABEL.get(order.status, order.status),
        "entitlement_id": order.entitlement_id,
        "short_url": url,
        "token": ent.token if ent else None,
        "entitlement_status": ent.status if ent else None,
        "paid_at": _fmt_dt(order.paid_at),
        "redeemed_at": _fmt_dt(order.redeemed_at),
        "refunded_at": _fmt_dt(order.refunded_at),
        "refund_remark": order.refund_remark,
        "refund_operator": order.refund_operator,
        "deliver_ok": bool(order.deliver_ok),
        "create_datetime": _fmt_dt(order.create_datetime),
    }


async def create_offline_order(
    db: AsyncSession,
    *,
    remark: str | None = None,
    expires_days: int | None = 30,
    external_order_id: str | None = None,
) -> dict:
    """线下收款后由管理员出链：1 次需求分析，订单 channel=offline、已支付。"""
    oid = (external_order_id or "").strip() or None
    if not oid:
        oid = f"offline-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}"
    note = (remark or "").strip() or "线下出链"
    ent = await create_entitlement(
        db,
        channel="offline",
        external_order_id=oid,
        expires_days=expires_days,
        remark=note,
    )
    oq = await db.execute(
        select(VadminOrChannelOrder).where(
            VadminOrChannelOrder.entitlement_id == ent.id,
            VadminOrChannelOrder.is_delete == false(),
        )
    )
    order = oq.scalar_one_or_none()
    if not order:
        order = await _ensure_paid_order_for_entitlement(db, ent, sku_code=None, raw_event=None)
    return _order_dict(order, ent)


async def list_channel_orders(
    db: AsyncSession,
    *,
    q: str = "",
    status: str = "",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict], int]:
    from sqlalchemy import func

    stmt = select(VadminOrChannelOrder).where(VadminOrChannelOrder.is_delete == false())
    st = (status or "").strip()
    if st in (ORDER_PAID, ORDER_REDEEMED, ORDER_REFUNDED):
        stmt = stmt.where(VadminOrChannelOrder.status == st)
    kw = (q or "").strip()
    if kw:
        like = f"%{kw}%"
        stmt = stmt.where(
            or_(
                VadminOrChannelOrder.external_order_id.like(like),
                VadminOrChannelOrder.channel.like(like),
                VadminOrChannelOrder.short_url.like(like),
                VadminOrChannelOrder.sku_code.like(like),
            )
        )
    count_q = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = int(count_q.scalar_one() or 0)
    rows = (
        await db.execute(
            stmt.order_by(VadminOrChannelOrder.id.desc()).offset((page - 1) * limit).limit(limit)
        )
    ).scalars().all()
    ent_ids = [r.entitlement_id for r in rows if r.entitlement_id]
    ent_map: dict[int, VadminOrEntitlement] = {}
    if ent_ids:
        er = await db.execute(
            select(VadminOrEntitlement).where(VadminOrEntitlement.id.in_(ent_ids))
        )
        for e in er.scalars().all():
            ent_map[e.id] = e
    items = [_order_dict(r, ent_map.get(r.entitlement_id) if r.entitlement_id else None) for r in rows]
    return items, total


async def list_entitlements(
    db: AsyncSession,
    *,
    q: str = "",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict], int]:
    from sqlalchemy import func

    stmt = select(VadminOrEntitlement).where(VadminOrEntitlement.is_delete == false())
    kw = (q or "").strip()
    if kw:
        like = f"%{kw}%"
        stmt = stmt.where(
            or_(
                VadminOrEntitlement.token.like(like),
                VadminOrEntitlement.external_order_id.like(like),
                VadminOrEntitlement.channel.like(like),
                VadminOrEntitlement.remark.like(like),
            )
        )
    count_q = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = int(count_q.scalar_one() or 0)
    rows = (
        await db.execute(
            stmt.order_by(VadminOrEntitlement.id.desc()).offset((page - 1) * limit).limit(limit)
        )
    ).scalars().all()
    items = []
    for ent in rows:
        items.append(
            {
                "id": ent.id,
                "token": ent.token,
                "short_url": short_url_for(ent.token),
                "status": ent.status,
                "status_label": entitlement_status_label(ent.status),
                "service_type": ent.service_type,
                "channel": ent.channel,
                "channel_label": channel_label(ent.channel),
                "external_order_id": ent.external_order_id,
                "bound_user_id": ent.bound_user_id,
                "bound_session_id": ent.bound_session_id,
                "expires_at": ent.expires_at.isoformat(sep=" ", timespec="seconds")
                if ent.expires_at
                else None,
                "used_at": ent.used_at.isoformat(sep=" ", timespec="seconds") if ent.used_at else None,
                "void_at": ent.void_at.isoformat(sep=" ", timespec="seconds") if ent.void_at else None,
                "remark": ent.remark,
                "create_datetime": ent.create_datetime.isoformat(sep=" ", timespec="seconds")
                if ent.create_datetime
                else None,
            }
        )
    return items, total


def dump_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)[:8000]
    except Exception:
        return str(obj)[:8000]
