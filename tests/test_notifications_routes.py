from datetime import datetime, timedelta

from app.api.routes.notifications.list_notifications import list_notifications
from app.api.routes.notifications.unread_count import get_unread_count
from app.models.email_verification import (
    EmailVerification,  # noqa: F401 — registers relationship
)
from app.models.events import Event
from app.models.users import Alumni


def _seed_matching_event(db_session):
    owner = Alumni(
        id="owner",
        email="owner@innopolis.university",
        first_name="Owner",
        last_name="User",
        graduation_year="2020",
        location="Russia, Innopolis",
        is_verified=True,
        is_banned=False,
    )
    user = Alumni(
        id="user1",
        email="user1@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025",
        location="Russia, Innopolis",
        is_verified=True,
        is_banned=False,
    )
    event = Event(
        id="evt1",
        owner_id="owner",
        participants_ids=["owner"],
        title="Reunion",
        description="desc",
        location="Russia, Innopolis",
        datetime=datetime.utcnow() + timedelta(days=7),
        cost=0.0,
        is_online=False,
        approved=True,
    )
    db_session.add_all([owner, user, event])
    db_session.commit()
    return user


def test_unread_count_reflects_a_matching_event(db_session):
    user = _seed_matching_event(db_session)

    result = get_unread_count(db=db_session, current_user=user)

    assert result.count == 1


def test_unread_count_does_not_mark_as_read(db_session):
    user = _seed_matching_event(db_session)

    get_unread_count(db=db_session, current_user=user)

    assert user.notifications_seen_at is None


def test_list_notifications_shows_unread_on_first_view(db_session):
    user = _seed_matching_event(db_session)

    result = list_notifications(db=db_session, current_user=user)

    assert len(result.items) == 1
    item = result.items[0]
    assert item.read is False
    assert item.title == "Reunion"
    assert item.location == "Russia, Innopolis"


def test_list_notifications_marks_seen_as_a_side_effect(db_session):
    user = _seed_matching_event(db_session)

    list_notifications(db=db_session, current_user=user)

    assert user.notifications_seen_at is not None


def test_second_view_shows_notification_as_already_read(db_session):
    user = _seed_matching_event(db_session)

    list_notifications(db=db_session, current_user=user)
    second_result = list_notifications(db=db_session, current_user=user)

    assert second_result.items[0].read is True


def test_unread_count_drops_to_zero_after_viewing_list(db_session):
    user = _seed_matching_event(db_session)

    list_notifications(db=db_session, current_user=user)
    result = get_unread_count(db=db_session, current_user=user)

    assert result.count == 0


def test_event_entering_window_after_last_view_shows_as_unread(db_session):
    """A currently-matching event's "entered the window" moment
    (datetime - 7 days) is fixed by its own datetime. So whether it's read
    depends on whether the user's cursor falls before or after that fixed
    point — this pins both sides of that comparison directly, rather than
    relying on real time passing between two calls (which wouldn't move
    either event's fixed "entered the window" moment)."""
    owner = Alumni(
        id="owner",
        email="owner@innopolis.university",
        first_name="Owner",
        last_name="User",
        graduation_year="2020",
        location="Russia, Innopolis",
        is_verified=True,
        is_banned=False,
    )
    user = Alumni(
        id="user1",
        email="user1@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025",
        location="Russia, Innopolis",
        is_verified=True,
        is_banned=False,
    )
    db_session.add_all([owner, user])

    now = datetime.utcnow()
    # window_entry_time = datetime - 7d - 12h (NOTICE_LEAD_TIME + ENTRY_BUFFER), so:
    already_seen = Event(
        id="evt_seen",
        owner_id="owner",
        participants_ids=["owner"],
        title="Already Seen",
        description="desc",
        location="Russia, Innopolis",
        datetime=now + timedelta(days=7, hours=-12),  # enters window at now-24h
        cost=0.0,
        is_online=False,
        approved=True,
    )
    brand_new = Event(
        id="evt_new",
        owner_id="owner",
        participants_ids=["owner"],
        title="Brand New",
        description="desc",
        location="Russia, Innopolis",
        datetime=now + timedelta(days=7, hours=6),  # enters window at now-6h
        cost=0.0,
        is_online=False,
        approved=True,
    )
    db_session.add_all([already_seen, brand_new])
    # Cursor sits between the two events' "entered the window" moments.
    user.notifications_seen_at = now - timedelta(hours=15)
    db_session.commit()

    result = list_notifications(db=db_session, current_user=user)
    by_title = {item.title: item.read for item in result.items}

    assert by_title["Already Seen"] is True
    assert by_title["Brand New"] is False
