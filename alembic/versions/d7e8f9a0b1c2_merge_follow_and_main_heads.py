"""Merge follow and current main migration heads.

Revision ID: d7e8f9a0b1c2
Revises: c5d6e7f8a9b0, g1h2i3j4k5
Create Date: 2026-08-01 00:00:00.000000
"""

from collections.abc import Sequence


revision: str = "d7e8f9a0b1c2"
down_revision: str | tuple[str, str] | None = (
    "c5d6e7f8a9b0",
    "g1h2i3j4k5",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Join the follow and current main migration branches."""


def downgrade() -> None:
    """Split the graph back into the two parent heads."""
