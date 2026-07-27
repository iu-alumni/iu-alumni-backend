"""Finds "upcoming event near you" matches for a user, computed live.

An in-person event is "near" a user if it happens in the same city as the
user's profile location, with Innopolis and Kazan treated as one city
(alumni in one routinely attend events in the other, and they're a short
commute apart). Online events are near everyone, regardless of location.

Unlike a materialized per-(user, event) notification table, read/unread
state here is tracked with a single per-user cursor
(Alumni.notifications_seen_at). An event counts as "unread" until the user
has viewed the notifications list at least once *after* the event entered
the ~7-day window — computed purely from the event's own datetime, so no
extra table or scheduled job is needed.

This is a persistent history, not a transient popup: once an event enters
the window (becomes <= 7 days + ENTRY_BUFFER away), it stays part of the
result forever — including after the event has actually happened. There's
no time-based upper cutoff that removes old matches; the response is
bounded only by MAX_ITEMS in the list endpoint. This does mean the
underlying query scans every approved event that has ever entered the
window, growing over the app's lifetime — acceptable at this data scale,
but worth knowing if event volume grows much larger.

ENTRY_BUFFER exists only so an event's first appearance isn't sensitive to
time-of-day: without it, an event scheduled for exactly "7 days and a few
hours from now" wouldn't show up until real time closed that few-hour gap,
even though it's clearly "about a week away." It only affects *when an
event first appears* — it has no bearing on whether older matches keep
showing, which they always do regardless of this buffer.

Trade-off: because "entered the window" is derived from event.datetime
rather than a real creation/approval timestamp, an event approved very
late (already <= 7 days away) could show as already-read if the user
happened to view the list recently for an unrelated reason. This is rare
in practice — events are normally approved well before the 7-day mark —
and is the accepted cost of not needing a table or background job.

Public entry points:
    find_nearby_upcoming_events(db, alumni) -> list[Event]
    is_read(alumni, event) -> bool
    mark_seen(db, alumni) -> None
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.events import Event
from app.models.users import Alumni


# Cities treated as interchangeable for "near me" matching.
_CITY_ALIASES: dict[str, str] = {
    "kazan": "innopolis",
}

NOTICE_LEAD_TIME = timedelta(days=7)
ENTRY_BUFFER = timedelta(hours=12)


def _city_bucket(location: str | None) -> str | None:
    """Extract and normalize the city part of a "Country, City" string."""
    if not location:
        return None
    parts = [p.strip() for p in location.split(",") if p.strip()]
    if not parts:
        return None
    city = parts[-1].lower()
    return _CITY_ALIASES.get(city, city)


def _window_entry_time(event: Event) -> datetime:
    """The moment this event started being "upcoming" (~7 days out)."""
    return event.datetime - NOTICE_LEAD_TIME - ENTRY_BUFFER


def find_nearby_upcoming_events(
    db: Session, alumni: Alumni, now: datetime | None = None
) -> list[Event]:
    """Approved events near `alumni`, most recently-relevant first.

    Covers a ~7 day window. Includes events that have already happened —
    a match doesn't disappear just because time passed or the event
    occurred; see the module docstring.

    Excludes the event's own owner/participants (they already know about
    it). Online events match regardless of the alumnus's profile city;
    in-person events only match alumni in the same city.
    """
    now = now or datetime.utcnow()

    events = (
        db.query(Event)
        .filter(
            Event.approved == True,
            Event.datetime <= now + NOTICE_LEAD_TIME + ENTRY_BUFFER,
        )
        .order_by(Event.datetime.desc())
        .all()
    )

    my_bucket = _city_bucket(alumni.location)
    matches = []
    for event in events:
        if alumni.id == event.owner_id or alumni.id in (event.participants_ids or []):
            continue
        if event.is_online or (my_bucket and _city_bucket(event.location) == my_bucket):
            matches.append(event)
    return matches


def is_read(alumni: Alumni, event: Event) -> bool:
    """Whether `alumni` has viewed the list since this event became relevant.

    "Relevant" means the point the event entered the ~7-day window.
    """
    seen_at = alumni.notifications_seen_at
    return seen_at is not None and seen_at >= _window_entry_time(event)


def mark_seen(db: Session, alumni: Alumni, now: datetime | None = None) -> None:
    """Advances the read cursor — call after listing notifications."""
    alumni.notifications_seen_at = now or datetime.utcnow()
    db.commit()
