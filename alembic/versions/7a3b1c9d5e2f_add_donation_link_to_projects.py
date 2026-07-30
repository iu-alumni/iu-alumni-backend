"""Add donation_link column to projects

Revision ID: 7a3b1c9d5e2f
Revises: f3a4b5c6d7e8
Create Date: 2026-07-16 13:00:00.000000

Note: revision id renumbered from e2f3a4b5c6d7 (which was picked before
the notifications-table migration landed on main and stole the same
hex). down_revision bumped to the current main head to keep the chain
linear rather than forcing an alembic merge.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a3b1c9d5e2f"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("donation_link", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("projects", "donation_link")
