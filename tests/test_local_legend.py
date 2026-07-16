"""Tests for compute_local_legend_winners — the yearly leaderboard.

Awards one Local Legend per city (normalized `events.location`) per year,
tie-broken deterministically by earliest attendance datetime then alumni id.
Idempotent on re-run.
"""
from __future__ import annotations

from datetime import datetime
import uuid

import pytest
from sqlalchemy import JSON

from app.models.badge import Badge, UserBadge
from app.models.email_verification import (
    EmailVerification,  # noqa: F401 — needed for Alumni relationship resolution
)
from app.models.events import Event
from app.models.users import Alumni
from app.services import badges as service


@pytest.fixture(scope="module", autouse=True)
def _patch_badge_columns_for_sqlite():
    for col in Badge.__table__.columns:
        if col.type.__class__.__name__ in ("JSONB", "ARRAY"):
            col.type = JSON()
    for col in UserBadge.__table__.columns:
        if col.type.__class__.__name__ in ("JSONB",):
            col.type = JSON()
    return


@pytest.fixture
def db(db_session, engine):
    Badge.__table__.create(bind=engine, checkfirst=True)
    UserBadge.__table__.create(bind=engine, checkfirst=True)
    yield db_session
    db_session.expire_all()


def _alumni(db, alumni_id: str | None = None) -> Alumni:
    a = Alumni(
        id=alumni_id or str(uuid.uuid4()),
        email=f"{uuid.uuid4().hex[:8]}@innopolis.university",
        hashed_password="x",
        first_name="A",
        last_name="B",
        graduation_year="2018",
        is_verified=True,
        is_banned=False,
    )
    db.add(a)
    db.flush()
    return a


def _event(
    db,
    owner_id: str,
    location: str,
    when: datetime,
    participants: list[str],
    approved: bool = True,
) -> Event:
    e = Event(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        participants_ids=participants,
        title="e",
        description="",
        location=location,
        datetime=when,
        cost=0.0,
        is_online=False,
        approved=approved,
    )
    db.add(e)
    db.flush()
    return e


def _seed_badge(db) -> Badge:
    b = Badge(
        id=str(uuid.uuid4()),
        code="local_legend",
        name="Local Legend",
        description="",
        tier="gold",
        icon_key="crown",
        strategy="leaderboard",
        params={},
        trigger_metrics=[],
    )
    db.add(b)
    db.flush()
    return b


