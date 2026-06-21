from datetime import datetime

import pytest

from app.api.routes.events.list_events import list_events
from app.models.events import Event
from app.models.users import Alumni


@pytest.mark.asyncio
async def test_list_events_empty(db_session):
    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)
    db_session.commit()

    result = await list_events(
        db=db_session,
        current_user=user,
        search=None,
        cursor=None,
        limit=50
    )

    assert len(result.items) == 0
    assert result.next_cursor is None


@pytest.mark.asyncio
async def test_list_events_only_approved(db_session):
    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    approved_event = Event(
        id="event1",
        title="Approved Event",
        description="Description",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(approved_event)

    not_approved_event = Event(
        id="event2",
        title="Not Approved Event",
        description="Description",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 2, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=False
    )
    db_session.add(not_approved_event)
    db_session.commit()

    result = await list_events(
        db=db_session,
        current_user=user,
        search=None,
        cursor=None,
        limit=50
    )

    assert len(result.items) == 1
    assert result.items[0].id == "event1"
    assert result.items[0].title == "Approved Event"


@pytest.mark.asyncio
async def test_list_events_search(db_session):
    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    event1 = Event(
        id="event1",
        title="Python Workshop",
        description="Learn Python",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event1)

    event2 = Event(
        id="event2",
        title="JavaScript Workshop",
        description="Learn JS",
        owner_id="user123",
        location="Room 102",
        datetime=datetime(2025, 1, 2, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event2)
    db_session.commit()

    result = await list_events(
        db=db_session,
        current_user=user,
        search="Python",
        cursor=None,
        limit=50
    )

    assert len(result.items) == 1
    assert result.items[0].id == "event1"
    assert result.items[0].title == "Python Workshop"


@pytest.mark.asyncio
async def test_list_events_pagination(db_session):
    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    for i in range(5):
        event = Event(
            id=f"event{i}",
            title=f"Event {i}",
            description=f"Description {i}",
            owner_id="user123",
            location=f"Room {i}",
            datetime=datetime(2025, 1, i + 1, 10, 0, 0),
            cost=0.0,
            is_online=False,
            participants_ids=[],
            approved=True
        )
        db_session.add(event)
    db_session.commit()

    result = await list_events(
        db=db_session,
        current_user=user,
        search=None,
        cursor=None,
        limit=2
    )

    assert len(result.items) == 2
    assert result.next_cursor is not None

    result2 = await list_events(
        db=db_session,
        current_user=user,
        search=None,
        cursor=result.next_cursor,
        limit=2
    )

    assert len(result2.items) == 2
    assert result2.next_cursor is not None
