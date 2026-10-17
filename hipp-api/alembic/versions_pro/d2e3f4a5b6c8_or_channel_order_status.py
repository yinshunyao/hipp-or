"""channel order paid/redeemed/refunded fields

Revision ID: d2e3f4a5b6c8
Revises: c1d2e3f4a5b7
Create Date: 2026-10-16

"""
from alembic import op
import sqlalchemy as sa

revision = "d2e3f4a5b6c8"
down_revision = "c1d2e3f4a5b7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("vadmin_or_channel_order", sa.Column("paid_at", sa.DateTime(), nullable=True, comment="已支付时间"))
    op.add_column(
        "vadmin_or_channel_order", sa.Column("redeemed_at", sa.DateTime(), nullable=True, comment="已核销时间")
    )
    op.add_column(
        "vadmin_or_channel_order", sa.Column("refunded_at", sa.DateTime(), nullable=True, comment="已退费时间")
    )
    op.add_column("vadmin_or_channel_order", sa.Column("refund_remark", sa.String(255), nullable=True))
    op.add_column(
        "vadmin_or_channel_order",
        sa.Column("refund_operator", sa.String(64), nullable=True, comment="退费操作人"),
    )
    op.create_index("ix_vadmin_or_channel_order_status", "vadmin_or_channel_order", ["status"])
    op.execute(
        "UPDATE vadmin_or_channel_order SET status='paid', paid_at=COALESCE(paid_at, create_datetime) "
        "WHERE status IN ('created','delivered')"
    )
    op.execute(
        "UPDATE vadmin_or_channel_order SET paid_at=COALESCE(paid_at, create_datetime) "
        "WHERE status='paid' AND paid_at IS NULL"
    )
    op.execute(
        "UPDATE vadmin_or_channel_order SET refunded_at=COALESCE(refunded_at, update_datetime) "
        "WHERE status='refunded' AND refunded_at IS NULL"
    )


def downgrade():
    op.drop_index("ix_vadmin_or_channel_order_status", table_name="vadmin_or_channel_order")
    op.drop_column("vadmin_or_channel_order", "refund_operator")
    op.drop_column("vadmin_or_channel_order", "refund_remark")
    op.drop_column("vadmin_or_channel_order", "refunded_at")
    op.drop_column("vadmin_or_channel_order", "redeemed_at")
    op.drop_column("vadmin_or_channel_order", "paid_at")
