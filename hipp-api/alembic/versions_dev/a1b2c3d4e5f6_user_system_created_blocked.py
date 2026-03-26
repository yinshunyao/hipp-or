"""user is_system_created and is_blocked

Revision ID: a1b2c3d4e5f6
Revises: 42883dd82a74
Create Date: 2026-03-26 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "42883dd82a74"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_auth_user",
        sa.Column(
            "is_system_created",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
            comment="是否由系统/后台创建（用于多标签「系统创建」）",
        ),
    )
    op.add_column(
        "vadmin_auth_user",
        sa.Column(
            "is_blocked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
            comment="是否拉黑（禁止登录）",
        ),
    )
    op.alter_column("vadmin_auth_user", "is_system_created", server_default=None)
    op.alter_column("vadmin_auth_user", "is_blocked", server_default=None)


def downgrade():
    op.drop_column("vadmin_auth_user", "is_blocked")
    op.drop_column("vadmin_auth_user", "is_system_created")
