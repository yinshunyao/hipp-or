"""auth user type and wechat profile

Revision ID: e1f3a5b7c9d1
Revises: a8cb944df864
Create Date: 2026-03-26 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e1f3a5b7c9d1"
down_revision = "a8cb944df864"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_auth_user",
        sa.Column("user_type", sa.String(length=16), nullable=False, server_default="system", comment="用户类型(system/wechat)")
    )
    op.add_column(
        "vadmin_auth_user",
        sa.Column("wx_nickname", sa.String(length=128), nullable=True, comment="微信昵称")
    )
    op.add_column(
        "vadmin_auth_user",
        sa.Column("wx_avatar", sa.String(length=500), nullable=True, comment="微信头像")
    )
    op.execute("UPDATE vadmin_auth_user SET user_type='system' WHERE user_type IS NULL")
    op.alter_column("vadmin_auth_user", "user_type", server_default=None)


def downgrade():
    op.drop_column("vadmin_auth_user", "wx_avatar")
    op.drop_column("vadmin_auth_user", "wx_nickname")
    op.drop_column("vadmin_auth_user", "user_type")
