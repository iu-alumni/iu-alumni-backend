"""merge all heads

Revision ID: f1e2d3c4b5a6
Revises: abbdcb5d6cb9, a1b2c3d4e5f6
Create Date: 2026-03-08

"""
from typing import Sequence, Union

revision: str = 'f1e2d3c4b5a6'
down_revision: Union[str, None] = ('abbdcb5d6cb9', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
