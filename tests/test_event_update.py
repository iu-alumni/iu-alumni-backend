from datetime import datetime

from fastapi import HTTPException
import pytest

from app.api.routes.events.update_event import update_event
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.schemas.event import UpdateEventRequest


@pytest.mark.asyncio
async def test_update_event_not_found(db_session):
    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)
    db_session.commit()

    request = UpdateEventRequest(title="New Title")

    with pytest.raises(HTTPException) as exc_info:
        await update_event(
            event_id="nonexistent_id",
            event_data=request,
            db=db_session,
            current_user=user
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Event not found"


@pytest.mark.asyncio
async def test_update_event_not_owner(db_session):
    owner = Alumni(
        id="owner123",
        email="owner@innopolis.university",
        first_name="Owner",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(owner)

    event = Event(
        id="event123",
        title="Test Event",
        description="Description",
        owner_id="owner123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event)

    other_user = Alumni(
        id="user123",
        email="other@innopolis.university",
        first_name="Other",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(other_user)
    db_session.commit()

    request = UpdateEventRequest(title="New Title")

    with pytest.raises(HTTPException) as exc_info:
        await update_event(
            event_id="event123",
            event_data=request,
            db=db_session,
            current_user=other_user
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You don't have permission to update this event"


@pytest.mark.asyncio
async def test_update_event_title(db_session):
    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    event = Event(
        id="event123",
        title="Test Event",
        description="Description",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event)
    db_session.commit()

    request = UpdateEventRequest(title="New Title")

    result = await update_event(
        event_id="event123",
        event_data=request,
        db=db_session,
        current_user=user
    )

    assert result.title == "New Title"


@pytest.mark.asyncio
async def test_update_event_location(db_session, mocker):
    mocker.patch(
        "app.api.routes.events.update_event.NotificationService.send_custom_notification",
        return_value=True
    )

    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    event = Event(
        id="event123",
        title="Test Event",
        description="Description",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event)
    db_session.commit()

    request = UpdateEventRequest(location="Room 202")

    result = await update_event(
        event_id="event123",
        event_data=request,
        db=db_session,
        current_user=user
    )

    assert result.location == "Room 202"


@pytest.mark.asyncio
async def test_update_event_datetime(db_session, mocker):
    mocker.patch(
        "app.api.routes.events.update_event.NotificationService.send_custom_notification",
        return_value=True
    )

    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    event = Event(
        id="event123",
        title="Test Event",
        description="Description",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event)
    db_session.commit()

    new_datetime = datetime(2025, 2, 1, 14, 0, 0)
    request = UpdateEventRequest(datetime=new_datetime)

    result = await update_event(
        event_id="event123",
        event_data=request,
        db=db_session,
        current_user=user
    )

    assert result.datetime == new_datetime


@pytest.mark.asyncio
async def test_update_event_cost(db_session, mocker):
    mocker.patch(
        "app.api.routes.events.update_event.NotificationService.send_custom_notification",
        return_value=True
    )

    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    event = Event(
        id="event123",
        title="Test Event",
        description="Description",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event)
    db_session.commit()

    request = UpdateEventRequest(cost=50.0)

    result = await update_event(
        event_id="event123",
        event_data=request,
        db=db_session,
        current_user=user
    )

    assert result.cost == 50.0


@pytest.mark.asyncio
async def test_update_event_is_online(db_session, mocker):
    mocker.patch(
        "app.api.routes.events.update_event.NotificationService.send_custom_notification",
        return_value=True
    )

    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    event = Event(
        id="event123",
        title="Test Event",
        description="Description",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event)
    db_session.commit()

    request = UpdateEventRequest(is_online=True)

    result = await update_event(
        event_id="event123",
        event_data=request,
        db=db_session,
        current_user=user
    )

    assert result.is_online is True


@pytest.mark.asyncio
async def test_update_event_cover(db_session):
    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    event = Event(
        id="event123",
        title="Test Event",
        description="Description",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event)
    db_session.commit()

    request = UpdateEventRequest(cover="https://example.com/image.jpg")

    result = await update_event(
        event_id="event123",
        event_data=request,
        db=db_session,
        current_user=user
    )

    assert result.cover == "https://example.com/image.jpg"


@pytest.mark.asyncio
async def test_update_event_admin_success(db_session):
    admin = Admin(
        id="admin123",
        email="admin@innopolis.university"
    )
    db_session.add(admin)

    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    event = Event(
        id="event123",
        title="Test Event",
        description="Description",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event)
    db_session.commit()

    request = UpdateEventRequest(title="Admin Updated Title")

    result = await update_event(
        event_id="event123",
        event_data=request,
        db=db_session,
        current_user=admin
    )

    assert result.title == "Admin Updated Title"


@pytest.mark.asyncio
async def test_update_event_no_changes(db_session):
    user = Alumni(
        id="user123",
        email="user@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    db_session.add(user)

    event = Event(
        id="event123",
        title="Test Event",
        description="Description",
        owner_id="user123",
        location="Room 101",
        datetime=datetime(2025, 1, 1, 10, 0, 0),
        cost=0.0,
        is_online=False,
        participants_ids=[],
        approved=True
    )
    db_session.add(event)
    db_session.commit()

    request = UpdateEventRequest()

    result = await update_event(
        event_id="event123",
        event_data=request,
        db=db_session,
        current_user=user
    )

    assert result.title == "Test Event"
    assert result.location == "Room 101"
