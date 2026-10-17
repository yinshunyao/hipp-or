# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class AgentSnippetOut(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    service_type: Optional[str] = None
    icon_type: Optional[str] = None
    icon: Optional[str] = None
    icon_background: Optional[str] = None
    icon_url: Optional[str] = None

    model_config = {"from_attributes": True}


class SessionListOut(BaseModel):
    id: int
    agent_id: Optional[int] = None
    session_kind: Literal["dify", "human_support"] = "dify"
    title: str
    # 列表/导航展示用：用户改过标题（与 agent_name_snapshot 不一致）时用库内 title；
    # 否则用实时智能体名称（若仍存在），避免后台改智能体名称后小程序仍显示旧 title
    display_title: Optional[str] = None
    agent_name_snapshot: Optional[str] = None
    agent_avatar_snapshot: Optional[str] = None
    agent_status: Optional[Literal["active", "offline", "deleted"]] = None
    last_message_preview: Optional[str] = None
    is_pinned: bool = False
    is_topic_closed: bool = False
    is_archived: bool = False
    is_shared: bool = False
    share_token: Optional[str] = Field(default=None, exclude=True)
    token_usage: int = 0
    update_datetime: Optional[datetime] = None
    assigned_human_user_id: Optional[int] = None
    assigned_human_name: Optional[str] = None
    source_archive_session_id: Optional[int] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def mark_shared(self):
        if self.share_token:
            self.is_shared = True
        return self


class SessionDetailOut(SessionListOut):
    dify_conversation_id: Optional[str] = None
    agent: Optional[AgentSnippetOut] = None
    viewer_context: Optional[Literal["owner", "assigned_staff"]] = None
    end_user_display_name: Optional[str] = None


class InboxItem(BaseModel):
    kind: Literal["session", "agent"]
    session: Optional[SessionListOut] = None
    agent: AgentSnippetOut


class InboxOut(BaseModel):
    items: list[InboxItem]


class CreateSessionIn(BaseModel):
    agent_id: int = Field(..., ge=1)


class CreateHumanSupportSessionIn(BaseModel):
    source_session_id: int = Field(..., ge=1, description="已归档的智能体会话 id")


class PatchSessionIn(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None
    resume_topic: Optional[bool] = None


class ChatAttachmentIn(BaseModel):
    type: Literal["image", "document"]
    url: str = Field(..., min_length=8, max_length=2000)
    name: str = Field(..., min_length=1, max_length=255)
    size: int = Field(..., ge=1)
    mime: str = Field("", max_length=128)


class ChatAttachmentOut(BaseModel):
    type: str
    url: str
    name: str
    size: int = 0
    mime: str = ""


class SendMessageIn(BaseModel):
    query: str = Field("", max_length=8000)
    files: Optional[list[ChatAttachmentIn]] = None

    @model_validator(mode="after")
    def require_query_or_files(self):
        text = (self.query or "").strip()
        if not text and not self.files:
            raise ValueError("请输入内容或添加附件")
        return self


class DeleteChatUploadIn(BaseModel):
    url: str = Field(..., min_length=8, max_length=2000)


class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    attachments: Optional[list[ChatAttachmentOut]] = None
    create_datetime: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_validator("attachments", mode="before")
    @classmethod
    def coerce_attachments(cls, value: Any):
        if value is None or value == "":
            return None
        if isinstance(value, list):
            return value or None
        if isinstance(value, str):
            import json

            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                return None
            return data if isinstance(data, list) and data else None
        return None


class ShareMessageOut(BaseModel):
    role: str
    content: str
    attachments: Optional[list[ChatAttachmentOut]] = None
    create_datetime: Optional[datetime] = None

    @field_validator("attachments", mode="before")
    @classmethod
    def coerce_share_attachments(cls, value: Any):
        return ChatMessageOut.coerce_attachments(value)


class ShareOut(BaseModel):
    title: str
    messages: list[ShareMessageOut]


class ArchivedTopicItemOut(BaseModel):
    """场景页时间线：归档话题条目（用于分页与向上翻阅更早记录）。"""

    session_id: int
    display_title: str
    update_ts: float = Field(..., description="会话 update_datetime 的 Unix 时间戳（秒，浮点），作分页游标")


class ArchivedTopicsPageOut(BaseModel):
    items: list[ArchivedTopicItemOut]
    has_more: bool


class SceneAgentOut(BaseModel):
    """
    场景页入口解析后的智能体（按 service_type 过滤；同类型多候选时随机 1 个）。
    guest_*：仅 mp_guest；归档次数按当前场景的 service_type（需求分析 / 商业评估）分别统计，非两场景合计。
    """

    service_type: str
    agent: AgentSnippetOut
    session: SessionListOut | None = None
    guest_scene_archived_count: int = 0
    guest_scene_trial_limit: int = 2
    guest_need_login: bool = False
