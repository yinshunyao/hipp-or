# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class SessionFeeAmountIn(BaseModel):
    amount: Decimal = Field(..., description="每次会话费用（元）")
