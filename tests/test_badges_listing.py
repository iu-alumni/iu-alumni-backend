"""Tests for the badge read APIs and the per-city founding-host hook.

test_badges.py covers strategy evaluation; these are the surfaces around it that
were untested: what the profile shows (`list_my_badges`), what other people see
(`list_for_user`), dismissing the "new badge" popup (`mark_seen`), and the
per-city first-host award.

Same SQLite caveat as test_badges.py — the badge tables use JSONB/ARRAY in
production, so those column types are swapped for plain JSON here.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _alumni(db) -> Alumni:
    alumni = Alumni(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4().hex[:8]}@innopolis.university",
        hashed_password="hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
    )
    db.add(alumni)
    db.flush()
    return alumni


# distinct_cities_hosted is the default metric because it filters on
# Event.owner_id. The events_attended metrics go through
# `Event.participants_ids.any(...)`, which is a Postgres ARRAY operator SQLite
# cannot execute — the same limitation test_badges.py documents.
def _badge(db, code: str, *, strategy: str = "distinct_count", params=None) -> Badge:
    badge = Badge(
        id=str(uuid.uuid4()),
        code=code,
        name=code.replace("_", " ").title(),
        description=f"{code} description",
        tier="gold",
        icon_key="star",
        strategy=strategy,
        params=params or {"metric": "distinct_cities_hosted", "threshold": 5},
        trigger_metrics=[],
    )
    db.add(badge)
    db.flush()
    return badge


def _award(db, alumni: Alumni, badge: Badge, *, seen: bool = False, extra=None) -> UserBadge:
    ub = UserBadge(
        id=str(uuid.uuid4()),
        alumni_id=alumni.id,
        badge_id=badge.id,
        awarded_at=_now(),
        seen_at=_now() if seen else None,
        extra=extra or {},
    )
    db.add(ub)
    db.flush()
    return ub


def _event(owner_id: str, location: str, *, approved: bool | None = True, when=None) -> Event:
    return Event(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        participants_ids=[],
        title="Meetup",
        description="A meetup",
        location=location,
        datetime=when or _now(),
        cost=0.0,
        is_online=False,
        cover=None,
        approved=approved,
    )


# ── list_my_badges ───────────────────────────────────────────────────────────


def test_my_badges_splits_earned_and_locked(db):
    alumni = _alumni(db)
    earned_badge = _badge(db, "first_event")
    _badge(db, "super_host")
    _award(db, alumni, earned_badge)

    result = service.list_my_badges(db, alumni)

    assert [b["code"] for b in result["earned"]] == ["first_event"]
    assert [b["code"] for b in result["locked"]] == ["super_host"]


def test_my_badges_reports_unseen_awards_as_newly_earned(db):
    alumni = _alumni(db)
    unseen = _badge(db, "first_event")
    seen = _badge(db, "second_event")
    _award(db, alumni, unseen, seen=False)
    _award(db, alumni, seen, seen=True)

    result = service.list_my_badges(db, alumni)

    # Both are earned, but only the unseen one should trigger the popup.
    assert {b["code"] for b in result["earned"]} == {"first_event", "second_event"}
    assert [b["code"] for b in result["newly_earned"]] == ["first_event"]


def test_my_badges_locked_entries_carry_progress(db):
    alumni = _alumni(db)
    _badge(db, "super_host", params={"metric": "distinct_cities_hosted", "threshold": 5})

    locked = service.list_my_badges(db, alumni)["locked"][0]

    # The UI renders "progress / threshold", so both must be present.
    assert locked["threshold"] == 5
    assert locked["progress"] is not None
    assert "metric_label" in locked


def test_my_badges_defaults_missing_extra_to_empty_dict(db):
    alumni = _alumni(db)
    badge = _badge(db, "founding_host")
    _award(db, alumni, badge, extra=None)

    earned = service.list_my_badges(db, alumni)["earned"][0]

    assert earned["extra"] == {}


def test_my_badges_returns_one_entry_per_award(db):
    alumni = _alumni(db)
    badge = _badge(db, "founding_host")
    _award(db, alumni, badge, extra={"city": "innopolis"})
    _award(db, alumni, badge, extra={"city": "dubai"})

    result = service.list_my_badges(db, alumni)

    # Repeatable badges are awarded per city, so each award is its own entry.
    assert len(result["earned"]) == 2
    assert {e["extra"]["city"] for e in result["earned"]} == {"innopolis", "dubai"}


def test_my_badges_with_empty_catalog(db):
    alumni = _alumni(db)

    result = service.list_my_badges(db, alumni)

    assert result == {"earned": [], "locked": [], "newly_earned": []}


# ── list_for_user (public view) ──────────────────────────────────────────────


def test_public_view_shows_earned_only(db):
    alumni = _alumni(db)
    earned_badge = _badge(db, "first_event")
    _badge(db, "super_host")
    _award(db, alumni, earned_badge, seen=False)

    result = service.list_for_user(db, alumni.id)

    # Other people must not see progress toward unearned badges, and the
    # unseen-popup state is private to the owner.
    assert [b["code"] for b in result["earned"]] == ["first_event"]
    assert result["locked"] == []
    assert result["newly_earned"] == []


def test_public_view_of_user_without_badges(db):
    alumni = _alumni(db)
    _badge(db, "super_host")

    assert service.list_for_user(db, alumni.id) == {
        "earned": [],
        "locked": [],
        "newly_earned": [],
    }


def test_public_view_is_scoped_to_the_requested_user(db):
    owner = _alumni(db)
    other = _alumni(db)
    badge = _badge(db, "first_event")
    _award(db, other, badge)

    assert service.list_for_user(db, owner.id)["earned"] == []
    assert len(service.list_for_user(db, other.id)["earned"]) == 1


# ── mark_seen ────────────────────────────────────────────────────────────────


def test_mark_seen_clears_the_popup(db):
    alumni = _alumni(db)
    badge = _badge(db, "first_event")
    award = _award(db, alumni, badge, seen=False)

    assert service.mark_seen(db, alumni, "first_event") is True
    assert award.seen_at is not None
    assert service.list_my_badges(db, alumni)["newly_earned"] == []


def test_mark_seen_is_idempotent(db):
    alumni = _alumni(db)
    badge = _badge(db, "first_event")
    _award(db, alumni, badge, seen=False)

    service.mark_seen(db, alumni, "first_event")

    # Nothing left unseen, so a repeat dismiss reports that it changed nothing.
    assert service.mark_seen(db, alumni, "first_event") is False


def test_mark_seen_unknown_badge_code(db):
    alumni = _alumni(db)

    assert service.mark_seen(db, alumni, "no_such_badge") is False


def test_mark_seen_does_not_touch_other_users(db):
    alumni = _alumni(db)
    other = _alumni(db)
    badge = _badge(db, "first_event")
    theirs = _award(db, other, badge, seen=False)

    assert service.mark_seen(db, alumni, "first_event") is False
    assert theirs.seen_at is None


# ── award_founding_host ──────────────────────────────────────────────────────


def test_founding_host_awarded_for_first_event_in_city(db):
    alumni = _alumni(db)
    _badge(db, "founding_host", strategy="manual")
    event = _event(alumni.id, "Innopolis")
    db.add(event)
    db.flush()

    award = service.award_founding_host(db, alumni, event)

    assert award is not None
    assert award.extra == {"city": "innopolis"}


def test_founding_host_normalises_city_casing_and_spacing(db):
    alumni = _alumni(db)
    _badge(db, "founding_host", strategy="manual")
    event = _event(alumni.id, "  InnoPOLIS  ")
    db.add(event)
    db.flush()

    award = service.award_founding_host(db, alumni, event)

    # City is the dedupe key, so it has to normalise or the same city awards twice.
    assert award.extra == {"city": "innopolis"}


def test_founding_host_not_awarded_when_an_earlier_event_exists(db):
    alumni = _alumni(db)
    _badge(db, "founding_host", strategy="manual")
    earlier = _event(alumni.id, "Innopolis", when=_now() - timedelta(days=1))
    later = _event(alumni.id, "Innopolis", when=_now())
    db.add_all([earlier, later])
    db.flush()

    assert service.award_founding_host(db, alumni, later) is None


def test_founding_host_ignores_earlier_unapproved_events(db):
    alumni = _alumni(db)
    _badge(db, "founding_host", strategy="manual")
    pending = _event(alumni.id, "Innopolis", approved=None, when=_now() - timedelta(days=1))
    approved = _event(alumni.id, "Innopolis", when=_now())
    db.add_all([pending, approved])
    db.flush()

    # A pending event was never public, so it should not block the award.
    assert service.award_founding_host(db, alumni, approved) is not None


def test_founding_host_requires_a_location(db):
    alumni = _alumni(db)
    _badge(db, "founding_host", strategy="manual")
    event = _event(alumni.id, "")
    db.add(event)
    db.flush()

    assert service.award_founding_host(db, alumni, event) is None


def test_founding_host_no_ops_when_badge_missing_from_catalog(db):
    alumni = _alumni(db)
    event = _event(alumni.id, "Innopolis")
    db.add(event)
    db.flush()

    # Deployments that have not seeded the badge must not blow up event approval.
    assert service.award_founding_host(db, alumni, event) is None
