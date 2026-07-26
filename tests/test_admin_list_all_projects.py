"""Tests for the admin project moderation list.

Ordering is created_at DESC then id ASC, and the cursor carries both. Ties on
created_at are the risk: Project.created_at defaults to server_default=func.now(),
which in Postgres is the *transaction* start time, so projects created together
share a timestamp exactly. A cursor that only compares timestamps skips them.
"""

from datetime import UTC, datetime, timedelta
import uuid

from fastapi import HTTPException
import pytest

from app.api.routes.admin.list_all_projects import admin_list_projects
from app.models.projects import Project
from app.models.users import Admin, Alumni


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _admin() -> Admin:
    return Admin(id="admin-1", email="admin@innopolis.university")


def _alumni() -> Alumni:
    return Alumni(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4().hex[:8]}@innopolis.university",
        hashed_password="hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
    )


def _project(
    owner_id: str,
    project_id: str,
    *,
    title: str = "Project",
    approved: bool | None = None,
    created=None,
) -> Project:
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


async def _call(db_session, **kwargs):
    params = {
        "status_filter": "all",
        "search": None,
        "cursor": None,
        "limit": 50,
        "db": db_session,
        "current_user": _admin(),
    }
    params.update(kwargs)
    return await admin_list_projects(**params)


def _ids(page) -> list[str]:
    return [p.id for p in page.items]


@pytest.fixture
def owner(db_session) -> Alumni:
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    return user


# ── authorization / validation ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_non_admin_is_rejected(db_session):
    with pytest.raises(HTTPException) as exc:
        await _call(db_session, current_user=_alumni())

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_unknown_status_filter_is_rejected(db_session):
    with pytest.raises(HTTPException) as exc:
        await _call(db_session, status_filter="bogus")

    assert exc.value.status_code == 422


# ── status filters ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_status_filters_select_the_right_projects(db_session, owner):
    db_session.add_all(
        [
            _project(owner.id, "pending", approved=None),
            _project(owner.id, "approved", approved=True),
            _project(owner.id, "declined", approved=False),
        ]
    )
    db_session.commit()

    assert _ids(await _call(db_session, status_filter="pending")) == ["pending"]
    assert _ids(await _call(db_session, status_filter="approved")) == ["approved"]
    assert _ids(await _call(db_session, status_filter="declined")) == ["declined"]
    assert sorted(_ids(await _call(db_session, status_filter="all"))) == [
        "approved",
        "declined",
        "pending",
    ]


@pytest.mark.asyncio
async def test_search_matches_title_case_insensitively(db_session, owner):
    db_session.add_all(
        [
            _project(owner.id, "p1", title="Alumni Portal"),
            _project(owner.id, "p2", title="Hackathon"),
        ]
    )
    db_session.commit()

    assert _ids(await _call(db_session, search="portal")) == ["p1"]


# ── ordering ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_projects_are_returned_newest_first(db_session, owner):
    base = _now()
    db_session.add_all(
        [
            _project(owner.id, "old", created=base - timedelta(days=2)),
            _project(owner.id, "new", created=base),
            _project(owner.id, "mid", created=base - timedelta(days=1)),
        ]
    )
    db_session.commit()

    assert _ids(await _call(db_session)) == ["new", "mid", "old"]


# ── pagination ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_short_page_has_no_cursor(db_session, owner):
    db_session.add(_project(owner.id, "p1"))
    db_session.commit()

    page = await _call(db_session, limit=50)

    assert len(page.items) == 1
    assert page.next_cursor is None


@pytest.mark.asyncio
async def test_cursor_walks_distinct_timestamps_exactly_once(db_session, owner):
    base = _now()
    db_session.add_all(
        [_project(owner.id, f"p{i}", created=base - timedelta(days=i)) for i in range(5)]
    )
    db_session.commit()

    seen: list[str] = []
    cursor = None
    for _ in range(10):  # bounded so a broken cursor cannot loop forever
        page = await _call(db_session, limit=2, cursor=cursor)
        seen.extend(_ids(page))
        cursor = page.next_cursor
        if cursor is None:
            break

    assert seen == [f"p{i}" for i in range(5)]


@pytest.mark.asyncio
async def test_cursor_walks_tied_timestamps_exactly_once(db_session, owner):
    same = _now()
    db_session.add_all([_project(owner.id, f"p{i}", created=same) for i in range(5)])
    db_session.commit()

    seen: list[str] = []
    cursor = None
    for _ in range(10):
        page = await _call(db_session, limit=2, cursor=cursor)
        seen.extend(_ids(page))
        cursor = page.next_cursor
        if cursor is None:
            break

    # Projects created in one transaction share created_at exactly, so paging
    # here depends entirely on the id half of the cursor. Comparing timestamps
    # alone drops every project that ties with the page boundary.
    assert seen == ["p0", "p1", "p2", "p3", "p4"]
    assert len(seen) == len(set(seen))


@pytest.mark.asyncio
async def test_status_filter_is_preserved_across_pages(db_session, owner):
    base = _now()
    db_session.add_all(
        [
            _project(owner.id, "a1", approved=None, created=base),
            _project(owner.id, "b1", approved=True, created=base - timedelta(days=1)),
            _project(owner.id, "a2", approved=None, created=base - timedelta(days=2)),
            _project(owner.id, "a3", approved=None, created=base - timedelta(days=3)),
        ]
    )
    db_session.commit()

    first = await _call(db_session, status_filter="pending", limit=2)
    second = await _call(
        db_session, status_filter="pending", limit=2, cursor=first.next_cursor
    )

    assert _ids(first) == ["a1", "a2"]
    assert _ids(second) == ["a3"]
