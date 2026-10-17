"""占位：恢复仓库中缺失的修订 id，便于与已写入 alembic_version 的数据库对齐。

若某环境 `alembic_version` 已为 `04bbb43d68dc` 但仓库无对应脚本，会导致
`Can't locate revision identified by '04bbb43d68dc'`。
本迁移为 no-op；实际 schema 变更由后续 `c146cc30b075` 等脚本承担。

Revision ID: 04bbb43d68dc
Revises:
Create Date: 2026-04-09

"""
from alembic import op

revision = "04bbb43d68dc"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
