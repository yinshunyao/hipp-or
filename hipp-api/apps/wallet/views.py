# -*- coding: utf-8 -*-
"""个人资金账户：透传 hipp-manager 钱包 API。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from apps.vadmin.auth.utils.current import AllUserAuth
from apps.vadmin.auth.utils.validation.auth import Auth
from core.database import redis_getter
from utils import hipp_manager
from utils.manager_session import get_manager_token
from utils.response import ErrorResponse, SuccessResponse

app = APIRouter()


class RechargeBody(BaseModel):
    amount: float = Field(..., gt=0)
    channel: str = ""


async def _manager_bearer(request: Request, auth: Auth) -> str | ErrorResponse:
    if not hipp_manager.enabled():
        return ErrorResponse(msg="未配置用户资金系统", code=503)
    ut = str(getattr(auth.user, "user_type", None) or "").strip()
    if ut in ("mp_guest", "entitlement"):
        return ErrorResponse(msg="请先登录正式账号", code=403)
    try:
        rd: Redis = redis_getter(request)
    except Exception:
        return ErrorResponse(msg="请重新登录以同步账户", code=401)
    tok = await get_manager_token(rd, auth.user.id)
    if not tok:
        return ErrorResponse(msg="请重新登录以同步账户", code=401)
    return tok


def _mgr_error(exc: hipp_manager.ManagerError):
    code = int(exc.status or 400)
    if code < 400:
        code = 400
    return ErrorResponse(msg=str(exc) or "资金服务失败", code=code)


@app.get("/session-fee", summary="当前用户每次会话费用")
async def session_fee(auth: Auth = Depends(AllUserAuth())):
    from apps.vadmin.billing import service as billing_service

    amount, is_override = await billing_service.resolve_session_fee(auth.db, auth.user.id)
    return SuccessResponse({"amount": float(amount), "is_override": is_override})


@app.get("/balance", summary="余额（manager）")
async def balance(request: Request, auth: Auth = Depends(AllUserAuth())):
    tok = await _manager_bearer(request, auth)
    if isinstance(tok, ErrorResponse):
        return tok
    try:
        return SuccessResponse(hipp_manager.wallet_balance(tok))
    except hipp_manager.ManagerError as e:
        return _mgr_error(e)


@app.get("/presets", summary="充值面额（manager）")
async def presets(request: Request, auth: Auth = Depends(AllUserAuth())):
    tok = await _manager_bearer(request, auth)
    if isinstance(tok, ErrorResponse):
        return tok
    try:
        return SuccessResponse(hipp_manager.wallet_presets(tok))
    except hipp_manager.ManagerError as e:
        return _mgr_error(e)


@app.get("/pay-channels", summary="支付渠道（manager）")
async def pay_channels(request: Request, auth: Auth = Depends(AllUserAuth())):
    tok = await _manager_bearer(request, auth)
    if isinstance(tok, ErrorResponse):
        return tok
    try:
        return SuccessResponse(hipp_manager.wallet_pay_channels(tok))
    except hipp_manager.ManagerError as e:
        return _mgr_error(e)


@app.post("/recharge", summary="充值下单（manager）")
async def recharge(
    body: RechargeBody,
    request: Request,
    auth: Auth = Depends(AllUserAuth()),
):
    tok = await _manager_bearer(request, auth)
    if isinstance(tok, ErrorResponse):
        return tok
    try:
        data = hipp_manager.wallet_recharge(
            tok, body.amount, channel=(body.channel or "").strip()
        )
        return SuccessResponse(data)
    except hipp_manager.ManagerError as e:
        return _mgr_error(e)


@app.get("/recharge/orders", summary="充值订单列表（manager）")
async def recharge_orders(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(""),
    product: str = Query(""),
    auth: Auth = Depends(AllUserAuth()),
):
    tok = await _manager_bearer(request, auth)
    if isinstance(tok, ErrorResponse):
        return tok
    prod = (product or "").strip() or "or"
    try:
        return SuccessResponse(
            hipp_manager.wallet_recharge_orders(
                tok, page=page, page_size=page_size, status=status, product=prod
            )
        )
    except hipp_manager.ManagerError as e:
        return _mgr_error(e)


@app.get("/recharge/{order_id}", summary="充值订单详情（manager）")
async def recharge_detail(
    order_id: str,
    request: Request,
    auth: Auth = Depends(AllUserAuth()),
):
    tok = await _manager_bearer(request, auth)
    if isinstance(tok, ErrorResponse):
        return tok
    try:
        return SuccessResponse(hipp_manager.wallet_recharge_detail(tok, order_id))
    except hipp_manager.ManagerError as e:
        return _mgr_error(e)


@app.post("/recharge/{order_id}/dev-pay", summary="开发入账（manager）")
async def recharge_dev_pay(
    order_id: str,
    request: Request,
    auth: Auth = Depends(AllUserAuth()),
):
    tok = await _manager_bearer(request, auth)
    if isinstance(tok, ErrorResponse):
        return tok
    try:
        return SuccessResponse(hipp_manager.wallet_dev_pay(tok, order_id))
    except hipp_manager.ManagerError as e:
        return _mgr_error(e)


def _tx_title_fallback(item: dict) -> str:
    t = str(item.get("type") or "").strip()
    if t == "recharge":
        return "充值"
    if t == "refund":
        remark = str(item.get("remark") or "").strip()
        return (remark[:40] if remark else "退费")
    remark = str(item.get("remark") or "").strip()
    return (remark[:40] if remark else "—")


async def _enrich_tx_titles(db, user_id: int, payload: dict) -> dict:
    """为 or 流水补 title（会话名）；不改 manager 真源。"""
    import re

    from sqlalchemy import select

    from apps.mp_chat import models as chat_models

    items = list(payload.get("items") or [])
    if not items:
        return payload
    session_ids: set[int] = set()
    pattern = re.compile(r"^or_session_(\d+)$")
    for item in items:
        m = pattern.match(str(item.get("ref_id") or "").strip())
        if m:
            session_ids.add(int(m.group(1)))
    titles: dict[int, str] = {}
    if session_ids:
        result = await db.execute(
            select(chat_models.VadminChatSession.id, chat_models.VadminChatSession.title)
            .where(
                chat_models.VadminChatSession.id.in_(session_ids),
                chat_models.VadminChatSession.user_id == user_id,
            )
        )
        for sid, title in result.all():
            titles[int(sid)] = str(title or "").strip()
    out_items = []
    for item in items:
        row = dict(item) if isinstance(item, dict) else {}
        m = pattern.match(str(row.get("ref_id") or "").strip())
        if m:
            sid = int(m.group(1))
            name = titles.get(sid) or ""
            row["title"] = name or f"会话 #{sid}"
        else:
            row["title"] = _tx_title_fallback(row)
        out_items.append(row)
    enriched = dict(payload)
    enriched["items"] = out_items
    return enriched


@app.get("/transactions", summary="交易流水（manager）")
async def transactions(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product: str = Query(""),
    auth: Auth = Depends(AllUserAuth()),
):
    tok = await _manager_bearer(request, auth)
    if isinstance(tok, ErrorResponse):
        return tok
    prod = (product or "").strip() or "or"
    try:
        data = hipp_manager.wallet_transactions(
            tok, page=page, page_size=page_size, product=prod
        )
        data = await _enrich_tx_titles(auth.db, auth.user.id, data)
        return SuccessResponse(data)
    except hipp_manager.ManagerError as e:
        return _mgr_error(e)


@app.get("/bills", summary="月账单（manager）")
async def bills(request: Request, auth: Auth = Depends(AllUserAuth())):
    tok = await _manager_bearer(request, auth)
    if isinstance(tok, ErrorResponse):
        return tok
    try:
        return SuccessResponse(hipp_manager.wallet_bills(tok))
    except hipp_manager.ManagerError as e:
        return _mgr_error(e)
