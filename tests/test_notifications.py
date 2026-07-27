from datetime import datetime, timedelta

from app.models.email_verification import (
    EmailVerification,  # noqa: F401 — registers relationship
)
from app.models.events import Event
from app.models.users import Alumni
from app.services.notifications import (
    ENTRY_BUFFER,
    NOTICE_LEAD_TIME,
    find_nearby_upcoming_events,
    is_read,
    mark_seen,
)


def _alumni(id_, location, **kw):
    return Alumni(
        id=id_,
        email=f"{id_}@innopolis.university",
        first_name="Test",
        last_name="User",
        graduation_year="2025",
        location=location,
        is_verified=True,
        is_banned=False,
        **kw,
    )


def _event(id_, owner_id, location, days_from_now, **kw):
    return Event(
        id=id_,
        owner_id=owner_id,
        participants_ids=kw.pop("participants_ids", [owner_id]),
        title=f"Event {id_}",
        description="desc",
        location=location,
        datetime=datetime.utcnow() + timedelta(days=days_from_now),
        cost=0.0,
        is_online=kw.pop("is_online", False),
        approved=kw.pop("approved", True),
    )


def test_matches_event_in_same_city_within_window(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    nearby = _alumni("nearby", "Russia, Innopolis")
    db_session.add_all([owner, nearby])
    db_session.add(_event("evt1", "owner", "Russia, Innopolis", days_from_now=7))
    db_session.commit()

    matches = find_nearby_upcoming_events(db_session, nearby)

    assert [e.id for e in matches] == ["evt1"]


def test_innopolis_and_kazan_treated_as_same_city(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    kazan_user = _alumni("kazan_user", "Russia, Kazan")
    db_session.add_all([owner, kazan_user])
    db_session.add(_event("evt1", "owner", "Russia, Innopolis", days_from_now=7))
    db_session.commit()

    matches = find_nearby_upcoming_events(db_session, kazan_user)

    assert [e.id for e in matches] == ["evt1"]


def test_different_city_does_not_match(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    far_away = _alumni("far_away", "Germany, Berlin")
    db_session.add_all([owner, far_away])
    db_session.add(_event("evt1", "owner", "Russia, Innopolis", days_from_now=7))
    db_session.commit()

    matches = find_nearby_upcoming_events(db_session, far_away)

    assert matches == []


def test_excludes_owner_and_participants(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    participant = _alumni("participant", "Russia, Innopolis")
    db_session.add_all([owner, participant])
    db_session.add(
        _event(
            "evt1",
            "owner",
            "Russia, Innopolis",
            days_from_now=7,
            participants_ids=["owner", "participant"],
        )
    )
    db_session.commit()

    assert find_nearby_upcoming_events(db_session, owner) == []
    assert find_nearby_upcoming_events(db_session, participant) == []


def test_online_events_match_regardless_of_city(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    far_away = _alumni("far_away", "Germany, Berlin")
    no_location = _alumni("no_location", None)
    db_session.add_all([owner, far_away, no_location])
    db_session.add(
        _event("evt1", "owner", "Russia, Innopolis", days_from_now=7, is_online=True)
    )
    db_session.commit()

    assert [e.id for e in find_nearby_upcoming_events(db_session, far_away)] == ["evt1"]
    assert [e.id for e in find_nearby_upcoming_events(db_session, no_location)] == [
        "evt1"
    ]


def test_online_events_still_exclude_owner_and_participants(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    participant = _alumni("participant", "Germany, Berlin")
    db_session.add_all([owner, participant])
    db_session.add(
        _event(
            "evt1",
            "owner",
            "Russia, Innopolis",
            days_from_now=7,
            is_online=True,
            participants_ids=["owner", "participant"],
        )
    )
    db_session.commit()

    assert find_nearby_upcoming_events(db_session, owner) == []
    assert find_nearby_upcoming_events(db_session, participant) == []


def test_events_within_a_week_match_however_soon(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    nearby = _alumni("nearby", "Russia, Innopolis")
    db_session.add_all([owner, nearby])
    db_session.add(_event("evt_soon", "owner", "Russia, Innopolis", days_from_now=1))
    db_session.commit()

    assert [e.id for e in find_nearby_upcoming_events(db_session, nearby)] == [
        "evt_soon"
    ]


def test_excludes_events_more_than_a_week_out(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    nearby = _alumni("nearby", "Russia, Innopolis")
    db_session.add_all([owner, nearby])
    db_session.add(_event("evt_far", "owner", "Russia, Innopolis", days_from_now=30))
    db_session.commit()

    assert find_nearby_upcoming_events(db_session, nearby) == []


def test_matches_event_just_past_the_exact_seven_day_mark(db_session):
    """Regression: an event 7 days + a few hours out is still "about a
    week away" and must match — the ENTRY_BUFFER exists exactly so a
    match's first appearance doesn't depend on time-of-day."""
    owner = _alumni("owner", "Russia, Innopolis")
    nearby = _alumni("nearby", "Russia, Innopolis")
    db_session.add_all([owner, nearby])
    db_session.add(_event("evt1", "owner", "Russia, Innopolis", days_from_now=7.1))
    db_session.commit()

    assert [e.id for e in find_nearby_upcoming_events(db_session, nearby)] == ["evt1"]


def test_includes_events_that_already_happened(db_session):
    """Once an event enters the window it stays part of the user's
    notification history — it doesn't disappear just because it occurred
    or because real time has since moved past it."""
    owner = _alumni("owner", "Russia, Innopolis")
    nearby = _alumni("nearby", "Russia, Innopolis")
    db_session.add_all([owner, nearby])
    db_session.add(_event("evt_past", "owner", "Russia, Innopolis", days_from_now=-2))
    db_session.commit()

    assert [e.id for e in find_nearby_upcoming_events(db_session, nearby)] == [
        "evt_past"
    ]


def test_excludes_unapproved_events(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    nearby = _alumni("nearby", "Russia, Innopolis")
    db_session.add_all([owner, nearby])
    db_session.add(
        _event("evt1", "owner", "Russia, Innopolis", days_from_now=7, approved=False)
    )
    db_session.commit()

    assert find_nearby_upcoming_events(db_session, nearby) == []


def test_alumni_without_location_never_matched_for_in_person_events(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    no_location = _alumni("no_location", None)
    db_session.add_all([owner, no_location])
    db_session.add(_event("evt1", "owner", "Russia, Innopolis", days_from_now=7))
    db_session.commit()

    assert find_nearby_upcoming_events(db_session, no_location) == []


def test_unread_until_seen_after_event_enters_window(db_session):
    owner = _alumni("owner", "Russia, Innopolis")
    nearby = _alumni("nearby", "Russia, Innopolis")
    db_session.add_all([owner, nearby])
    event = _event("evt1", "owner", "Russia, Innopolis", days_from_now=7)
    db_session.add(event)
    db_session.commit()

    # Never viewed -> unread.
    assert is_read(nearby, event) is False

    # Viewed *before* the event entered the window -> still unread.
    nearby.notifications_seen_at = (
        event.datetime - NOTICE_LEAD_TIME - ENTRY_BUFFER - timedelta(minutes=1)
    )
    assert is_read(nearby, event) is False

    # Viewed *after* the event entered the window -> read.
    mark_seen(db_session, nearby)
    assert is_read(nearby, event) is True


def test_mark_seen_persists(db_session):
    user = _alumni("user1", "Russia, Innopolis")
    db_session.add(user)
    db_session.commit()
    assert user.notifications_seen_at is None

    mark_seen(db_session, user)

    assert user.notifications_seen_at is not None
