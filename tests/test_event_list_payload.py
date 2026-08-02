"""Regression tests for the event-feed payload size.

Synthetic large covers reproduce the production risk without needing a copy
of production data.
"""

from datetime import datetime, timedelta

from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni


EVENT_COUNT = 100
COVER_SIZE = 250_000
MAX_LIST_RESPONSE_SIZE = 100_000


def test_large_covers_do_not_inflate_public_or_admin_event_lists(client, db_session):
    owner = Alumni(
        id="payload-owner",
        email="payload-owner@innopolis.university",
        first_name="Payload",
        last_name="Owner",
        graduation_year="2026",
    )
    db_session.add(owner)
    base_time = datetime(2026, 8, 1, 12, 0)
    db_session.add_all(
        [
            Event(
                id=f"payload-event-{index:03d}",
                owner_id=owner.id,
                participants_ids=[],
                title=f"Synthetic event {index}",
                description="Synthetic payload regression event",
                location="Innopolis",
                datetime=base_time + timedelta(minutes=index),
                cost=0,
                is_online=False,
                cover="A" * COVER_SIZE,
                approved=True,
            )
            for index in range(EVENT_COUNT)
        ]
    )
    db_session.commit()

    client.app.dependency_overrides[get_current_user] = lambda: owner
    public_response = client.get("/api/v1/events/?limit=100")

    admin = Admin(id="payload-admin", email="payload-admin@innopolis.university")
    client.app.dependency_overrides[get_current_user] = lambda: admin
    admin_response = client.get("/api/v1/admin/events?limit=100")

    for response in (public_response, admin_response):
        assert response.status_code == 200
        assert len(response.json()["items"]) == EVENT_COUNT
        assert all("cover" not in item for item in response.json()["items"])
        assert len(response.content) < MAX_LIST_RESPONSE_SIZE

