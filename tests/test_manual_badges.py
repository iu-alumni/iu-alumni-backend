"""Tests for manual_award / manual_revoke service functions.

Covers the two admin actions introduced with the manual-award endpoints:
happy path, duplicate rejection, missing badge, and missing user_badges row
on revoke.
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


def _alumni(db) -> Alumni:
    a = Alumni(
        id=str(uuid.uuid4()),
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


def _badge(db, code: str = "open_source_contributor") -> Badge:
    b = Badge(
        id=str(uuid.uuid4()),
        code=code,
        name=code.replace("_", " ").title(),
        description="",
        tier="special",
        icon_key="code",
        strategy="manual",
        params={},
        trigger_metrics=[],
    )
    db.add(b)
    db.flush()
    return b


class TestManualAward:
    def test_awards_and_records_admin(self, db):
        alumni = _alumni(db)
        _badge(db)
        admin_id = "admin-1"

        row = service.manual_award(
            db, alumni, "open_source_contributor", admin_id=admin_id
        )

        assert row.alumni_id == alumni.id
        assert row.awarded_by == admin_id

    def test_missing_badge_raises(self, db):
        alumni = _alumni(db)
        with pytest.raises(service.ManualAwardError, match="does not exist"):
            service.manual_award(db, alumni, "unknown_badge", admin_id="admin-1")

    def test_duplicate_raises(self, db):
        alumni = _alumni(db)
        _badge(db)
        service.manual_award(
            db, alumni, "open_source_contributor", admin_id="admin-1"
        )
        with pytest.raises(service.ManualAwardError, match="already awarded"):
            service.manual_award(
                db, alumni, "open_source_contributor", admin_id="admin-2"
            )


class TestManualRevoke:
    def test_revokes_when_held(self, db):
        alumni = _alumni(db)
        _badge(db)
        service.manual_award(
            db, alumni, "open_source_contributor", admin_id="admin-1"
        )

        service.manual_revoke(db, alumni, "open_source_contributor")

        assert (
            db.query(UserBadge).filter(UserBadge.alumni_id == alumni.id).count()
            == 0
        )

    def test_missing_badge_raises(self, db):
        alumni = _alumni(db)
        with pytest.raises(service.ManualAwardError, match="does not exist"):
            service.manual_revoke(db, alumni, "unknown_badge")

    def test_not_held_raises(self, db):
        alumni = _alumni(db)
        _badge(db)
        with pytest.raises(service.ManualAwardError, match="does not hold"):
            service.manual_revoke(db, alumni, "open_source_contributor")

    def test_revoke_matches_on_metadata(self, db):
        """Founding Host / Local Legend can repeat per metadata — revoke
        with a specific metadata should only drop the matching row."""
        alumni = _alumni(db)
        b = _badge(db, code="local_legend")
        db.add(
            UserBadge(
                id=str(uuid.uuid4()),
                alumni_id=alumni.id,
                badge_id=b.id,
                extra={"city": "dubai", "year": 2025},
            )
        )
        db.add(
            UserBadge(
                id=str(uuid.uuid4()),
                alumni_id=alumni.id,
                badge_id=b.id,
                extra={"city": "berlin", "year": 2025},
            )
        )
        db.commit()

        service.manual_revoke(
            db, alumni, "local_legend", metadata={"city": "dubai", "year": 2025}
        )

        remaining_extras = [
            r.extra
            for r in db.query(UserBadge)
            .filter(UserBadge.alumni_id == alumni.id)
            .all()
        ]
        assert remaining_extras == [{"city": "berlin", "year": 2025}]
