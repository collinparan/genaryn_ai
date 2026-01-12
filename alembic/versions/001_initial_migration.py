"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create custom types
    op.execute("CREATE TYPE userrole AS ENUM ('commander', 'staff', 'observer', 'admin')")
    op.execute("CREATE TYPE conversationtype AS ENUM ('tactical', 'strategic', 'operational', 'intelligence', 'logistics', 'general')")
    op.execute("CREATE TYPE classificationlevel AS ENUM ('unclassified', 'confidential', 'secret', 'top_secret')")
    op.execute("CREATE TYPE messagerole AS ENUM ('user', 'assistant', 'system')")
    op.execute("CREATE TYPE messagetype AS ENUM ('text', 'decision', 'analysis', 'recommendation', 'intelligence', 'warning')")
    op.execute("CREATE TYPE decisionstatus AS ENUM ('draft', 'pending', 'approved', 'rejected', 'executed')")
    op.execute("CREATE TYPE decisionpriority AS ENUM ('routine', 'priority', 'immediate', 'flash')")
    op.execute("CREATE TYPE decisiontype AS ENUM ('tactical', 'operational', 'strategic', 'administrative', 'logistics')")

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('rank', sa.String(length=50), nullable=True),
        sa.Column('unit', sa.String(length=255), nullable=True),
        sa.Column('role', postgresql.ENUM('commander', 'staff', 'observer', 'admin', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_password_change', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mission_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('type', postgresql.ENUM('tactical', 'strategic', 'operational', 'intelligence', 'logistics', 'general', name='conversationtype'), nullable=False),
        sa.Column('classification', postgresql.ENUM('unclassified', 'confidential', 'secret', 'top_secret', name='classificationlevel'), nullable=False),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_mission_id'), 'conversations', ['mission_id'], unique=False)
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)

    # Create messages table
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', postgresql.ENUM('user', 'assistant', 'system', name='messagerole'), nullable=False),
        sa.Column('type', postgresql.ENUM('text', 'decision', 'analysis', 'recommendation', 'intelligence', 'warning', name='messagetype'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('processing_time_ms', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('sources', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_messages_user_id'), 'messages', ['user_id'], unique=False)

    # Create decisions table
    op.create_table('decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mission_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('type', postgresql.ENUM('tactical', 'operational', 'strategic', 'administrative', 'logistics', name='decisiontype'), nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'pending', 'approved', 'rejected', 'executed', name='decisionstatus'), nullable=False),
        sa.Column('priority', postgresql.ENUM('routine', 'priority', 'immediate', 'flash', name='decisionpriority'), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('risk_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('alternatives', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('selected_coa', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('coa_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('estimated_success_probability', sa.Float(), nullable=True),
        sa.Column('mdmp_phase', sa.String(length=50), nullable=True),
        sa.Column('mdmp_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('outcome', sa.Text(), nullable=True),
        sa.Column('lessons_learned', sa.Text(), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decisions_conversation_id'), 'decisions', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_decisions_mission_id'), 'decisions', ['mission_id'], unique=False)
    op.create_index(op.f('ix_decisions_user_id'), 'decisions', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_decisions_user_id'), table_name='decisions')
    op.drop_index(op.f('ix_decisions_mission_id'), table_name='decisions')
    op.drop_index(op.f('ix_decisions_conversation_id'), table_name='decisions')
    op.drop_table('decisions')

    op.drop_index(op.f('ix_messages_user_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_conversation_id'), table_name='messages')
    op.drop_table('messages')

    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_mission_id'), table_name='conversations')
    op.drop_table('conversations')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop custom types
    op.execute("DROP TYPE IF EXISTS decisiontype")
    op.execute("DROP TYPE IF EXISTS decisionpriority")
    op.execute("DROP TYPE IF EXISTS decisionstatus")
    op.execute("DROP TYPE IF EXISTS messagetype")
    op.execute("DROP TYPE IF EXISTS messagerole")
    op.execute("DROP TYPE IF EXISTS classificationlevel")
    op.execute("DROP TYPE IF EXISTS conversationtype")
    op.execute("DROP TYPE IF EXISTS userrole")