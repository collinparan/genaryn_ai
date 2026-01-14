"""Rename metadata to conversation_metadata

Revision ID: 002
Revises: 001
Create Date: 2026-01-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename metadata column to conversation_metadata in conversations table
    op.alter_column('conversations', 'metadata', new_column_name='conversation_metadata')


def downgrade() -> None:
    # Rename conversation_metadata back to metadata
    op.alter_column('conversations', 'conversation_metadata', new_column_name='metadata')
