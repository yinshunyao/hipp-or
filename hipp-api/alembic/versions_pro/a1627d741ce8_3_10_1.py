"""占位：`python main.py migrate` 在生产误生成的 autogenerate 噪声修订。

本迁移不改表（原脚本仅重复改 server_default / 类型噪音，已在库端执行过同类 ALTER，此处保留 revision 链）。

Revision ID: a1627d741ce8
Revises: d2e3f4a5b6c8
Create Date: 2026-10-16

"""

revision = "a1627d741ce8"
down_revision = "d2e3f4a5b6c8"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
