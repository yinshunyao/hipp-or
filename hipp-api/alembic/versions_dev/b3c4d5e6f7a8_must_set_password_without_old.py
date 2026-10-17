"""vadmin_auth_user.must_set_password_without_old for MP SMS first password

Revision ID: b3c4d5e6f7a8
Revises: f1f1d08ef849
Create Date: 2026-04-09

"""
from alembic import op
import sqlalchemy as sa

revision = "b3c4d5e6f7a8"
down_revision = "f1f1d08ef849"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_auth_user",
        sa.Column(
            "must_set_password_without_old",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
            comment="短信自助注册是否须无旧密码首次设密",
        ),
    )
    op.alter_column(
        "vadmin_auth_user",
        "must_set_password_without_old",
        server_default=None,
    )


def downgrade():
    op.drop_column("vadmin_auth_user", "must_set_password_without_old")
