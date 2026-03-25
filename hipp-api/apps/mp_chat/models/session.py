#!/usr/bin/python
# -*- coding: utf-8 -*-
# @desc           : 小程序会话与消息（表级不设外键，ID 为逻辑引用；查询用 join/relationship primaryjoin）

from sqlalchemy import String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.vadmin.agent_manager.models import VadminAgent
from db.db_base import BaseModel


class VadminChatSession(BaseModel):
    __tablename__ = "vadmin_chat_session"
    __table_args__ = ({'comment': '小程序用户与智能体会话'})

    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="用户 vadmin_auth_user.id")
    # human_support 会话无智能体，可为空
    agent_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True, comment="智能体 vadmin_agent.id")
    session_kind: Mapped[str] = mapped_column(
        String(32),
        default="dify",
        index=True,
        comment="dify=智能体对话 human_support=人工客服",
    )
    assigned_human_user_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True, comment="分配的人工客服 vadmin_auth_user.id"
    )
    source_archive_session_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="触发人工会话的归档会话 id"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="展示标题")
    agent_name_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="智能体名称快照")
    agent_avatar_snapshot: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="智能体头像快照")
    last_message_preview: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="最近消息摘要")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否置顶")
    dify_conversation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Dify conversation_id")
    is_topic_closed: Mapped[bool] = mapped_column(Boolean, default=False, comment="话题是否已结束（归档）")

    # 无 DB 外键：ORM 用 foreign() 标注逻辑引用，便于 joinedload
    agent: Mapped[VadminAgent] = relationship(
        primaryjoin="foreign(VadminChatSession.agent_id) == VadminAgent.id",
        viewonly=True,
    )


class VadminChatMessage(BaseModel):
    __tablename__ = "vadmin_chat_message"
    __table_args__ = ({'comment': '小程序会话消息'})

    session_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="会话 vadmin_chat_session.id")
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="user / assistant / system")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")

    session: Mapped["VadminChatSession"] = relationship(
        primaryjoin="foreign(VadminChatMessage.session_id) == VadminChatSession.id",
        viewonly=True,
    )
