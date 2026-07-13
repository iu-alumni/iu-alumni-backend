"""Add projects table

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-07-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column(
            "contributors_ids",
            sa.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("cover", sa.String(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["alumni.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_projects_owner_id", "projects", ["owner_id"], unique=False
    )
    op.create_index(
        "ix_projects_approved", "projects", ["approved"], unique=False
    )
    op.create_index(
        "ix_projects_approved_created_at",
        "projects",
        ["approved", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_projects_approved_created_at", table_name="projects")
    op.drop_index("ix_projects_approved", table_name="projects")
    op.drop_index("ix_projects_owner_id", table_name="projects")
    op.drop_table("projects")
