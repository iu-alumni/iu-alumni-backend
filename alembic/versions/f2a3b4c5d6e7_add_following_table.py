"""Add alumni follows table

Revision ID: f2a3b4c5d6e7
Revises: f1e2d3c4b5a6
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'f1e2d3c4b5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'alumni_follows',
        sa.Column('follower_id', sa.String(), nullable=False),
        sa.Column('followed_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['follower_id'], ['alumni.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['followed_id'], ['alumni.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('follower_id', 'followed_id'),
    )
    op.create_index('ix_alumni_follows_follower_id', 'alumni_follows', ['follower_id'])
    op.create_index('ix_alumni_follows_followed_id', 'alumni_follows', ['followed_id'])


def downgrade() -> None:
    op.drop_index('ix_alumni_follows_followed_id', table_name='alumni_follows')
    op.drop_index('ix_alumni_follows_follower_id', table_name='alumni_follows')
    op.drop_table('alumni_follows')
