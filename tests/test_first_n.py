"""Tests for the `first_n` badge-award strategy (Pioneer badge).

Rule: at most `n` awards are ever issued for a `first_n` badge. Beyond
`n`, the strategy short-circuits and no further rows are inserted.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import JSON

from app.models.badge import Badge, UserBadge
from app.models.email_verification import (
    EmailVerification,  # noqa: F401 — needed for Alumni relationship resolution
)
from app.models.users import Alumni
from app.services import badges as service


N = 100


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


def _pioneer(db) -> Badge:
    b = Badge(
        id=str(uuid.uuid4()),
        code="pioneer",
        name="Pioneer",
        description="First to pin location.",
        tier="special",
        icon_key="flag",
        strategy="first_n",
        params={"n": N},
        trigger_metrics=["profile_updated"],
    )
    db.add(b)
    db.flush()
    return b


def _alumni(db) -> Alumni:
    a = Alumni(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4().hex[:8]}@innopolis.university",
        hashed_password="x",
        first_name="A",
        last_name="B",
        graduation_year="2018",
        location="Innopolis",
        show_location=True,
        is_verified=True,
        is_banned=False,
    )
    db.add(a)
    db.flush()
    return a


class TestFirstNSequential:
    """Serial invariant: 200 in-order triggers cap out at exactly N awards.

    This is the sequential form of the race guarantee — every eval reads
    the count under the same transaction, so once N rows exist, the
    strategy stops awarding.

    We drive the strategy directly (`_should_award` + `_award`) rather
    than through `evaluate_for_user`. The latter loads badges via a
    `Badge.trigger_metrics.contains(...)` filter that expects a real
    Postgres ARRAY column; the SQLite fixture rewrites the column to
    JSON but SQLite has no equivalent operator so the query blows up
    on `sqlite3.OperationalError: unrecognized token: "@"`. The Pioneer
    logic itself lives in `_should_award(first_n)` — testing it in
    isolation is what the ticket asked for.
    """

    def test_stops_at_n_after_two_hundred_triggers(self, db):
        badge = _pioneer(db)

        # 200 distinct alumni, each triggers the eval once. Only the
        # first N should walk away with a Pioneer row.
        alumni = [_alumni(db) for _ in range(200)]
        db.commit()

        for a in alumni:
            should, _ = service._should_award(db, a, badge)
            if should:
                service._award(db, a.id, badge)
        db.commit()

        awarded = (
            db.query(UserBadge)
            .filter(UserBadge.badge_id == badge.id)
            .all()
        )
        assert len(awarded) == N

        # The winners are exactly the first N alumni (deterministic order).
        winner_ids = {ub.alumni_id for ub in awarded}
        expected = {alumni[i].id for i in range(N)}
        assert winner_ids == expected

    def test_no_award_for_alumni_without_location_signal(self, db):
        badge = _pioneer(db)

        # Alumnus with show_location=False → doesn't qualify, doesn't
        # consume a slot.
        a = _alumni(db)
        a.show_location = False
        db.commit()

        should, _ = service._should_award(db, a, badge)
        assert should is False

        # And the DB should still have zero Pioneer awards.
        assert (
            db.query(UserBadge).filter(UserBadge.badge_id == badge.id).count()
            == 0
        )


class TestFirstNConcurrent:
    """True race protection requires DB-level locking (advisory lock or
    SELECT FOR UPDATE) which the current implementation does not use.

    Under real concurrent load with 200 alumni each firing the profile-
    updated trigger simultaneously, the SELECT COUNT / INSERT gap is
    unprotected and >N rows can land. Documented here as a known gap
    against the ticket's original acceptance criterion (`iu-alumni/
    iu-alumni-backend#115`); the SQLite test fixture also lacks real
    concurrency, so the assertion can't be exercised locally either
    way.
    """

    @pytest.mark.skip(reason="Requires DB-level locking + concurrent fixture; see docstring.")
    def test_two_hundred_parallel_triggers_award_exactly_n(self, db):
        _pioneer(db)
        # Sketch: build 200 alumni, evaluate concurrently, assert exactly N rows.
        _ = [_alumni(db) for _ in range(200)]
        db.commit()
        # Would need: run each evaluate_for_user in its own transaction,
        # concurrently, and assert the badge_id count == N.
        raise NotImplementedError
