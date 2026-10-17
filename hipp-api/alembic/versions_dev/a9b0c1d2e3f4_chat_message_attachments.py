"""chat message attachments

Revision ID: a9b0c1d2e3f4
Revises: f8a9b0c1d2e3
Create Date: 2026-10-15

"""
from alembic import op
import sqlalchemy as sa

revision = "a9b0c1d2e3f4"
down_revision = "f8a9b0c1d2e3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vadmin_chat_message",
        sa.Column(
            "attachments",
            sa.Text(),
            nullable=True,
            comment="附件 JSON 数组",
        ),
    )


def downgrade():
    op.drop_column("vadmin_chat_message", "attachments")
