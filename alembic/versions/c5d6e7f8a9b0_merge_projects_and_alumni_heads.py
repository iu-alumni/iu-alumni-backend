"""Merge projects and alumni-role migration heads.

Revision ID: c5d6e7f8a9b0
Revises: 8c4d2b1a6f3e, b4d15f21e9a7
Create Date: 2026-07-30 05:30:00.000000
"""

from collections.abc import Sequence


revision: str = "c5d6e7f8a9b0"
down_revision: str | tuple[str, str] | None = (
    "8c4d2b1a6f3e",
    "b4d15f21e9a7",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Join both migration branches without changing the schema."""


def downgrade() -> None:
    """Split the migration graph back into its two parent heads."""
