"""mp_chat session is_topic_closed

Revision ID: ba5e1f2a3c4d
Revises: 8fb508aa2dd3
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa

revision = "ba5e1f2a3c4d"
down_revision = "8fb508aa2dd3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_chat_session",
        sa.Column(
            "is_topic_closed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
            comment="话题是否已结束（归档）",
        ),
    )


def downgrade():
    op.drop_column("vadmin_chat_session", "is_topic_closed")
