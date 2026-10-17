"""or session fee global + user override

Revision ID: e7f8a9b0c1d3
Revises: f6a7b8c9d0e1
Create Date: 2026-10-15

"""
from alembic import op
import sqlalchemy as sa

revision = "e7f8a9b0c1d3"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vadmin_or_billing_setting",
        sa.Column("id", sa.Integer(), primary_key=True, comment="主键ID"),
        sa.Column("create_datetime", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), comment="创建时间"),
        sa.Column("update_datetime", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), comment="更新时间"),
        sa.Column("delete_datetime", sa.DateTime(), nullable=True, comment="删除时间"),
        sa.Column("is_delete", sa.Boolean(), server_default=sa.text("0"), nullable=False, comment="是否软删除"),
        sa.Column("config_key", sa.String(64), nullable=False, comment="配置键"),
        sa.Column("config_value", sa.String(64), nullable=False, comment="配置值"),
        comment="or 计费全局配置",
    )
    op.create_index("ix_vadmin_or_billing_setting_config_key", "vadmin_or_billing_setting", ["config_key"], unique=True)

    op.create_table(
        "vadmin_or_user_session_fee",
        sa.Column("id", sa.Integer(), primary_key=True, comment="主键ID"),
        sa.Column("create_datetime", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), comment="创建时间"),
        sa.Column("update_datetime", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), comment="更新时间"),
        sa.Column("delete_datetime", sa.DateTime(), nullable=True, comment="删除时间"),
        sa.Column("is_delete", sa.Boolean(), server_default=sa.text("0"), nullable=False, comment="是否软删除"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False, comment="每次会话费用（元）"),
        sa.UniqueConstraint("user_id", name="uq_or_user_session_fee_user"),
        comment="or 用户会话费用专属",
    )
    op.create_index("ix_vadmin_or_user_session_fee_user_id", "vadmin_or_user_session_fee", ["user_id"])

    op.execute(
        "INSERT INTO vadmin_or_billing_setting "
        "(config_key, config_value, is_delete, create_datetime, update_datetime) "
        "VALUES ('session_fee', '0.10', 0, NOW(), NOW())"
    )


def downgrade():
    op.drop_index("ix_vadmin_or_user_session_fee_user_id", table_name="vadmin_or_user_session_fee")
    op.drop_table("vadmin_or_user_session_fee")
    op.drop_index("ix_vadmin_or_billing_setting_config_key", table_name="vadmin_or_billing_setting")
    op.drop_table("vadmin_or_billing_setting")
