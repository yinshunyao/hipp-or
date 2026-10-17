"""把归档字段的数据库默认值补回去。

自动对照模型时去掉了 is_archived、token_usage 的默认值。
旧进程插入会话时不带这两列，没有默认值会写不进去。

Revision ID: f6a7b8c9d0e1
Revises: 91ada6e0d02b
Create Date: 2026-10-13

"""
from alembic import op
import sqlalchemy as sa

revision = "f6a7b8c9d0e1"
down_revision = "91ada6e0d02b"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "vadmin_chat_session",
        "is_archived",
        existing_type=sa.Boolean(),
        server_default=sa.text("0"),
        existing_nullable=False,
    )
    op.alter_column(
        "vadmin_chat_session",
        "token_usage",
        existing_type=sa.Integer(),
        server_default=sa.text("0"),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "vadmin_chat_session",
        "is_archived",
        existing_type=sa.Boolean(),
        server_default=None,
        existing_nullable=False,
    )
    op.alter_column(
        "vadmin_chat_session",
        "token_usage",
        existing_type=sa.Integer(),
        server_default=None,
        existing_nullable=False,
    )
