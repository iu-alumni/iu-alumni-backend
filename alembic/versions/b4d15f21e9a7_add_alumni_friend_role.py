"""Add alumni role enum + make graduation_year nullable

Revision ID: b4d15f21e9a7
Revises: f3a4b5c6d7e8
Create Date: 2026-07-28 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4d15f21e9a7"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Postgres enum. Stored as text is tempting for cheap migrations, but the
# enum gives us a real constraint at the DB level and neat OpenAPI schemas.
_role_enum = sa.Enum("alumni", "alumni_friend", name="alumni_role")


def upgrade() -> None:
    _role_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "alumni",
        sa.Column(
            "role",
            _role_enum,
            nullable=False,
            server_default="alumni",
        ),
    )
    # Alumni Friends have no graduation year by design; existing rows all
    # come in as role='alumni' and keep their year, so the loosened
    # constraint is safe.
    op.alter_column("alumni", "graduation_year", nullable=True)


def downgrade() -> None:
    op.alter_column("alumni", "graduation_year", nullable=False)
    op.drop_column("alumni", "role")
    _role_enum.drop(op.get_bind(), checkfirst=True)
