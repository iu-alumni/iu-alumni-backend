"""Tests for the admin user directory.

Covers the admin-only gate, the search/filter predicates, and cursor pagination
— the part most likely to silently drop or repeat a user, since the cursor is
derived from the page contents rather than the requested offset.
"""

from fastapi import HTTPException
import pytest

from app.api.routes.admin.list_users import list_users
from app.models.users import Admin, Alumni


def _admin() -> Admin:
    return Admin(id="admin-1", email="admin@innopolis.university")


def _alumni(
    user_id: str,
    *,
    first_name: str = "Ada",
    last_name: str = "Lovelace",
    email: str | None = None,
    is_banned: bool = False,
    is_verified: bool = True,
) -> Alumni:
    return Alumni(
        id=user_id,
        email=email or f"{user_id}@innopolis.university",
        hashed_password="hash",
        first_name=first_name,
        last_name=last_name,
        graduation_year="2024",
        is_banned=is_banned,
        is_verified=is_verified,
    )


def _seed(db_session, users: list[Alumni]) -> None:
    db_session.add_all(users)
    db_session.commit()


def _call(db_session, **kwargs):
    params = {
        "search": None,
        "banned": None,
        "verified": None,
        "cursor": None,
        "limit": 50,
        "db": db_session,
        "current_user": _admin(),
    }
    params.update(kwargs)
    return list_users(**params)


def _ids(page) -> list[str]:
    return [u.id for u in page.items]


# ── authorization ────────────────────────────────────────────────────────────


def test_non_admin_cannot_list_users(db_session):
    with pytest.raises(HTTPException) as exc:
        _call(db_session, current_user=_alumni("user-1"))

    assert exc.value.status_code == 403


# ── search ───────────────────────────────────────────────────────────────────


def test_search_matches_first_name_case_insensitively(db_session):
    _seed(
        db_session,
        [
            _alumni("user-1", first_name="Ada"),
            _alumni("user-2", first_name="Grace"),
        ],
    )

    assert _ids(_call(db_session, search="ada")) == ["user-1"]


def test_search_matches_last_name(db_session):
    _seed(
        db_session,
        [
            _alumni("user-1", last_name="Lovelace"),
            _alumni("user-2", last_name="Hopper"),
        ],
    )

    assert _ids(_call(db_session, search="hopp")) == ["user-2"]


def test_search_matches_email(db_session):
    _seed(
        db_session,
        [
            _alumni("user-1", email="ada@innopolis.university"),
            _alumni("user-2", email="grace@innopolis.university"),
        ],
    )

    assert _ids(_call(db_session, search="grace@")) == ["user-2"]


def test_search_with_no_match_returns_empty_page(db_session):
    _seed(db_session, [_alumni("user-1")])

    page = _call(db_session, search="nobody")

    assert page.items == []
    assert page.next_cursor is None


# ── filters ──────────────────────────────────────────────────────────────────


def test_banned_filter_selects_both_ways(db_session):
    _seed(
        db_session,
        [
            _alumni("user-1", is_banned=True),
            _alumni("user-2", is_banned=False),
        ],
    )

    assert _ids(_call(db_session, banned=True)) == ["user-1"]
    assert _ids(_call(db_session, banned=False)) == ["user-2"]


def test_verified_filter_selects_both_ways(db_session):
    _seed(
        db_session,
        [
            _alumni("user-1", is_verified=True),
            _alumni("user-2", is_verified=False),
        ],
    )

    assert _ids(_call(db_session, verified=True)) == ["user-1"]
    assert _ids(_call(db_session, verified=False)) == ["user-2"]


def test_filters_combine(db_session):
    _seed(
        db_session,
        [
            _alumni("user-1", first_name="Ada", is_banned=True, is_verified=False),
            _alumni("user-2", first_name="Ada", is_banned=False, is_verified=False),
            _alumni("user-3", first_name="Grace", is_banned=True, is_verified=False),
        ],
    )

    page = _call(db_session, search="ada", banned=True, verified=False)

    assert _ids(page) == ["user-1"]


def test_no_filters_returns_everyone(db_session):
    _seed(db_session, [_alumni(f"user-{i}") for i in range(1, 4)])

    page = _call(db_session)

    assert len(page.items) == 3
    assert page.next_cursor is None


# ── pagination ───────────────────────────────────────────────────────────────


def test_page_smaller_than_limit_has_no_cursor(db_session):
    _seed(db_session, [_alumni("user-1"), _alumni("user-2")])

    page = _call(db_session, limit=50)

    assert len(page.items) == 2
    assert page.next_cursor is None


def test_full_page_with_more_rows_returns_a_cursor(db_session):
    _seed(db_session, [_alumni(f"user-{i}") for i in range(1, 6)])

    page = _call(db_session, limit=2)

    assert _ids(page) == ["user-1", "user-2"]
    assert page.next_cursor is not None


def test_cursor_walks_every_user_exactly_once(db_session):
    _seed(db_session, [_alumni(f"user-{i}") for i in range(1, 6)])

    seen: list[str] = []
    cursor = None
    for _ in range(10):  # bounded so a broken cursor cannot loop forever
        page = _call(db_session, limit=2, cursor=cursor)
        seen.extend(_ids(page))
        cursor = page.next_cursor
        if cursor is None:
            break

    # The cursor is derived from the page contents, so an off-by-one here would
    # skip a user or serve one twice.
    assert seen == [f"user-{i}" for i in range(1, 6)]
    assert len(seen) == len(set(seen))


def test_exact_multiple_of_limit_terminates(db_session):
    _seed(db_session, [_alumni(f"user-{i}") for i in range(1, 5)])

    seen: list[str] = []
    cursor = None
    for _ in range(10):
        page = _call(db_session, limit=2, cursor=cursor)
        seen.extend(_ids(page))
        cursor = page.next_cursor
        if cursor is None:
            break

    # 4 users at limit=2 is the boundary case where the "is there more?" probe
    # matters most — it must not hand back an endless trailing cursor.
    assert seen == ["user-1", "user-2", "user-3", "user-4"]


def test_filters_are_preserved_across_pages(db_session):
    _seed(
        db_session,
        [
            _alumni("user-1", is_banned=True),
            _alumni("user-2", is_banned=False),
            _alumni("user-3", is_banned=True),
            _alumni("user-4", is_banned=True),
        ],
    )

    first = _call(db_session, banned=True, limit=2)
    second = _call(db_session, banned=True, limit=2, cursor=first.next_cursor)

    # A cursor must not smuggle filtered-out users back into later pages.
    assert _ids(first) == ["user-1", "user-3"]
    assert _ids(second) == ["user-4"]
