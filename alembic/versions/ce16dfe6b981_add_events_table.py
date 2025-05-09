"""Add events table

Revision ID: ce16dfe6b981
Revises: c36707b4309e
Create Date: 2025-03-07 22:07:18.592403

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce16dfe6b981'
down_revision: Union[str, None] = 'c36707b4309e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('owner_id', sa.String(), nullable=False),
    sa.Column('participants_ids', sa.ARRAY(sa.String()), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('location', sa.String(), nullable=False),
    sa.Column('datetime', sa.DateTime(), nullable=False),
    sa.Column('cost', sa.Integer(), nullable=False),
    sa.Column('is_online', sa.Boolean(), nullable=False),
    sa.Column('cover', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['alumni.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('events')
    # ### end Alembic commands ###
