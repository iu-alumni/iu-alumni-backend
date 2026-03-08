"""add performance indexes

Revision ID: a2b3c4d5e6f7
Revises: f1e2d3c4b5a6
Create Date: 2026-03-08

"""
from typing import Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1e2d3c4b5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Events: index on owner_id (FK, used in owner/participant queries)
    op.create_index('ix_events_owner_id', 'events', ['owner_id'])

    # Events: index on datetime (ORDER BY in every list query)
    op.create_index('ix_events_datetime', 'events', ['datetime'])

    # Events: index on approved (WHERE in every public events query)
    op.create_index('ix_events_approved', 'events', ['approved'])

    # Events: composite index covering the most common query pattern:
    # .filter(approved == True).order_by(datetime.desc())
    op.create_index('ix_events_approved_datetime', 'events', ['approved', 'datetime'])

    # Alumni: index on is_verified (admin filter + login check)
    op.create_index('ix_alumni_is_verified', 'alumni', ['is_verified'])

    # Alumni: index on is_banned (admin filter + login check)
    op.create_index('ix_alumni_is_banned', 'alumni', ['is_banned'])


def downgrade() -> None:
    op.drop_index('ix_events_owner_id', table_name='events')
    op.drop_index('ix_events_datetime', table_name='events')
    op.drop_index('ix_events_approved', table_name='events')
    op.drop_index('ix_events_approved_datetime', table_name='events')
    op.drop_index('ix_alumni_is_verified', table_name='alumni')
    op.drop_index('ix_alumni_is_banned', table_name='alumni')
