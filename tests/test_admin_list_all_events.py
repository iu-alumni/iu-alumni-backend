"""Tests for the admin event list.

The interesting part is the composite keyset cursor: results are ordered by
datetime DESC then id ASC, and the cursor encodes both. Ties on datetime are
where composite cursors usually break — either skipping events or serving them
twice — so the walk is asserted over a set with deliberate ties.
"""

from datetime import UTC, datetime, timedelta
import uuid

from fastapi import HTTPException
import pytest

from app.api.routes.admin.list_all_events import list_events
from app.models.events import Event
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


def _event(owner_id: str, event_id: str, *, title: str = "Meetup", when=None) -> Event:
    return Event(
        id=event_id,
        owner_id=owner_id,
        participants_ids=[],
        title=title,
        description="A meetup",
        location="Innopolis",
        datetime=when or _now(),
        cost=0.0,
        is_online=False,
        cover=None,
        approved=True,
    )


async def _call(db_session, **kwargs):
    params = {
        "search": None,
        "cursor": None,
        "limit": 50,
        "db": db_session,
        "current_user": _admin(),
    }
    params.update(kwargs)
    return await list_events(**params)


def _ids(page) -> list[str]:
    return [e.id for e in page.items]


@pytest.fixture
def owner(db_session) -> Alumni:
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    return user


# ── authorization ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_non_admin_cannot_list_events(db_session):
    with pytest.raises(HTTPException) as exc:
        await _call(db_session, current_user=_alumni())

    assert exc.value.status_code == 403


# ── search ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_matches_title_case_insensitively(db_session, owner):
    db_session.add_all(
        [
            _event(owner.id, "e1", title="Alumni Meetup"),
            _event(owner.id, "e2", title="Hackathon"),
        ]
    )
    db_session.commit()

    assert _ids(await _call(db_session, search="meetup")) == ["e1"]


@pytest.mark.asyncio
async def test_search_with_no_match_returns_empty_page(db_session, owner):
    db_session.add(_event(owner.id, "e1", title="Hackathon"))
    db_session.commit()

    page = await _call(db_session, search="nothing")

    assert page.items == []
    assert page.next_cursor is None


# ── ordering ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_events_are_returned_newest_first(db_session, owner):
    base = _now()
    db_session.add_all(
        [
            _event(owner.id, "old", when=base - timedelta(days=2)),
            _event(owner.id, "new", when=base),
            _event(owner.id, "mid", when=base - timedelta(days=1)),
        ]
    )
    db_session.commit()

    assert _ids(await _call(db_session)) == ["new", "mid", "old"]


@pytest.mark.asyncio
async def test_ties_on_datetime_break_by_id_ascending(db_session, owner):
    same = _now()
    db_session.add_all(
        [
            _event(owner.id, "e2", when=same),
            _event(owner.id, "e1", when=same),
        ]
    )
    db_session.commit()

    # A stable tiebreaker is what makes the keyset cursor safe.
    assert _ids(await _call(db_session)) == ["e1", "e2"]


# ── pagination ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_short_page_has_no_cursor(db_session, owner):
    db_session.add(_event(owner.id, "e1"))
    db_session.commit()

    page = await _call(db_session, limit=50)

    assert len(page.items) == 1
    assert page.next_cursor is None


@pytest.mark.asyncio
async def test_full_page_with_more_rows_returns_a_cursor(db_session, owner):
    base = _now()
    db_session.add_all(
        [_event(owner.id, f"e{i}", when=base - timedelta(days=i)) for i in range(5)]
    )
    db_session.commit()

    page = await _call(db_session, limit=2)

    assert _ids(page) == ["e0", "e1"]
    assert page.next_cursor is not None


@pytest.mark.asyncio
async def test_cursor_walks_distinct_datetimes_exactly_once(db_session, owner):
    base = _now()
    db_session.add_all(
        [_event(owner.id, f"e{i}", when=base - timedelta(days=i)) for i in range(5)]
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

    assert seen == [f"e{i}" for i in range(5)]
    assert len(seen) == len(set(seen))


@pytest.mark.asyncio
async def test_cursor_walks_across_datetime_ties_exactly_once(db_session, owner):
    same = _now()
    db_session.add_all([_event(owner.id, f"e{i}", when=same) for i in range(5)])
    db_session.commit()

    seen: list[str] = []
    cursor = None
    for _ in range(10):
        page = await _call(db_session, limit=2, cursor=cursor)
        seen.extend(_ids(page))
        cursor = page.next_cursor
        if cursor is None:
            break

    # All five share a datetime, so paging relies entirely on the id half of the
    # composite cursor. This is the case that silently drops or repeats rows.
    assert seen == ["e0", "e1", "e2", "e3", "e4"]
    assert len(seen) == len(set(seen))


@pytest.mark.asyncio
async def test_search_is_preserved_across_pages(db_session, owner):
    base = _now()
    db_session.add_all(
        [
            _event(owner.id, "m1", title="Meetup one", when=base),
            _event(owner.id, "h1", title="Hackathon", when=base - timedelta(days=1)),
            _event(owner.id, "m2", title="Meetup two", when=base - timedelta(days=2)),
            _event(owner.id, "m3", title="Meetup three", when=base - timedelta(days=3)),
        ]
    )
    db_session.commit()

    first = await _call(db_session, search="meetup", limit=2)
    second = await _call(db_session, search="meetup", limit=2, cursor=first.next_cursor)

    # A cursor must not smuggle non-matching events into a later page.
    assert _ids(first) == ["m1", "m2"]
    assert _ids(second) == ["m3"]
