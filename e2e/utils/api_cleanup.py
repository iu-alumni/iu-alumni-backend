from __future__ import annotations

from functools import lru_cache

import requests

from config import settings


@lru_cache
def _admin_token() -> str:
    response = requests.post(
        f"{settings.api_base_url}/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def delete_event_by_title(title: str) -> None:
    """Deletes every event matching `title` exactly, as an admin.

    Cleanup only — not part of what any test verifies, so it goes straight
    through the API rather than the UI. No-ops if nothing matches (e.g. the
    test failed before the event was ever created).
    """
    headers = {"Authorization": f"Bearer {_admin_token()}"}
    response = requests.get(
        f"{settings.api_base_url}/admin/events",
        params={"search": title},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    for item in response.json()["items"]:
        if item["title"] == title:
            requests.delete(
                f"{settings.api_base_url}/events/{item['id']}",
                headers=headers,
                timeout=30,
            ).raise_for_status()


def delete_alumnus_by_email(email: str) -> None:
    """Deletes the alumnus at `email` — owned events/projects, auth-flow
    rows (email verification, login codes, password reset/telegram
    tokens), and this alumnus's id in other people's participant/
    contributor lists all cascade on the backend (see
    `app/api/routes/admin/delete_alumni.py`). No-ops if nothing matches.

    Refuses to touch the fixed test account regardless of what's passed
    in — that one is shared infrastructure, not test data.
    """
    if email == settings.test_account_email:
        return

    headers = {"Authorization": f"Bearer {_admin_token()}"}
    response = requests.get(
        f"{settings.api_base_url}/admin/users",
        params={"search": email},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    for item in response.json()["items"]:
        if item["email"] == email:
            requests.delete(
                f"{settings.api_base_url}/admin/alumni/{item['id']}",
                headers=headers,
                timeout=30,
            ).raise_for_status()
