#!/usr/bin/python
# -*- coding: utf-8 -*-
# @desc           : 智能客服序列化模型

from pydantic import BaseModel, ConfigDict
from core.data_types import DatetimeStr
from apps.vadmin.auth.schemas import UserSimpleOut


class Agent(BaseModel):
    api_server: str | None = None
    app_key: str | None = None
    remark: str | None = None
    name: str | None = None
    description: str | None = None
    tags: str | None = None
    mode: str | None = None
    icon_type: str | None = None
    icon: str | None = None
    icon_background: str | None = None
    icon_url: str | None = None
    webapp_config: str | None = None
    status: str | None = None
    is_tested: bool | None = None
    create_user_id: int | None = None


class AgentSimpleOut(Agent):
    model_config = ConfigDict(from_attributes=True)

    id: int
    update_datetime: DatetimeStr
    create_datetime: DatetimeStr


class AgentListOut(AgentSimpleOut):
    model_config = ConfigDict(from_attributes=True)

    create_user: UserSimpleOut


class AgentTestIn(BaseModel):
    """连通性测试：须携带当前表单中的 api_server、app_key、remark；id 为空表示尚未落库"""

    api_server: str
    app_key: str
    remark: str | None = None
    id: int | None = None
