# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.db_base import BaseModel

SESSION_FEE_KEY = "session_fee"
DEFAULT_SESSION_FEE = Decimal("0.10")


class VadminOrBillingSetting(BaseModel):
    __tablename__ = "vadmin_or_billing_setting"
    __table_args__ = ({"comment": "or 计费全局配置"},)

    config_key: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True, comment="配置键"
    )
    config_value: Mapped[str] = mapped_column(String(64), nullable=False, comment="配置值")


class VadminOrUserSessionFee(BaseModel):
    __tablename__ = "vadmin_or_user_session_fee"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_or_user_session_fee_user"),
        {"comment": "or 用户会话费用专属"},
    )

    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="用户ID")
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="每次会话费用（元）"
    )
