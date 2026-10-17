"""chat session fee_charged

Revision ID: f8a9b0c1d2e4
Revises: e7f8a9b0c1d3
Create Date: 2026-10-15

"""
from alembic import op
import sqlalchemy as sa

revision = "f8a9b0c1d2e4"
down_revision = "e7f8a9b0c1d3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_chat_session",
        sa.Column(
            "fee_charged",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
            comment="是否已扣会话咨询费",
        ),
    )


def downgrade():
    op.drop_column("vadmin_chat_session", "fee_charged")
