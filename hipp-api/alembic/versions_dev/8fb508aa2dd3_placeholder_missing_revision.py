"""占位：恢复仓库中缺失的修订 id，便于与已写入 alembic_version 的数据库对齐。

若某环境 `alembic_version` 已为 `8fb508aa2dd3` 但仓库无对应脚本，会导致
`Can't locate revision identified by '8fb508aa2dd3'`。
本迁移为 no-op；实际 schema 变更由后续 `ba5e1f2a3c4d` 等脚本承担。

Revision ID: 8fb508aa2dd3
Revises: e73fc59fc7cc
Create Date: 2026-03-24

"""
from alembic import op

revision = "8fb508aa2dd3"
down_revision = "e73fc59fc7cc"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
