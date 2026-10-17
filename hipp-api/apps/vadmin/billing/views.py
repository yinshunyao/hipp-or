# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from apps.vadmin.auth.utils.current import FullAdminAuth
from apps.vadmin.auth.utils.validation.auth import Auth
from apps.vadmin.billing import service
from apps.vadmin.billing.schemas import SessionFeeAmountIn
from utils.response import ErrorResponse, SuccessResponse

app = APIRouter()


@app.get("/session-fee/global", summary="全局会话费用")
async def get_global_fee(auth: Auth = Depends(FullAdminAuth())):
    amount = await service.get_global_session_fee(auth.db)
    return SuccessResponse({"amount": float(amount)})


@app.put("/session-fee/global", summary="更新全局会话费用")
async def put_global_fee(body: SessionFeeAmountIn, auth: Auth = Depends(FullAdminAuth())):
    try:
        amount = await service.set_global_session_fee(auth.db, body.amount)
    except ValueError as e:
        return ErrorResponse(msg=str(e))
    return SuccessResponse({"amount": float(amount)})


@app.get("/session-fee/users", summary="搜索用户会话费用")
async def list_user_fees(
    q: str = Query("", description="手机号/姓名/昵称"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    auth: Auth = Depends(FullAdminAuth()),
):
    items, count = await service.search_users_with_fee(
        auth.db, q=q, page=page, limit=limit
    )
    return SuccessResponse(items, count=count)


@app.put("/session-fee/users/{user_id}", summary="设定用户专属会话费用")
async def put_user_fee(
    user_id: int,
    body: SessionFeeAmountIn,
    auth: Auth = Depends(FullAdminAuth()),
):
    row = (
        await auth.db.execute(
            text(
                "SELECT id FROM vadmin_auth_user "
                "WHERE id = :id AND is_delete = 0 LIMIT 1"
            ),
            {"id": user_id},
        )
    ).first()
    if not row:
        return ErrorResponse(msg="用户不存在")
    try:
        amount = await service.set_user_session_fee(auth.db, user_id, body.amount)
    except ValueError as e:
        return ErrorResponse(msg=str(e))
    return SuccessResponse({"user_id": user_id, "amount": float(amount)})


@app.delete("/session-fee/users/{user_id}", summary="清除用户专属会话费用")
async def delete_user_fee(user_id: int, auth: Auth = Depends(FullAdminAuth())):
    await service.clear_user_session_fee(auth.db, user_id)
    return SuccessResponse({"user_id": user_id})
