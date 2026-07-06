"""Tests for the badge evaluator + individual strategies.

Scope: strategies that are self-contained enough to run against SQLite.
Local Legend (leaderboard) is intentionally deferred — its yearly winner
cron lives in another branch and is tracked separately.

The badges tables use JSONB + Postgres ARRAY in production. The shared
conftest excludes them from the in-memory SQLite schema, so this file
builds a scoped fixture that swaps those types for plain `JSON` and
creates the two tables locally. Strategies whose queries lean on the
`ARRAY.any()` operator on the events table are exercised by
monkey-patching the small integer helpers (`_events_attended_count`
etc.) — the strategy dispatch itself is what we care about here, not
the SQL that Postgres runs for it.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import JSON

from app.models.badge import Badge, UserBadge
from app.models.email_verification import EmailVerification  # noqa: F401 — needed for Alumni relationship resolution
from app.models.users import Alumni
from app.services import badges as service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def _patch_badge_columns_for_sqlite():
    """Swap JSONB / ARRAY on the badge tables for plain JSON so SQLite can
    create them. Done once per module — the swap is safe to leave in place
    for the rest of the test session because other tests avoid these tables.
    """
    for col in Badge.__table__.columns:
        if col.type.__class__.__name__ in ("JSONB", "ARRAY"):
            col.type = JSON()
    for col in UserBadge.__table__.columns:
        if col.type.__class__.__name__ in ("JSONB",):
            col.type = JSON()
    yield


@pytest.fixture
def db(db_session, engine):
    """Rebuild the badges + user_badges tables per test so counts are clean."""
    Badge.__table__.create(bind=engine, checkfirst=True)
    UserBadge.__table__.create(bind=engine, checkfirst=True)
    yield db_session
    # Best-effort cleanup — nested transaction in the shared fixture rolls
    # inserts back; we just make sure ORM state isn't holding references.
    db_session.expire_all()


def _mk_alumni(db, **kwargs) -> Alumni:
    defaults = {
        "id": str(uuid.uuid4()),
        "email": f"{uuid.uuid4().hex[:8]}@innopolis.university",
        "hashed_password": "x",
        "first_name": "Test",
        "last_name": "User",
        "graduation_year": "2018",
        "location": None,
        "biography": None,
        "show_location": False,
        "telegram_alias": None,
        "avatar": None,
        "is_verified": True,
        "is_banned": False,
    }
    defaults.update(kwargs)
    a = Alumni(**defaults)
    db.add(a)
    db.flush()
    return a


def _mk_badge(db, code, strategy, params=None, tier="bronze") -> Badge:
    b = Badge(
        id=str(uuid.uuid4()),
        code=code,
        name=code.replace("_", " ").title(),
        description="",
        tier=tier,
        icon_key="star",
        strategy=strategy,
        params=params or {},
        trigger_metrics=[],
    )
    db.add(b)
    db.flush()
    return b


# ---------------------------------------------------------------------------
# Pure logic — no DB helpers involved
# ---------------------------------------------------------------------------


class TestYearRange:
    """Innopolis OG — graduation year in 2014..2019."""

    def test_in_range_awards(self, db):
        alumni = _mk_alumni(db, graduation_year="2016")
        badge = _mk_badge(db, "innopolis_og", "year_range", {"min": 2014, "max": 2019})
        should, extra = service._should_award(db, alumni, badge)
        assert should is True
        assert extra == {}

    def test_below_range_does_not_award(self, db):
        alumni = _mk_alumni(db, graduation_year="2013")
        badge = _mk_badge(db, "innopolis_og", "year_range", {"min": 2014, "max": 2019})
        should, _ = service._should_award(db, alumni, badge)
        assert should is False

    def test_above_range_does_not_award(self, db):
        alumni = _mk_alumni(db, graduation_year="2020")
        badge = _mk_badge(db, "innopolis_og", "year_range", {"min": 2014, "max": 2019})
        should, _ = service._should_award(db, alumni, badge)
        assert should is False

    def test_boundary_years_award(self, db):
        badge = _mk_badge(db, "innopolis_og", "year_range", {"min": 2014, "max": 2019})
        low = _mk_alumni(db, graduation_year="2014")
        high = _mk_alumni(db, graduation_year="2019")
        assert service._should_award(db, low, badge)[0] is True
        assert service._should_award(db, high, badge)[0] is True

    def test_non_numeric_year_does_not_crash(self, db):
        alumni = _mk_alumni(db, graduation_year="unknown")
        badge = _mk_badge(db, "innopolis_og", "year_range", {"min": 2014, "max": 2019})
        should, _ = service._should_award(db, alumni, badge)
        assert should is False


class TestProfileCompleteness:
    """Profile Pro — all listed fields populated."""

    FIELDS = ["avatar", "location", "biography", "graduation_year", "telegram_alias"]

    def test_all_fields_populated_awards(self, db):
        alumni = _mk_alumni(
            db,
            avatar="a.png",
            location="Dubai",
            biography="hi",
            graduation_year="2018",
            telegram_alias="@t",
        )
        badge = _mk_badge(
            db, "profile_pro", "profile_completeness", {"fields": self.FIELDS}
        )
        should, _ = service._should_award(db, alumni, badge)
        assert should is True

    def test_missing_one_field_does_not_award(self, db):
        alumni = _mk_alumni(
            db,
            avatar="a.png",
            location="Dubai",
            biography=None,  # missing
            graduation_year="2018",
            telegram_alias="@t",
        )
        badge = _mk_badge(
            db, "profile_pro", "profile_completeness", {"fields": self.FIELDS}
        )
        should, _ = service._should_award(db, alumni, badge)
        assert should is False

    def test_empty_string_counts_as_missing(self, db):
        alumni = _mk_alumni(
            db,
            avatar="",  # empty string treated as unfilled
            location="Dubai",
            biography="bio",
            graduation_year="2018",
            telegram_alias="@t",
        )
        badge = _mk_badge(
            db, "profile_pro", "profile_completeness", {"fields": self.FIELDS}
        )
        should, _ = service._should_award(db, alumni, badge)
        assert should is False


# ---------------------------------------------------------------------------
# First-N — window-close semantics
# ---------------------------------------------------------------------------


class TestFirstN:
    """Pioneer — first N alumni to flip show_location and set a location."""

    def _mk_pioneer(self, db):
        return _mk_badge(db, "pioneer", "first_n", {"n": 3})

    def test_gates_on_show_location_true_and_location_set(self, db):
        badge = self._mk_pioneer(db)
        alumni = _mk_alumni(db, show_location=True, location="Dubai")
        should, _ = service._should_award(db, alumni, badge)
        assert should is True

    def test_show_location_false_blocks_award(self, db):
        badge = self._mk_pioneer(db)
        alumni = _mk_alumni(db, show_location=False, location="Dubai")
        should, _ = service._should_award(db, alumni, badge)
        assert should is False

    def test_missing_location_blocks_award(self, db):
        badge = self._mk_pioneer(db)
        alumni = _mk_alumni(db, show_location=True, location=None)
        should, _ = service._should_award(db, alumni, badge)
        assert should is False

    def test_window_closes_after_n_awards(self, db):
        """N=3 → 3 previous awards close the window even if the 4th qualifies."""
        badge = self._mk_pioneer(db)
        for _ in range(3):
            db.add(
                UserBadge(
                    id=str(uuid.uuid4()),
                    alumni_id=str(uuid.uuid4()),
                    badge_id=badge.id,
                    extra={},
                )
            )
        db.flush()
        alumni = _mk_alumni(db, show_location=True, location="Dubai")
        should, _ = service._should_award(db, alumni, badge)
        assert should is False


# ---------------------------------------------------------------------------
# Badge Count — Badge Collector
# ---------------------------------------------------------------------------


class TestBadgeCount:
    def test_below_threshold_does_not_award(self, db):
        collector = _mk_badge(db, "badge_collector", "badge_count", {"threshold": 3})
        alumni = _mk_alumni(db)
        # Two other badges awarded — still short of 3.
        for i in range(2):
            other = _mk_badge(db, f"other_{i}", "manual", {})
            db.add(
                UserBadge(
                    id=str(uuid.uuid4()),
                    alumni_id=alumni.id,
                    badge_id=other.id,
                    extra={},
                )
            )
        db.flush()
        should, _ = service._should_award(db, alumni, collector)
        assert should is False

    def test_at_threshold_awards(self, db):
        collector = _mk_badge(db, "badge_collector", "badge_count", {"threshold": 3})
        alumni = _mk_alumni(db)
        for i in range(3):
            other = _mk_badge(db, f"other_{i}", "manual", {})
            db.add(
                UserBadge(
                    id=str(uuid.uuid4()),
                    alumni_id=alumni.id,
                    badge_id=other.id,
                    extra={},
                )
            )
        db.flush()
        should, _ = service._should_award(db, alumni, collector)
        assert should is True


# ---------------------------------------------------------------------------
# Count-threshold strategies — stub the SQL helpers to keep tests portable
# ---------------------------------------------------------------------------


class TestCountThreshold:
    """Networker / Rainmaker / Cross-city commuter share the strategy but
    differ in the metric helper. We stub each helper so the test doesn't
    depend on the Postgres ARRAY operator used in production queries.
    """

    def test_networker_at_threshold_awards(self, db, monkeypatch):
        monkeypatch.setattr(service, "_events_attended_count", lambda *_a, **_k: 5)
        badge = _mk_badge(
            db,
            "networker",
            "count_threshold",
            {"metric": "events_attended", "threshold": 5},
        )
        alumni = _mk_alumni(db)
        should, _ = service._should_award(db, alumni, badge)
        assert should is True

    def test_networker_below_threshold_does_not_award(self, db, monkeypatch):
        monkeypatch.setattr(service, "_events_attended_count", lambda *_a, **_k: 4)
        badge = _mk_badge(
            db,
            "networker",
            "count_threshold",
            {"metric": "events_attended", "threshold": 5},
        )
        alumni = _mk_alumni(db)
        should, _ = service._should_award(db, alumni, badge)
        assert should is False

    def test_rainmaker_uses_biggest_hosted_event(self, db, monkeypatch):
        monkeypatch.setattr(service, "_max_attendees_on_owned", lambda *_a, **_k: 20)
        badge = _mk_badge(
            db,
            "rainmaker",
            "count_threshold",
            {"metric": "max_attendees_on_owned", "threshold": 20},
        )
        alumni = _mk_alumni(db)
        should, _ = service._should_award(db, alumni, badge)
        assert should is True

    def test_cross_city_needs_home_city_signal(self, db, monkeypatch):
        monkeypatch.setattr(service, "_cross_city_attendances", lambda *_a, **_k: 1)
        badge = _mk_badge(
            db,
            "cross_city_commuter",
            "count_threshold",
            {"metric": "cross_city_attendances", "threshold": 1},
        )
        alumni = _mk_alumni(db, location="Dubai")
        should, _ = service._should_award(db, alumni, badge)
        assert should is True


# ---------------------------------------------------------------------------
# Idempotency at the insertion layer
# ---------------------------------------------------------------------------


class TestAwardIdempotency:
    def test_awarding_same_badge_twice_returns_none_second_time(self, db):
        alumni = _mk_alumni(db)
        badge = _mk_badge(db, "innopolis_og", "year_range", {"min": 2014, "max": 2019})

        first = service._award(db, alumni.id, badge)
        assert first is not None
        db.commit()

        second = service._award(db, alumni.id, badge)
        # Unique constraint on (alumni_id, badge_id, extra) prevents duplicates.
        assert second is None

    def test_extra_metadata_lets_repeats_through(self, db):
        """Local Legend / Founding Host repeat per city/year via the extra
        column — the unique constraint keys on it too."""
        alumni = _mk_alumni(db)
        badge = _mk_badge(db, "local_legend", "leaderboard")

        first = service._award(db, alumni.id, badge, {"city": "dubai", "year": 2025})
        db.commit()
        second = service._award(db, alumni.id, badge, {"city": "berlin", "year": 2025})
        db.commit()

        assert first is not None
        assert second is not None


# ---------------------------------------------------------------------------
# Revocation
# ---------------------------------------------------------------------------


class TestRevokeIneligible:
    def test_revokes_when_criteria_no_longer_hold(self, db, monkeypatch):
        """Networker granted at 5 attendances → attendee count drops to 4 →
        revoke_ineligible deletes the row."""
        alumni = _mk_alumni(db)
        badge = _mk_badge(
            db,
            "networker",
            "count_threshold",
            {"metric": "events_attended", "threshold": 5},
        )
        db.add(
            UserBadge(
                id=str(uuid.uuid4()),
                alumni_id=alumni.id,
                badge_id=badge.id,
                extra={},
            )
        )
        db.commit()

        monkeypatch.setattr(service, "_events_attended_count", lambda *_a, **_k: 4)
        revoked = service.revoke_ineligible(db, alumni)

        assert revoked == ["networker"]
        remaining = (
            db.query(UserBadge).filter(UserBadge.alumni_id == alumni.id).count()
        )
        assert remaining == 0

    def test_preserves_when_criteria_still_hold(self, db, monkeypatch):
        alumni = _mk_alumni(db)
        badge = _mk_badge(
            db,
            "networker",
            "count_threshold",
            {"metric": "events_attended", "threshold": 5},
        )
        db.add(
            UserBadge(
                id=str(uuid.uuid4()),
                alumni_id=alumni.id,
                badge_id=badge.id,
                extra={},
            )
        )
        db.commit()

        monkeypatch.setattr(service, "_events_attended_count", lambda *_a, **_k: 5)
        revoked = service.revoke_ineligible(db, alumni)

        assert revoked == []
        assert (
            db.query(UserBadge).filter(UserBadge.alumni_id == alumni.id).count() == 1
        )

    def test_non_revocable_strategies_are_preserved(self, db):
        """Pioneer / Innopolis OG / Founding Host / Local Legend / manual
        awards must never be revoked, even if the raw signal appears to
        disappear (e.g. user edits their graduation year)."""
        alumni = _mk_alumni(db, graduation_year="1999")  # would fail year_range
        for code, strat in [
            ("pioneer", "first_n"),
            ("innopolis_og", "year_range"),
            ("founding_host", "per_city_first"),
            ("local_legend", "leaderboard"),
            ("open_source_contributor", "manual"),
        ]:
            b = _mk_badge(db, code, strat)
            db.add(
                UserBadge(
                    id=str(uuid.uuid4()),
                    alumni_id=alumni.id,
                    badge_id=b.id,
                    extra={},
                )
            )
        db.commit()

        revoked = service.revoke_ineligible(db, alumni)
        assert revoked == []
        assert (
            db.query(UserBadge).filter(UserBadge.alumni_id == alumni.id).count() == 5
        )

    def test_cascade_revokes_badge_collector(self, db, monkeypatch):
        """Badge Collector at threshold=3 → user has 3 badges (2 revocable +
        collector). One revocable badge's criteria fails → after that revoke
        the total badge count drops below 3 → Badge Collector revoked too.
        """
        alumni = _mk_alumni(db)
        networker = _mk_badge(
            db,
            "networker",
            "count_threshold",
            {"metric": "events_attended", "threshold": 5},
        )
        host = _mk_badge(
            db,
            "host_with_the_most",
            "distinct_count",
            {"metric": "distinct_cities_hosted", "threshold": 3},
        )
        collector = _mk_badge(
            db, "badge_collector", "badge_count", {"threshold": 3}
        )
        for b in (networker, host, collector):
            db.add(
                UserBadge(
                    id=str(uuid.uuid4()),
                    alumni_id=alumni.id,
                    badge_id=b.id,
                    extra={},
                )
            )
        db.commit()

        # Networker criteria fails; Host criteria still holds.
        monkeypatch.setattr(service, "_events_attended_count", lambda *_a, **_k: 0)
        monkeypatch.setattr(service, "_distinct_cities_hosted", lambda *_a, **_k: 3)

        revoked = service.revoke_ineligible(db, alumni)
        assert set(revoked) == {"networker", "badge_collector"}
        remaining_codes = {
            row.Badge.code
            for row in db.query(UserBadge, Badge)
            .join(Badge, Badge.id == UserBadge.badge_id)
            .filter(UserBadge.alumni_id == alumni.id)
            .all()
        }
        assert remaining_codes == {"host_with_the_most"}
