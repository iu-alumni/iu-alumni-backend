"""add_email_verifications_table

Revision ID: b8cc16a01785
Revises: 18e160caec1f
Create Date: 2025-06-22 19:19:40.237083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8cc16a01785'
down_revision: Union[str, None] = '18e160caec1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create email_verifications table
    op.create_table(
        'email_verifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('alumni_id', sa.String(), nullable=False),
        sa.Column('verification_code', sa.String(), nullable=False),
        sa.Column('verification_code_expires', sa.DateTime(), nullable=False),
        sa.Column('verification_requested_at', sa.DateTime(), nullable=False),
        sa.Column('manual_verification_requested', sa.Boolean(), nullable=True, default=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['alumni_id'], ['alumni.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alumni_id')
    )
    op.create_index(op.f('ix_email_verifications_alumni_id'), 'email_verifications', ['alumni_id'], unique=True)


def downgrade() -> None:
    # Drop email_verifications table
    op.drop_index(op.f('ix_email_verifications_alumni_id'), table_name='email_verifications')
    op.drop_table('email_verifications')
