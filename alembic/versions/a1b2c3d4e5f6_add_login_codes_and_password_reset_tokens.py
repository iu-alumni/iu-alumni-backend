"""Add login_codes and password_reset_tokens tables

Revision ID: a1b2c3d4e5f6
Revises: daa05a12a026
Create Date: 2026-03-08 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "daa05a12a026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "login_codes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("alumni_id", sa.String(), nullable=False),
        sa.Column("session_token", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["alumni_id"], ["alumni.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token"),
    )
    op.create_index("ix_login_codes_alumni_id", "login_codes", ["alumni_id"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("alumni_id", sa.String(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["alumni_id"], ["alumni.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        "ix_password_reset_tokens_alumni_id", "password_reset_tokens", ["alumni_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_alumni_id", "password_reset_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_index("ix_login_codes_alumni_id", "login_codes")
    op.drop_table("login_codes")
