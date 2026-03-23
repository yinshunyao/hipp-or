"""mp_chat session add agent snapshot fields

Revision ID: 9a2c1d7e4b11
Revises: 0b551fe68b03
Create Date: 2026-03-23

"""
from alembic import op
import sqlalchemy as sa

revision = "9a2c1d7e4b11"
down_revision = "0b551fe68b03"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_chat_session",
        sa.Column("agent_name_snapshot", sa.String(length=255), nullable=True, comment="智能体名称快照"),
    )
    op.add_column(
        "vadmin_chat_session",
        sa.Column("agent_avatar_snapshot", sa.String(length=500), nullable=True, comment="智能体头像快照"),
    )


def downgrade():
    op.drop_column("vadmin_chat_session", "agent_avatar_snapshot")
    op.drop_column("vadmin_chat_session", "agent_name_snapshot")
