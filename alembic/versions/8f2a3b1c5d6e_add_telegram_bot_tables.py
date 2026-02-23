"""Add Telegram bot tables

Revision ID: 8f2a3b1c5d6e
Revises: 18e160caec1f
Create Date: 2026-02-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f2a3b1c5d6e'
down_revision: Union[str, None] = '18e160caec1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create telegram_users table
    op.create_table(
        'telegram_users',
        sa.Column('alias', sa.String(255), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('alias'),
        sa.UniqueConstraint('chat_id')
    )
    op.create_index(op.f('ix_telegram_users_alias'), 'telegram_users', ['alias'], unique=False)

    # Create polls table
    op.create_table(
        'polls',
        sa.Column('poll_id', sa.String(255), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('options', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('poll_id')
    )
    op.create_index(op.f('ix_polls_poll_id'), 'polls', ['poll_id'], unique=False)

    # Create feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alias', sa.String(255), nullable=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_alias'), 'feedback', ['alias'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_feedback_alias'), table_name='feedback')
    op.drop_table('feedback')
    op.drop_index(op.f('ix_polls_poll_id'), table_name='polls')
    op.drop_table('polls')
    op.drop_index(op.f('ix_telegram_users_alias'), table_name='telegram_users')
    op.drop_table('telegram_users')
