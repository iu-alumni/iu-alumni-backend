"""add_settings_table

Revision ID: 18e160caec1f
Revises: 9e14c7999275
Create Date: 2025-04-29 13:18:19.528041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '18e160caec1f'
down_revision: Union[str, None] = '9e14c7999275'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create settings table
    op.create_table('settings',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', JSONB(), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )

    # Insert default auto_approve setting
    op.execute(
        "INSERT INTO settings (key, value) VALUES ('event_settings', '{\"auto_approve\": true}'::jsonb)"
    )


def downgrade() -> None:
    op.drop_table('settings')
