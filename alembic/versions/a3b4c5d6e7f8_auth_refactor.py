"""Add is_telegram_verified to alumni and refactor email_verifications for link-based flow; add telegram_verify_tokens table

Revision ID: a3b4c5d6e7f8
Revises: f1e2d3c4b5a6
Create Date: 2026-03-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, None] = 'f1e2d3c4b5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_telegram_verified to alumni
    op.add_column(
        'alumni',
        sa.Column('is_telegram_verified', sa.Boolean(), nullable=False, server_default='false'),
    )

    # Add link-based verification columns to email_verifications
    op.add_column(
        'email_verifications',
        sa.Column('verification_token', sa.String(), nullable=True),
    )
    op.add_column(
        'email_verifications',
        sa.Column('verification_token_expires', sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint(
        'uq_email_verifications_token', 'email_verifications', ['verification_token']
    )
    op.create_index(
        'ix_email_verifications_token', 'email_verifications', ['verification_token']
    )

    # Make verification_code and verification_code_expires nullable (no longer required for link flow)
    op.alter_column('email_verifications', 'verification_code', nullable=True)
    op.alter_column('email_verifications', 'verification_code_expires', nullable=True)

    # Create telegram_verify_tokens table
    op.create_table(
        'telegram_verify_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('alumni_id', sa.String(), sa.ForeignKey('alumni.id'), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token', name='uq_telegram_verify_tokens_token'),
    )
    op.create_index('ix_telegram_verify_tokens_token', 'telegram_verify_tokens', ['token'])
    op.create_index('ix_telegram_verify_tokens_alumni_id', 'telegram_verify_tokens', ['alumni_id'])


def downgrade() -> None:
    op.drop_index('ix_telegram_verify_tokens_alumni_id', 'telegram_verify_tokens')
    op.drop_index('ix_telegram_verify_tokens_token', 'telegram_verify_tokens')
    op.drop_table('telegram_verify_tokens')

    op.drop_index('ix_email_verifications_token', 'email_verifications')
    op.drop_constraint('uq_email_verifications_token', 'email_verifications', type_='unique')
    op.drop_column('email_verifications', 'verification_token_expires')
    op.drop_column('email_verifications', 'verification_token')

    op.drop_column('alumni', 'is_telegram_verified')
