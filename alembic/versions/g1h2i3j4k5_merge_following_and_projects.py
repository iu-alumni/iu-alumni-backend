"""Merge follow and projects heads

Revision ID: g1h2i3j4k5
Revises: d1e2f3a4b5c6, f2a3b4c5d6e7
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'g1h2i3j4k5'
down_revision: Union[str, None] = ('d1e2f3a4b5c6', 'f2a3b4c5d6e7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
