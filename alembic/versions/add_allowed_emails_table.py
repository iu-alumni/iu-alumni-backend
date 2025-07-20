"""add_allowed_emails_table

Revision ID: add_allowed_emails_table
Revises: b8cc16a01785
Create Date: 2025-07-07

"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision = 'add_allowed_emails_table'
down_revision = 'b8cc16a01785'  # Последняя миграция
branch_labels = None
depends_on = None


def upgrade():
    # Создание таблицы allowed_emails
    op.create_table('allowed_emails',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('hashed_email', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allowed_emails_hashed_email'), 'allowed_emails', ['hashed_email'], unique=True)


def downgrade():
    # Удаление таблицы allowed_emails
    op.drop_index(op.f('ix_allowed_emails_hashed_email'), table_name='allowed_emails')
    op.drop_table('allowed_emails')
