"""Pagination coverage for the remaining cursor-paginated routes.

Two of the four routes audited so far had real cursor defects (#161, #162), so
these two are pinned the same way: walk every page and assert each row is seen
exactly once, with filters held across page boundaries.

get_profiles keys on id alone, which is the primary key and therefore unique —
no tiebreaker needed. list_projects uses the composite (created_at, id) cursor,
so it gets the tied-timestamp walk that caught the admin projects bug.
"""

from datetime import UTC, datetime, timedelta
import uuid

import pytest

from app.api.routes.profile.get_profiles import get_profiles
from app.api.routes.projects.list_projects import list_projects
from app.models.email_verification import (
    EmailVerification,  # noqa: F401 — needed for Alumni relationship resolution
)
from app.models.projects import Project
from app.models.users import Admin, Alumni


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _alumni(
    user_id: str,
    *,
    first_name: str = "Ada",
    last_name: str = "Lovelace",
    location: str | None = None,
    show_location: bool = True,
    is_verified: bool = True,
    is_banned: bool = False,
) -> Alumni:
    return Alumni(
        id=user_id,
        email=f"{user_id}@innopolis.university",
        hashed_password="hash",
        first_name=first_name,
        last_name=last_name,
        graduation_year="2024",
        location=location,
        show_location=show_location,
        is_verified=is_verified,
        is_banned=is_banned,
    )


def _project(owner_id: str, project_id: str, *, title="Project", approved=True, created=None):
    return Project(
        id=project_id,
        owner_id=owner_id,
        contributors_ids=[],
        title=title,
        description="A project",
        cover=None,
        approved=approved,
        created_at=created or _now(),
    )


def _viewer() -> Admin:
    return Admin(id="admin-1", email="admin@innopolis.university")


# ── get_profiles ─────────────────────────────────────────────────────────────


def _profiles(db_session, **kwargs):
    params = {
        "search": None,
        "location": None,
        "cursor": None,
        "limit": 50,
        "db": db_session,
        "current_user": _viewer(),
    }
    params.update(kwargs)
    return get_profiles(**params)


def test_profiles_search_matches_either_name(db_session):
    db_session.add_all(
        [
            _alumni("u1", first_name="Ada", last_name="Lovelace"),
            _alumni("u2", first_name="Grace", last_name="Hopper"),
        ]
    )
    db_session.commit()

    assert [p.id for p in _profiles(db_session, search="ada").items] == ["u1"]
    assert [p.id for p in _profiles(db_session, search="hopper").items] == ["u2"]


def test_profiles_location_filter_excludes_hidden_and_ineligible(db_session):
    db_session.add_all(
        [
            _alumni("visible", location="Russia, Innopolis"),
            _alumni("hidden", location="Russia, Innopolis", show_location=False),
            _alumni("unverified", location="Russia, Innopolis", is_verified=False),
            _alumni("banned", location="Russia, Innopolis", is_banned=True),
            _alumni("elsewhere", location="UAE, Dubai"),
        ]
    )
    db_session.commit()

    ids = [p.id for p in _profiles(db_session, location="russia, innopolis").items]

    # The pin count on the map applies all three gates, so the city detail list
    # has to match it exactly or the counts disagree.
    assert ids == ["visible"]


def test_profiles_cursor_walks_every_row_exactly_once(db_session):
    db_session.add_all([_alumni(f"u{i}") for i in range(1, 6)])
    db_session.commit()

    seen: list[str] = []
    cursor = None
    for _ in range(10):  # bounded so a broken cursor cannot loop forever
        page = _profiles(db_session, limit=2, cursor=cursor)
        seen.extend(p.id for p in page.items)
        cursor = page.next_cursor
        if cursor is None:
            break

    assert seen == [f"u{i}" for i in range(1, 6)]
    assert len(seen) == len(set(seen))


def test_profiles_filters_survive_pagination(db_session):
    db_session.add_all(
        [
            _alumni("a1", first_name="Ada"),
            _alumni("b1", first_name="Grace"),
            _alumni("a2", first_name="Ada"),
            _alumni("a3", first_name="Ada"),
        ]
    )
    db_session.commit()

    first = _profiles(db_session, search="ada", limit=2)
    second = _profiles(db_session, search="ada", limit=2, cursor=first.next_cursor)

    assert [p.id for p in first.items] == ["a1", "a2"]
    assert [p.id for p in second.items] == ["a3"]


# ── list_projects (public) ───────────────────────────────────────────────────


async def _public_projects(db_session, **kwargs):
    params = {"search": None, "cursor": None, "limit": 50, "db": db_session}
    params.update(kwargs)
    return await list_projects(**params)


@pytest.fixture
def owner(db_session) -> Alumni:
    user = _alumni(str(uuid.uuid4()))
    db_session.add(user)
    db_session.commit()
    return user


@pytest.mark.asyncio
async def test_public_projects_hide_unapproved(db_session, owner):
    db_session.add_all(
        [
            _project(owner.id, "approved", approved=True),
            _project(owner.id, "pending", approved=None),
            _project(owner.id, "declined", approved=False),
        ]
    )
    db_session.commit()

    page = await _public_projects(db_session)

    # The public list must never leak projects awaiting moderation.
    assert [p.id for p in page.items] == ["approved"]


@pytest.mark.asyncio
async def test_public_projects_search_by_title(db_session, owner):
    db_session.add_all(
        [
            _project(owner.id, "p1", title="Alumni Portal"),
            _project(owner.id, "p2", title="Hackathon"),
        ]
    )
    db_session.commit()

    page = await _public_projects(db_session, search="portal")

    assert [p.id for p in page.items] == ["p1"]


@pytest.mark.asyncio
async def test_public_projects_cursor_walks_tied_timestamps_once(db_session, owner):
    same = _now()
    db_session.add_all([_project(owner.id, f"p{i}", created=same) for i in range(5)])
    db_session.commit()

    seen: list[str] = []
    cursor = None
    for _ in range(10):
        page = await _public_projects(db_session, limit=2, cursor=cursor)
        seen.extend(p.id for p in page.items)
        cursor = page.next_cursor
        if cursor is None:
            break

    # Same shape as the admin bug in #162 — this route already had the id
    # tiebreaker, and this pins that it stays.
    assert seen == ["p0", "p1", "p2", "p3", "p4"]
    assert len(seen) == len(set(seen))


@pytest.mark.asyncio
async def test_public_projects_approval_filter_survives_pagination(db_session, owner):
    base = _now()
    db_session.add_all(
        [
            _project(owner.id, "a1", approved=True, created=base),
            _project(owner.id, "x1", approved=None, created=base - timedelta(days=1)),
            _project(owner.id, "a2", approved=True, created=base - timedelta(days=2)),
            _project(owner.id, "a3", approved=True, created=base - timedelta(days=3)),
        ]
    )
    db_session.commit()

    first = await _public_projects(db_session, limit=2)
    second = await _public_projects(db_session, limit=2, cursor=first.next_cursor)

    assert [p.id for p in first.items] == ["a1", "a2"]
    assert [p.id for p in second.items] == ["a3"]
