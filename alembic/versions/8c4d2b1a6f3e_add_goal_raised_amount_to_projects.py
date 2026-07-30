"""Add goal_amount + raised_amount columns to projects

Revision ID: 8c4d2b1a6f3e
Revises: 7a3b1c9d5e2f
Create Date: 2026-07-20 14:00:00.000000

Note: revision id renumbered from f3a4b5c6d7e8 (which was picked before
the "replace notifications table with cursor" migration landed on main
and stole the same hex). down_revision now points at the renumbered
donation_link migration (7a3b1c9d5e2f).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c4d2b1a6f3e"
down_revision: Union[str, None] = "7a3b1c9d5e2f"
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
