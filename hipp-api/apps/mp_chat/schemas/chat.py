# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AgentSnippetOut(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    icon_type: Optional[str] = None
    icon: Optional[str] = None
    icon_background: Optional[str] = None
    icon_url: Optional[str] = None

    model_config = {"from_attributes": True}


class SessionListOut(BaseModel):
    id: int
    agent_id: int
    title: str
    agent_name_snapshot: Optional[str] = None
    agent_avatar_snapshot: Optional[str] = None
    agent_status: Optional[Literal["active", "offline", "deleted"]] = None
    last_message_preview: Optional[str] = None
    is_pinned: bool = False
    update_datetime: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SessionDetailOut(SessionListOut):
    dify_conversation_id: Optional[str] = None
    agent: Optional[AgentSnippetOut] = None


class InboxItem(BaseModel):
    kind: Literal["session", "agent"]
    session: Optional[SessionListOut] = None
    agent: AgentSnippetOut


class InboxOut(BaseModel):
    items: list[InboxItem]


class CreateSessionIn(BaseModel):
    agent_id: int = Field(..., ge=1)


class PatchSessionIn(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    is_pinned: Optional[bool] = None


class SendMessageIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)


class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    create_datetime: Optional[datetime] = None

    model_config = {"from_attributes": True}
