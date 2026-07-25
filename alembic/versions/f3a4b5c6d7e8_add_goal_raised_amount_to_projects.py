"""Add goal_amount + raised_amount columns to projects

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-07-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("goal_amount", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column(
            "raised_amount",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("projects", "raised_amount")
    op.drop_column("projects", "goal_amount")
