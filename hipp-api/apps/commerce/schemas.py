# -*- coding: utf-8 -*-
from __future__ import annotations

from pydantic import BaseModel, Field


class EntitlementCreateIn(BaseModel):
    channel: str = "manual"
    external_order_id: str | None = None
    expires_days: int | None = Field(default=30, ge=0, le=3650)
    remark: str | None = None
    count: int = Field(default=1, ge=1, le=100)


class EntitlementBatchOut(BaseModel):
    items: list[dict]


class OrderRefundIn(BaseModel):
    remark: str | None = Field(default=None, max_length=255)


class OfflineOrderIn(BaseModel):
    """线下贩卖：生成一次需求分析短链。"""
    remark: str | None = Field(default=None, max_length=255)
    expires_days: int | None = Field(default=30, ge=0, le=3650)
    external_order_id: str | None = Field(
        default=None,
        max_length=128,
        description="可选线下单号；不填则系统自动生成",
    )
