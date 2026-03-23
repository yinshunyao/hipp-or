"""mp_chat session and message tables

Revision ID: d4f2a1b3c8e0
Revises: 3ce826810bf0
Create Date: 2026-03-23

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4f2a1b3c8e0'
down_revision = '3ce826810bf0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'vadmin_chat_session',
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户'),
        sa.Column('agent_id', sa.Integer(), nullable=False, comment='智能体'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='展示标题'),
        sa.Column('last_message_preview', sa.String(length=500), nullable=True, comment='最近消息摘要'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, comment='是否置顶'),
        sa.Column('dify_conversation_id', sa.String(length=255), nullable=True, comment='Dify conversation_id'),
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('create_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('update_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('delete_datetime', sa.DateTime(), nullable=True, comment='删除时间'),
        sa.Column('is_delete', sa.Boolean(), nullable=False, comment='是否软删除'),
        sa.ForeignKeyConstraint(['agent_id'], ['vadmin_agent.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['vadmin_auth_user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='小程序用户与智能体会话',
    )
    op.create_index(op.f('ix_vadmin_chat_session_user_id'), 'vadmin_chat_session', ['user_id'], unique=False)
    op.create_index(op.f('ix_vadmin_chat_session_agent_id'), 'vadmin_chat_session', ['agent_id'], unique=False)

    op.create_table(
        'vadmin_chat_message',
        sa.Column('session_id', sa.Integer(), nullable=False, comment='会话'),
        sa.Column('role', sa.String(length=20), nullable=False, comment='user / assistant'),
        sa.Column('content', sa.Text(), nullable=False, comment='消息内容'),
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('create_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('update_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('delete_datetime', sa.DateTime(), nullable=True, comment='删除时间'),
        sa.Column('is_delete', sa.Boolean(), nullable=False, comment='是否软删除'),
        sa.ForeignKeyConstraint(['session_id'], ['vadmin_chat_session.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='小程序会话消息',
    )
    op.create_index(op.f('ix_vadmin_chat_message_session_id'), 'vadmin_chat_message', ['session_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_vadmin_chat_message_session_id'), table_name='vadmin_chat_message')
    op.drop_table('vadmin_chat_message')
    op.drop_index(op.f('ix_vadmin_chat_session_agent_id'), table_name='vadmin_chat_session')
    op.drop_index(op.f('ix_vadmin_chat_session_user_id'), table_name='vadmin_chat_session')
    op.drop_table('vadmin_chat_session')
