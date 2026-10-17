# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.db_base import BaseModel


class VadminOrEntitlement(BaseModel):
    __tablename__ = "vadmin_or_entitlement"
    __table_args__ = (
        UniqueConstraint("channel", "external_order_id", name="uq_or_entitlement_channel_order"),
        {"comment": "电商/手工短链次卡权益"},
    )

    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True, comment="短链令牌")
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="unused",
        index=True,
        comment="unused/bound/used/void/expired",
    )
    service_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="需求分析", comment="可用智能体 service_type"
    )
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="manual", index=True)
    external_order_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True, comment="渠道订单号；manual 可空但唯一约束用占位"
    )
    bound_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    bound_session_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    void_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)


class VadminOrChannelOrder(BaseModel):
    __tablename__ = "vadmin_or_channel_order"
    __table_args__ = (
        UniqueConstraint("channel", "external_order_id", name="uq_or_channel_order"),
        {"comment": "渠道履约订单"},
    )

    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    external_order_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sku_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="paid",
        index=True,
        comment="paid已支付/redeemed已核销/refunded已退费",
    )
    entitlement_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    short_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="已支付时间")
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="已核销时间")
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="已退费时间")
    refund_remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    refund_operator: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="退费操作人")
    deliver_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    deliver_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_event: Mapped[str | None] = mapped_column(Text, nullable=True)
