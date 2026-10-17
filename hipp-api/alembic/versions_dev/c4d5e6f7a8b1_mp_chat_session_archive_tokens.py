"""mp_chat session user archive and token usage

Revision ID: c4d5e6f7a8b1
Revises: a1b2e3bca9af
Create Date: 2026-10-11

"""
from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7a8b1"
down_revision = "a1b2e3bca9af"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_chat_session",
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
            comment="用户是否已把会话放进归档",
        ),
    )
    op.add_column(
        "vadmin_chat_session",
        sa.Column(
            "token_usage",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="累计 token 消耗",
        ),
    )


def downgrade():
    op.drop_column("vadmin_chat_session", "token_usage")
    op.drop_column("vadmin_chat_session", "is_archived")