class TestComputeLocalLegend:
    def test_one_winner_per_city(self, db):
        _seed_badge(db)
        owner = _alumni(db)
        alice = _alumni(db, "alice")
        bob = _alumni(db, "bob")
        carol = _alumni(db, "carol")

        # Dubai: alice attends 3, bob 1 → alice wins.
        for i in range(3):
            _event(
                db, owner.id, "Dubai", datetime(2025, 6, i + 1),
                participants=[alice.id],
            )
        _event(
            db, owner.id, "Dubai", datetime(2025, 7, 1), participants=[bob.id]
        )
        # Berlin: carol 2, alice 1 → carol wins.
        for i in range(2):
            _event(
                db, owner.id, "Berlin", datetime(2025, 5, i + 1),
                participants=[carol.id],
            )
        _event(
            db, owner.id, "Berlin", datetime(2025, 5, 10), participants=[alice.id]
        )
        db.commit()

        winners = service.compute_local_legend_winners(db, 2025)

        assert len(winners) == 2
        winner_by_city = {w.extra["city"]: w.alumni_id for w in winners}
        assert winner_by_city == {"dubai": alice.id, "berlin": carol.id}

    def test_tiebreak_earliest_attendance(self, db):
        _seed_badge(db)
        owner = _alumni(db)
        alice = _alumni(db, "alice")
        bob = _alumni(db, "bob")

        # Both attend 2 events in Kazan → tie. Alice attended earlier (Jan 1),
        # so she wins even though Bob's IDs might sort otherwise.
        _event(db, owner.id, "Kazan", datetime(2025, 1, 1), participants=[alice.id])
        _event(db, owner.id, "Kazan", datetime(2025, 3, 1), participants=[alice.id])
        _event(db, owner.id, "Kazan", datetime(2025, 2, 1), participants=[bob.id])
        _event(db, owner.id, "Kazan", datetime(2025, 4, 1), participants=[bob.id])
        db.commit()

        winners = service.compute_local_legend_winners(db, 2025)

        assert len(winners) == 1
        assert winners[0].alumni_id == alice.id

    def test_no_events_in_year_awards_nothing(self, db):
        _seed_badge(db)
        winners = service.compute_local_legend_winners(db, 2025)
        assert winners == []

    def test_only_approved_events_counted(self, db):
        _seed_badge(db)
        owner = _alumni(db)
        alice = _alumni(db, "alice")
        bob = _alumni(db, "bob")

        _event(
            db, owner.id, "Prague", datetime(2025, 6, 1),
            participants=[alice.id, bob.id], approved=True,
        )
        # Bob has 2 unapproved events — shouldn't count.
        _event(
            db, owner.id, "Prague", datetime(2025, 7, 1),
            participants=[bob.id], approved=False,
        )
        _event(
            db, owner.id, "Prague", datetime(2025, 8, 1),
            participants=[bob.id], approved=False,
        )
        db.commit()

        winners = service.compute_local_legend_winners(db, 2025)

        # Tied at 1 each on approved events → earliest attendance wins.
        # Alice and Bob both first attended on Jun 1 (same event). Fall
        # through to alphabetical id tie-break → 'alice' < 'bob'.
        assert len(winners) == 1
        assert winners[0].alumni_id == alice.id

    def test_events_from_other_year_not_counted(self, db):
        _seed_badge(db)
        owner = _alumni(db)
        alice = _alumni(db, "alice")

        _event(
            db, owner.id, "Tokyo", datetime(2024, 12, 31),
            participants=[alice.id],
        )
        _event(
            db, owner.id, "Tokyo", datetime(2026, 1, 1), participants=[alice.id]
        )
        db.commit()

        winners = service.compute_local_legend_winners(db, 2025)
        assert winners == []

    def test_idempotent_on_rerun(self, db):
        _seed_badge(db)
        owner = _alumni(db)
        alice = _alumni(db, "alice")
        alice_id = alice.id  # keep a plain-str copy across commits

        _event(db, owner.id, "Rome", datetime(2025, 5, 1), participants=[alice_id])
        db.commit()

        first = service.compute_local_legend_winners(db, 2025)
        second = service.compute_local_legend_winners(db, 2025)

        # Both calls' semantics: first awards, second returns nothing
        # because the (alumni_id, badge_id, extra) unique constraint
        # rejects the duplicate insert.
        assert len(first) == 1
        assert second == []

    def test_three_cities_yield_three_winners_with_metadata(self, db):
        """Ticket #15 acceptance criterion: seed 3 cities with attendees,
        run compute_winners(year), assert 3 winners with correct metadata."""
        _seed_badge(db)
        owner = _alumni(db)
        alice = _alumni(db, "alice")
        bob = _alumni(db, "bob")
        carol = _alumni(db, "carol")

        # Dubai: alice attends 2 events, bob 1 → alice wins.
        for i in range(2):
            _event(
                db, owner.id, "Dubai", datetime(2025, 6, i + 1),
                participants=[alice.id],
            )
        _event(
            db, owner.id, "Dubai", datetime(2025, 7, 1), participants=[bob.id]
        )
        # Berlin: bob attends 2 events, carol 1 → bob wins.
        for i in range(2):
            _event(
                db, owner.id, "Berlin", datetime(2025, 5, i + 1),
                participants=[bob.id],
            )
        _event(
            db, owner.id, "Berlin", datetime(2025, 5, 15),
            participants=[carol.id],
        )
        # Innopolis: carol attends 2 events alone → carol wins.
        for i in range(2):
            _event(
                db, owner.id, "Innopolis", datetime(2025, 4, i + 1),
                participants=[carol.id],
            )
        db.commit()

        winners = service.compute_local_legend_winners(db, 2025)

        assert len(winners) == 3
        by_city = {w.extra["city"]: (w.alumni_id, w.extra["year"]) for w in winners}
        assert by_city == {
            "dubai": (alice.id, 2025),
            "berlin": (bob.id, 2025),
            "innopolis": (carol.id, 2025),
        }

    def test_location_case_and_whitespace_normalized(self, db):
        _seed_badge(db)
        owner = _alumni(db)
        alice = _alumni(db, "alice")

        # "Cairo", " cairo ", "CAIRO" should all count for the same city.
        _event(
            db, owner.id, "Cairo", datetime(2025, 1, 1), participants=[alice.id]
        )
        _event(
            db, owner.id, " cairo ", datetime(2025, 2, 1), participants=[alice.id]
        )
        _event(
            db, owner.id, "CAIRO", datetime(2025, 3, 1), participants=[alice.id]
        )
        db.commit()

        winners = service.compute_local_legend_winners(db, 2025)

        assert len(winners) == 1
        assert winners[0].extra == {"city": "cairo", "year": 2025}
