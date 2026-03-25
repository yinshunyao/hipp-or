"""vadmin_agent add service_type

Revision ID: b2c4e6d8a0f1
Revises: 4d87edb03e58
Create Date: 2026-03-25

"""
from alembic import op
import sqlalchemy as sa

revision = "b2c4e6d8a0f1"
down_revision = "4d87edb03e58"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_agent",
        sa.Column(
            "service_type",
            sa.String(length=100),
            nullable=True,
            comment="智能客服类型（如需求分析、商业评估）",
        ),
    )


def downgrade():
    op.drop_column("vadmin_agent", "service_type")
