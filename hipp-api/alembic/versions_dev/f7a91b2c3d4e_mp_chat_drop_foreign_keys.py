"""vadmin_chat_* 移除数据库外键（逻辑引用 + 应用层 JOIN）

Revision ID: f7a91b2c3d4e
Revises: 80492c7c769a
Create Date: 2026-03-23

必须在「仅 alter 列」的 autogenerate 迁移（如 5e8d64b0274f）之前执行：先删外键，避免后续误带的 drop_index 触发 MySQL 1553。

"""
from alembic import op
from sqlalchemy import inspect

revision = 'f7a91b2c3d4e'
down_revision = '80492c7c769a'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    # 先删子表外键，再删会话表外键
    for table in ('vadmin_chat_message', 'vadmin_chat_session'):
        if not inspector.has_table(table):
            continue
        for fk in inspector.get_foreign_keys(table):
            op.drop_constraint(fk['name'], table, type_='foreignkey')


def downgrade():
    op.create_foreign_key(
        None,
        'vadmin_chat_session',
        'vadmin_auth_user',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        None,
        'vadmin_chat_session',
        'vadmin_agent',
        ['agent_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    op.create_foreign_key(
        None,
        'vadmin_chat_message',
        'vadmin_chat_session',
        ['session_id'],
        ['id'],
        ondelete='CASCADE',
    )
