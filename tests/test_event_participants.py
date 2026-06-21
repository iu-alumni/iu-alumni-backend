from datetime import datetime

from fastapi import HTTPException
import pytest

from app.api.routes.events.event_add_participant import add_participant
from app.api.routes.events.event_remove_participant import remove_participant
from app.models.events import Event
from app.models.users import Admin, Alumni


class TestEventParticipants:

    @pytest.mark.asyncio
    async def test_add_participant_event_not_found(self, db_session):
        user = Alumni(
            id="user123",
            email="user@innopolis.university",
            first_name="Test",
            last_name="User",
            graduation_year="2025"
        )
        db_session.add(user)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await add_participant(
                event_id="nonexistent_id",
                db=db_session,
                current_user=user
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Event not found"

    @pytest.mark.asyncio
    async def test_add_participant_participant_not_found(self, db_session):
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
            owner_id="owner123",
            location="Room 101",
            datetime=datetime(2025, 1, 1, 10, 0, 0),
            cost=0.0,
            is_online=False,
            participants_ids=[],
            approved=True
        )
        db_session.add(event)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await add_participant(
                event_id="event123",
                participant_id="nonexistent_participant",
                db=db_session,
                current_user=user
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Participant not found"

    @pytest.mark.asyncio
    async def test_add_participant_not_authorized(self, db_session):
        user = Alumni(
            id="user123",
            email="user@innopolis.university",
            first_name="Test",
            last_name="User",
            graduation_year="2025"
        )
        db_session.add(user)

        another_user = Alumni(
            id="another_user_id",
            email="another@innopolis.university",
            first_name="Another",
            last_name="User",
            graduation_year="2025"
        )
        db_session.add(another_user)

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
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await add_participant(
                event_id="event123",
                participant_id="another_user_id",
                db=db_session,
                current_user=user
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "You can only add yourself as a participant"

    @pytest.mark.asyncio
    async def test_add_participant_already_participating(self, db_session):
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
            owner_id="owner123",
            location="Room 101",
            datetime=datetime(2025, 1, 1, 10, 0, 0),
            cost=0.0,
            is_online=False,
            participants_ids=["user123"],
            approved=True
        )
        db_session.add(event)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await add_participant(
                event_id="event123",
                db=db_session,
                current_user=user
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "You are already a participant in this event"

    @pytest.mark.asyncio
    async def test_add_participant_success(self, db_session, mocker):
        mocker.patch(
            "app.api.routes.events.event_add_participant.NotificationService.send_join_notification",
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
            owner_id="owner123",
            location="Room 101",
            datetime=datetime(2025, 1, 1, 10, 0, 0),
            cost=0.0,
            is_online=False,
            participants_ids=[],
            approved=True
        )
        db_session.add(event)
        db_session.commit()

        result = await add_participant(
            event_id="event123",
            db=db_session,
            current_user=user
        )

        assert result["message"] == "Successfully joined the event"

        db_session.refresh(event)
        assert "user123" in event.participants_ids

    @pytest.mark.asyncio
    async def test_add_participant_by_admin(self, db_session, mocker):
        mocker.patch(
            "app.api.routes.events.event_add_participant.NotificationService.send_join_notification",
            return_value=True
        )

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
            owner_id="owner123",
            location="Room 101",
            datetime=datetime(2025, 1, 1, 10, 0, 0),
            cost=0.0,
            is_online=False,
            participants_ids=[],
            approved=True
        )
        db_session.add(event)
        db_session.commit()

        result = await add_participant(
            event_id="event123",
            participant_id="user123",
            db=db_session,
            current_user=admin
        )

        assert result["message"] == "Successfully joined the event"

        db_session.refresh(event)
        assert "user123" in event.participants_ids

    @pytest.mark.asyncio
    async def test_remove_participant_event_not_found(self, db_session):
        user = Alumni(
            id="user123",
            email="user@innopolis.university",
            first_name="Test",
            last_name="User",
            graduation_year="2025"
        )
        db_session.add(user)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await remove_participant(
                event_id="nonexistent_id",
                db=db_session,
                current_user=user
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Event not found"

    @pytest.mark.asyncio
    async def test_remove_participant_not_found(self, db_session):
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
            owner_id="owner123",
            location="Room 101",
            datetime=datetime(2025, 1, 1, 10, 0, 0),
            cost=0.0,
            is_online=False,
            participants_ids=[],
            approved=True
        )
        db_session.add(event)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await remove_participant(
                event_id="event123",
                participant_id="nonexistent_participant",
                db=db_session,
                current_user=user
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Participant not found"

    @pytest.mark.asyncio
    async def test_remove_participant_not_authorized(self, db_session):
        user = Alumni(
            id="user123",
            email="user@innopolis.university",
            first_name="Test",
            last_name="User",
            graduation_year="2025"
        )
        db_session.add(user)

        another_user = Alumni(
            id="another_user_id",
            email="another@innopolis.university",
            first_name="Another",
            last_name="User",
            graduation_year="2025"
        )
        db_session.add(another_user)

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
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await remove_participant(
                event_id="event123",
                participant_id="another_user_id",
                db=db_session,
                current_user=user
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "You can only remove yourself as a participant"

    @pytest.mark.asyncio
    async def test_remove_participant_not_participating(self, db_session):
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
            owner_id="owner123",
            location="Room 101",
            datetime=datetime(2025, 1, 1, 10, 0, 0),
            cost=0.0,
            is_online=False,
            participants_ids=[],
            approved=True
        )
        db_session.add(event)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await remove_participant(
                event_id="event123",
                db=db_session,
                current_user=user
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "You are not a participant in this event"

    @pytest.mark.asyncio
    async def test_remove_participant_success(self, db_session):
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
            owner_id="owner123",
            location="Room 101",
            datetime=datetime(2025, 1, 1, 10, 0, 0),
            cost=0.0,
            is_online=False,
            participants_ids=["user123"],
            approved=True
        )
        db_session.add(event)
        db_session.commit()

        result = await remove_participant(
            event_id="event123",
            db=db_session,
            current_user=user
        )

        assert result["message"] == "Successfully left the event"

        db_session.refresh(event)
        assert "user123" not in event.participants_ids

    @pytest.mark.asyncio
    async def test_remove_participant_by_admin(self, db_session):
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
            owner_id="owner123",
            location="Room 101",
            datetime=datetime(2025, 1, 1, 10, 0, 0),
            cost=0.0,
            is_online=False,
            participants_ids=["user123"],
            approved=True
        )
        db_session.add(event)
        db_session.commit()

        result = await remove_participant(
            event_id="event123",
            participant_id="user123",
            db=db_session,
            current_user=admin
        )

        assert result["message"] == "Successfully left the event"

        db_session.refresh(event)
        assert "user123" not in event.participants_ids
