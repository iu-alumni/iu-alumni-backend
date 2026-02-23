"""merge_heads

Revision ID: abbdcb5d6cb9
Revises: 8f2a3b1c5d6e, d56a7033fce8
Create Date: 2026-02-24 01:43:49.937058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abbdcb5d6cb9'
down_revision: Union[str, None] = ('8f2a3b1c5d6e', 'd56a7033fce8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
