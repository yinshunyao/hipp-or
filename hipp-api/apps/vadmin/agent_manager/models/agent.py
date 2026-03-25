#!/usr/bin/python
# -*- coding: utf-8 -*-
# @desc           : 智能客服数据模型

from sqlalchemy.orm import relationship, Mapped, mapped_column
from apps.vadmin.auth.models import VadminUser
from db.db_base import BaseModel
from sqlalchemy import String, Boolean, Integer, ForeignKey, Text


class VadminAgent(BaseModel):
    __tablename__ = "vadmin_agent"
    __table_args__ = ({'comment': '智能客服表'})

    api_server: Mapped[str] = mapped_column(String(500), nullable=False, comment="Dify API 服务器地址")
    app_key: Mapped[str] = mapped_column(String(500), nullable=False, comment="Dify APP_KEY")
    service_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True, comment="智能客服类型（如需求分析、商业评估）"
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")

    name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, comment="智能体名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="智能体描述")
    tags: Mapped[str | None] = mapped_column(Text, nullable=True, comment="标签 JSON 数组")
    mode: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="应用模式")

    icon_type: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="图标类型")
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="图标内容")
    icon_background: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="图标背景色")
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="图标图片URL")
    webapp_config: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Dify WebApp配置JSON")

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", comment="上架状态: draft/published")
    is_tested: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否通过连通性测试")

    create_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vadmin_auth_user.id", ondelete='RESTRICT'),
        comment="创建人"
    )
    create_user: Mapped[VadminUser] = relationship(foreign_keys=create_user_id)
