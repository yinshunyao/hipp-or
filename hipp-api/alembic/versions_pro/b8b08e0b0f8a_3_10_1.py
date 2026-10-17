"""占位：`python main.py migrate` 在生产误生成的 autogenerate 噪声修订。

本迁移不改表（原脚本仅重复改 server_default / 类型噪音，已在库端执行过同类 ALTER，此处保留 revision 链）。

Revision ID: b8b08e0b0f8a
Revises: a9b0c1d2e3f5
Create Date: 2026-10-15

"""

revision = "b8b08e0b0f8a"
down_revision = "a9b0c1d2e3f5"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
