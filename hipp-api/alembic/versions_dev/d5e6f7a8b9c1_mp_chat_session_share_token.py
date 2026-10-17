"""mp_chat session share token

Revision ID: d5e6f7a8b9c1
Revises: c4d5e6f7a8b1
Create Date: 2026-10-13

"""
from alembic import op
import sqlalchemy as sa

revision = "d5e6f7a8b9c1"
down_revision = "c4d5e6f7a8b1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_chat_session",
        sa.Column("share_token", sa.String(length=64), nullable=True, comment="归档分享令牌"),
    )
    op.create_index("ix_vadmin_chat_session_share_token", "vadmin_chat_session", ["share_token"], unique=True)


def downgrade():
    op.drop_index("ix_vadmin_chat_session_share_token", table_name="vadmin_chat_session")
    op.drop_column("vadmin_chat_session", "share_token")
