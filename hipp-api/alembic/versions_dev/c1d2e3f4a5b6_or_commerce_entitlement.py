"""or commerce entitlement tables

Revision ID: c1d2e3f4a5b6
Revises: a9b0c1d2e3f4
Create Date: 2026-10-16

"""
from alembic import op
import sqlalchemy as sa

revision = "c1d2e3f4a5b6"
down_revision = "a9b0c1d2e3f4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vadmin_or_entitlement",
        sa.Column("id", sa.Integer(), primary_key=True, comment="主键ID"),
        sa.Column("create_datetime", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), comment="创建时间"),
        sa.Column("update_datetime", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), comment="更新时间"),
        sa.Column("delete_datetime", sa.DateTime(), nullable=True, comment="删除时间"),
        sa.Column("is_delete", sa.Boolean(), server_default=sa.text("0"), nullable=False, comment="是否软删除"),
        sa.Column("token", sa.String(64), nullable=False, comment="短链令牌"),
        sa.Column("status", sa.String(16), nullable=False, server_default="unused", comment="unused/bound/used/void/expired"),
        sa.Column("service_type", sa.String(32), nullable=False, server_default="需求分析", comment="可用智能体 service_type"),
        sa.Column("channel", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("external_order_id", sa.String(128), nullable=True, comment="渠道订单号"),
        sa.Column("bound_user_id", sa.Integer(), nullable=True),
        sa.Column("bound_session_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("void_at", sa.DateTime(), nullable=True),
        sa.Column("remark", sa.String(255), nullable=True),
        sa.UniqueConstraint("token", name="uq_or_entitlement_token"),
        sa.UniqueConstraint("channel", "external_order_id", name="uq_or_entitlement_channel_order"),
        comment="电商/手工短链次卡权益",
    )
    op.create_index("ix_vadmin_or_entitlement_token", "vadmin_or_entitlement", ["token"])
    op.create_index("ix_vadmin_or_entitlement_status", "vadmin_or_entitlement", ["status"])
    op.create_index("ix_vadmin_or_entitlement_channel", "vadmin_or_entitlement", ["channel"])
    op.create_index("ix_vadmin_or_entitlement_external_order_id", "vadmin_or_entitlement", ["external_order_id"])
    op.create_index("ix_vadmin_or_entitlement_bound_user_id", "vadmin_or_entitlement", ["bound_user_id"])

    op.create_table(
        "vadmin_or_channel_order",
        sa.Column("id", sa.Integer(), primary_key=True, comment="主键ID"),
        sa.Column("create_datetime", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), comment="创建时间"),
        sa.Column("update_datetime", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), comment="更新时间"),
        sa.Column("delete_datetime", sa.DateTime(), nullable=True, comment="删除时间"),
        sa.Column("is_delete", sa.Boolean(), server_default=sa.text("0"), nullable=False, comment="是否软删除"),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("external_order_id", sa.String(128), nullable=False),
        sa.Column("sku_code", sa.String(64), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="created", comment="created/delivered/refunded"),
        sa.Column("entitlement_id", sa.Integer(), nullable=True),
        sa.Column("short_url", sa.String(512), nullable=True),
        sa.Column("deliver_ok", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("deliver_payload", sa.Text(), nullable=True),
        sa.Column("raw_event", sa.Text(), nullable=True),
        sa.UniqueConstraint("channel", "external_order_id", name="uq_or_channel_order"),
        comment="渠道履约订单",
    )
    op.create_index("ix_vadmin_or_channel_order_channel", "vadmin_or_channel_order", ["channel"])
    op.create_index("ix_vadmin_or_channel_order_external_order_id", "vadmin_or_channel_order", ["external_order_id"])
    op.create_index("ix_vadmin_or_channel_order_entitlement_id", "vadmin_or_channel_order", ["entitlement_id"])


def downgrade():
    op.drop_table("vadmin_or_channel_order")
    op.drop_table("vadmin_or_entitlement")
