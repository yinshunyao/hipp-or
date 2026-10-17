# -*- coding: utf-8 -*-
"""电商短链次卡业务错误码（与前端/设计码表同步）。"""

from __future__ import annotations

ENTITLEMENT_INVALID_CODE = 46010
ENTITLEMENT_INVALID_MSG = "分析链接无效或已过期"

ENTITLEMENT_USED_CODE = 46011
ENTITLEMENT_USED_MSG = "本次分析次数已用完"

ENTITLEMENT_VOID_CODE = 46012
ENTITLEMENT_VOID_MSG = "分析链接已作废"

ENTITLEMENT_SCENE_DENIED_CODE = 46013
ENTITLEMENT_SCENE_DENIED_MSG = "当前链接仅可用于需求分析，或次数已用尽"
