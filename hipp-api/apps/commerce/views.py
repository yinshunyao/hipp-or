# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.commerce import service as commerce
from apps.commerce.channels import xhs as xhs_channel
from apps.commerce.schemas import EntitlementCreateIn, OfflineOrderIn, OrderRefundIn
from apps.vadmin.auth.utils.current import FullAdminAuth
from apps.vadmin.auth.utils.validation.auth import Auth
from core.database import db_getter
from utils.response import ErrorResponse, SuccessResponse

app = APIRouter()
admin_app = APIRouter()


@app.get("/access/{token}", summary="短链预检：未完成可聊；已核销返回只读正文")
async def access_preview(token: str, db: AsyncSession = Depends(db_getter)):
    return SuccessResponse(await commerce.preview_entitlement(db, token))


@app.post("/access/{token}/redeem", summary="打开短链并签发临时登录（进行中；非订单核销）")
async def access_redeem(token: str, db: AsyncSession = Depends(db_getter)):
    return SuccessResponse(await commerce.redeem(db, token))


@app.post("/channels/xhs/notify", summary="小红书订单消息回调")
async def xhs_notify(request: Request, db: AsyncSession = Depends(db_getter)):
    raw = await request.body()
    sig = (
        request.headers.get("x-xhs-signature")
        or request.headers.get("X-Xhs-Signature")
        or request.headers.get("signature")
        or ""
    )
    if not xhs_channel.verify_sign(raw, sig):
        return ErrorResponse(msg="签名校验失败", code=401)
    try:
        payload = await request.json()
    except Exception:
        payload = None
    data = await xhs_channel.handle_notify(db, payload)
    return SuccessResponse(data)


@admin_app.get("/orders", summary="电商渠道订单流水")
async def admin_orders(
    q: str = Query(""),
    status: str = Query("", description="paid/redeemed/refunded"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    auth: Auth = Depends(FullAdminAuth()),
):
    items, count = await commerce.list_channel_orders(
        auth.db, q=q, status=status, page=page, limit=limit
    )
    return SuccessResponse(items, count=count)


@admin_app.post("/orders/offline", summary="线下出链：生成一次需求分析短链")
async def admin_offline_order(body: OfflineOrderIn, auth: Auth = Depends(FullAdminAuth())):
    data = await commerce.create_offline_order(
        auth.db,
        remark=body.remark,
        expires_days=body.expires_days,
        external_order_id=body.external_order_id,
    )
    return SuccessResponse(data)


@admin_app.post("/orders/{order_id}/refund", summary="订单退费（作废短链；资金在渠道侧处理）")
async def admin_order_refund(
    order_id: int,
    body: OrderRefundIn,
    auth: Auth = Depends(FullAdminAuth()),
):
    op = getattr(auth.user, "name", None) or getattr(auth.user, "telephone", None) or str(auth.user.id)
    data = await commerce.refund_channel_order(
        auth.db,
        order_id,
        remark=body.remark,
        operator=str(op),
    )
    data["notice"] = "短链已失效。请在小红书千帆等渠道完成后台真实退款，本系统不记账本资金。"
    return SuccessResponse(data)


@admin_app.get("/entitlements", summary="次卡权益列表")
async def admin_list(
    q: str = Query(""),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    auth: Auth = Depends(FullAdminAuth()),
):
    items, count = await commerce.list_entitlements(auth.db, q=q, page=page, limit=limit)
    return SuccessResponse(items, count=count)


@admin_app.post("/entitlements", summary="创建次卡短链（可批量，同步生成已支付订单）")
async def admin_create(body: EntitlementCreateIn, auth: Auth = Depends(FullAdminAuth())):
    items = []
    n = int(body.count or 1)
    for i in range(n):
        oid = body.external_order_id
        if n > 1 and oid:
            oid = f"{oid}-{i + 1}"
        ent = await commerce.create_entitlement(
            auth.db,
            channel=body.channel or "manual",
            external_order_id=oid,
            expires_days=body.expires_days,
            remark=body.remark,
        )
        items.append(
            {
                "id": ent.id,
                "token": ent.token,
                "short_url": commerce.short_url_for(ent.token),
                "status": ent.status,
                "channel": ent.channel,
                "external_order_id": ent.external_order_id,
                "expires_at": ent.expires_at.isoformat(sep=" ", timespec="seconds")
                if ent.expires_at
                else None,
            }
        )
    return SuccessResponse({"items": items})


@admin_app.post("/entitlements/{entitlement_id}/void", summary="退费作废未消费短链（同步订单已退费）")
async def admin_void(entitlement_id: int, auth: Auth = Depends(FullAdminAuth())):
    op = getattr(auth.user, "name", None) or getattr(auth.user, "telephone", None) or "admin"
    ent = await commerce.void_entitlement(
        auth.db,
        entitlement_id,
        remark="管理端短链退费作废（未消费）",
        operator=str(op),
    )
    return SuccessResponse(
        {
            "id": ent.id,
            "status": ent.status,
            "status_label": commerce.entitlement_status_label(ent.status),
        }
    )
