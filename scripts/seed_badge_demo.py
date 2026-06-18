"""Seed enough activity so the existing user earns several more badges.

Idempotent: safe to re-run. Skips anything already in place.

Triggers covered:
    - Networker: user attends 5+ events
    - Cross-city commuter: user attends an event outside Innopolis
    - Founding Host: user creates the first approved event in 3 new cities
    - Host with the most: 3 distinct cities hosted -> earned
    - Rainmaker: user hosts an event with 20+ attendees
    - Badge Collector: chains in if total earned crosses 10

Run with:
    docker exec iu_alumni_backend python -m scripts.seed_badge_demo
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.email_verification import EmailVerification  # noqa: F401 — registers relationship
from app.models.events import Event
from app.models.users import Alumni

USER_EMAIL = "r.mohammed@innopolis.university"


def _ensure_alumni(db, idx: int) -> Alumni:
    email = f"demo-attendee-{idx}@iu-alumni.local"
    existing = db.query(Alumni).filter(Alumni.email == email).first()
    if existing is not None:
        return existing
    alumni = Alumni(
        id=f"demo-attendee-{idx}",
        email=email,
        hashed_password="$2b$12$placeholder.no.login.allowed.demo.account.hash",
        first_name=f"Demo{idx}",
        last_name="Attendee",
        graduation_year="2020",
        location="Innopolis",
        is_verified=True,
        is_banned=False,
    )
    db.add(alumni)
    db.flush()
    return alumni


def _ensure_event(
    db,
    code: str,
    owner_id: str,
    title: str,
    location: str,
    days_ago: int,
    participants_ids: list[str],
    approved: bool = True,
) -> Event:
    existing = db.query(Event).filter(Event.id == code).first()
    if existing is not None:
        # Update key fields so re-runs reflect changes.
        existing.participants_ids = participants_ids
        existing.approved = approved
        return existing
    event = Event(
        id=code,
        owner_id=owner_id,
        title=title,
        description=f"Demo event for badge testing — {title}",
        location=location,
        datetime=datetime.utcnow() - timedelta(days=days_ago),
        cost=0.0,
        is_online=False,
        cover=None,
        approved=approved,
        participants_ids=participants_ids,
    )
    db.add(event)
    db.flush()
    return event


def main() -> None:
    db = SessionLocal()
    try:
        user = db.query(Alumni).filter(Alumni.email == USER_EMAIL).first()
        if user is None:
            raise SystemExit(f"User {USER_EMAIL} not found")
        print(f"seeding for user {user.id}")

        # Ensure 22 attendee alumni so Rainmaker can pull 20 of them + extras.
        attendees = [_ensure_alumni(db, i) for i in range(22)]
        attendee_ids = [a.id for a in attendees]

        # 5 events the user attends in different cities (Networker + Cross-city commuter).
        attended_cities = [
            ("demo-evt-1", "Innopolis Tech Meetup", "Innopolis", 60),
            ("demo-evt-2", "Dubai Networking Night", "Dubai", 45),
            ("demo-evt-3", "Moscow Reunion", "Moscow", 30),
            ("demo-evt-4", "Berlin Alumni Coffee", "Berlin", 20),
            ("demo-evt-5", "Kazan Hackathon", "Kazan", 10),
        ]
        for code, title, city, days_ago in attended_cities:
            _ensure_event(
                db,
                code=code,
                owner_id=attendees[0].id,
                title=title,
                location=city,
                days_ago=days_ago,
                participants_ids=[user.id, attendees[1].id, attendees[2].id],
                approved=True,
            )

        # 3 events the USER hosts in different cities (Founding Host x3, Host with the most).
        hosted_cities = [
            ("demo-host-1", "User's Tashkent Talk", "Tashkent", 50),
            ("demo-host-2", "User's Almaty Drinks", "Almaty", 35),
            ("demo-host-3", "User's Yerevan Yoga", "Yerevan", 15),
        ]
        for code, title, city, days_ago in hosted_cities:
            _ensure_event(
                db,
                code=code,
                owner_id=user.id,
                title=title,
                location=city,
                days_ago=days_ago,
                participants_ids=[attendees[3].id, attendees[4].id],
                approved=True,
            )

        # 1 huge user-hosted event for Rainmaker (>=20 attendees).
        _ensure_event(
            db,
            code="demo-host-big",
            owner_id=user.id,
            title="User's Big Conference",
            location="Tashkent",  # reuses Tashkent — doesn't matter for Rainmaker
            days_ago=5,
            participants_ids=attendee_ids[:20],  # 20 attendees
            approved=True,
        )

        db.commit()

        # Trigger Founding Host for every event the user hosts that's the
        # earliest in its city — bypasses the approve_event hook since the
        # seed sets approved=True directly via SQL.
        from app.services.badges import award_founding_host

        user_events = (
            db.query(Event).filter(Event.owner_id == user.id, Event.approved.is_(True)).all()
        )
        for ev in user_events:
            award_founding_host(db, user, ev)
        db.commit()

        print("done. open the mobile app, refresh profile, watch badges unlock.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
