"""mp_chat human support session

Revision ID: c8d9e0f1a2b4
Revises: 1bcda5d88bf6
Create Date: 2026-03-25

"""
from alembic import op
import sqlalchemy as sa

revision = "c8d9e0f1a2b4"
down_revision = "1bcda5d88bf6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_chat_session",
        sa.Column(
            "session_kind",
            sa.String(length=32),
            nullable=False,
            server_default="dify",
            comment="dify=智能体对话 human_support=人工客服",
        ),
    )
    op.add_column(
        "vadmin_chat_session",
        sa.Column(
            "assigned_human_user_id",
            sa.Integer(),
            nullable=True,
            comment="分配的人工客服 vadmin_auth_user.id",
        ),
    )
    op.add_column(
        "vadmin_chat_session",
        sa.Column(
            "source_archive_session_id",
            sa.Integer(),
            nullable=True,
            comment="触发人工会话的归档会话 id",
        ),
    )
    op.create_index(
        op.f("ix_vadmin_chat_session_session_kind"),
        "vadmin_chat_session",
        ["session_kind"],
        unique=False,
    )
    op.create_index(
        op.f("ix_vadmin_chat_session_assigned_human_user_id"),
        "vadmin_chat_session",
        ["assigned_human_user_id"],
        unique=False,
    )
    op.alter_column(
        "vadmin_chat_session",
        "agent_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "vadmin_chat_session",
        "agent_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.drop_index(
        op.f("ix_vadmin_chat_session_assigned_human_user_id"),
        table_name="vadmin_chat_session",
    )
    op.drop_index(
        op.f("ix_vadmin_chat_session_session_kind"),
        table_name="vadmin_chat_session",
    )
    op.drop_column("vadmin_chat_session", "source_archive_session_id")
    op.drop_column("vadmin_chat_session", "assigned_human_user_id")
    op.drop_column("vadmin_chat_session", "session_kind")
