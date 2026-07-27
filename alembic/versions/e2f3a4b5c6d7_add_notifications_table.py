"""Add notifications table

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-07-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("alumni_id", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["alumni_id"], ["alumni.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "alumni_id", "event_id", name="uq_notifications_alumni_event"
        ),
    )
    op.create_index(
        "ix_notifications_alumni_id", "notifications", ["alumni_id"], unique=False
    )
    op.create_index(
        "ix_notifications_event_id", "notifications", ["event_id"], unique=False
    )
    op.create_index(
        "ix_notifications_alumni_read",
        "notifications",
        ["alumni_id", "read_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_alumni_read", table_name="notifications")
    op.drop_index("ix_notifications_event_id", table_name="notifications")
    op.drop_index("ix_notifications_alumni_id", table_name="notifications")
    op.drop_table("notifications")
