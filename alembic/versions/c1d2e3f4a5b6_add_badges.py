"""add badges

Revision ID: c1d2e3f4a5b6
Revises: a3b4c5d6e7f8
Create Date: 2026-06-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _badges_table() -> sa.Table:
    return sa.table(
        "badges",
        sa.column("id", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("tier", sa.String),
        sa.column("icon_key", sa.String),
        sa.column("strategy", sa.String),
        sa.column("params", postgresql.JSONB),
        sa.column("trigger_metrics", postgresql.ARRAY(sa.String)),
    )


_SEED = [
    dict(
        id="bdg-pioneer",
        code="pioneer",
        name="Pioneer",
        description="Among the first 100 alumni to pin their location on the map.",
        tier="special",
        icon_key="flag",
        strategy="first_n",
        params={"n": 100},
        trigger_metrics=["profile_updated"],
    ),
    dict(
        id="bdg-local-legend",
        code="local_legend",
        name="Local Legend",
        description="Most events attended in a single city in a given year.",
        tier="gold",
        icon_key="crown",
        strategy="leaderboard",
        params={},
        trigger_metrics=[],
    ),
    dict(
        id="bdg-founding-host",
        code="founding_host",
        name="Founding Host",
        description="Created the first alumni event in a city.",
        tier="gold",
        icon_key="flag",
        strategy="per_city_first",
        params={},
        trigger_metrics=["event_approved"],
    ),
    dict(
        id="bdg-networker",
        code="networker",
        name="Networker",
        description="Attended 5+ alumni events.",
        tier="bronze",
        icon_key="people",
        strategy="count_threshold",
        params={"metric": "events_attended", "threshold": 5},
        trigger_metrics=["event_attended"],
    ),
    dict(
        id="bdg-host-most",
        code="host_with_the_most",
        name="Host with the most",
        description="Organized 3+ events in different cities.",
        tier="silver",
        icon_key="trophy",
        strategy="distinct_count",
        params={"metric": "distinct_cities_hosted", "threshold": 3},
        trigger_metrics=["event_approved"],
    ),
    dict(
        id="bdg-rainmaker",
        code="rainmaker",
        name="Rainmaker",
        description="An event you created had 20+ attendees.",
        tier="silver",
        icon_key="spark",
        strategy="count_threshold",
        params={"metric": "max_attendees_on_owned", "threshold": 20},
        trigger_metrics=["event_attended", "event_approved"],
    ),
    dict(
        id="bdg-cross-city",
        code="cross_city_commuter",
        name="Cross-city commuter",
        description="Attended an event in a city different from your home city.",
        tier="bronze",
        icon_key="travel",
        strategy="count_threshold",
        params={"metric": "cross_city_attendances", "threshold": 1},
        trigger_metrics=["event_attended"],
    ),
    dict(
        id="bdg-innopolis-og",
        code="innopolis_og",
        name="Innopolis OG",
        description="Graduated from one of the first cohorts (2014-2019).",
        tier="gold",
        icon_key="graduation",
        strategy="year_range",
        params={"field": "graduation_year", "min": 2014, "max": 2019},
        trigger_metrics=["profile_updated"],
    ),
    dict(
        id="bdg-profile-pro",
        code="profile_pro",
        name="Profile Pro",
        description="Completed all profile fields: photo, location, biography, graduation year, Telegram.",
        tier="bronze",
        icon_key="profile_check",
        strategy="profile_completeness",
        params={
            "fields": [
                "avatar",
                "location",
                "biography",
                "graduation_year",
                "telegram_alias",
            ]
        },
        trigger_metrics=["profile_updated"],
    ),
    dict(
        id="bdg-badge-collector",
        code="badge_collector",
        name="Badge Collector",
        description="Earned 10+ badges.",
        tier="gold",
        icon_key="collection",
        strategy="badge_count",
        params={"threshold": 10},
        trigger_metrics=["badge_awarded"],
    ),
    dict(
        id="bdg-open-source",
        code="open_source_contributor",
        name="Open Source Contributor",
        description="Contributed to the platform's open-source codebase.",
        tier="silver",
        icon_key="code",
        strategy="manual",
        params={},
        trigger_metrics=[],
    ),
    dict(
        id="bdg-suggestion",
        code="suggestion_box",
        name="Suggestion Box",
        description="Submitted a badge or feature idea that got implemented.",
        tier="special",
        icon_key="lightbulb",
        strategy="manual",
        params={},
        trigger_metrics=[],
    ),
]


def upgrade() -> None:
    op.create_table(
        "badges",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("tier", sa.String(), nullable=False),
        sa.Column("icon_key", sa.String(), nullable=False),
        sa.Column("strategy", sa.String(), nullable=False),
        sa.Column(
            "params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "trigger_metrics",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("code", name="uq_badges_code"),
    )

    op.create_table(
        "user_badges",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "alumni_id",
            sa.String(),
            sa.ForeignKey("alumni.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "badge_id",
            sa.String(),
            sa.ForeignKey("badges.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "awarded_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("seen_at", sa.DateTime(), nullable=True),
        sa.Column(
            "extra",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("awarded_by", sa.String(), nullable=True),
        sa.UniqueConstraint(
            "alumni_id", "badge_id", "extra", name="uq_user_badges_unique"
        ),
    )
    op.create_index(
        "ix_user_badges_alumni", "user_badges", ["alumni_id"], unique=False
    )

    op.bulk_insert(_badges_table(), _SEED)


def downgrade() -> None:
    op.drop_index("ix_user_badges_alumni", table_name="user_badges")
    op.drop_table("user_badges")
    op.drop_table("badges")
