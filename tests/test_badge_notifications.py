"""Tests for best-effort Telegram badge notifications."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.users import Alumni
from app.services.badge_notifications import notify_badge_awards


def _alumni(*, verified: bool = True, alias: str | None = "ada") -> Alumni:
    return Alumni(
        id="alumni-1",
        email="ada@innopolis.university",
        hashed_password="hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
        is_telegram_verified=verified,
        telegram_alias=alias,
    )


@pytest.mark.asyncio
async def test_notification_is_a_noop_without_awards_or_verified_alias():
    db = MagicMock()

    await notify_badge_awards(db, _alumni(), [])
    await notify_badge_awards(db, _alumni(verified=False), ["founding_host"])
    await notify_badge_awards(db, _alumni(alias=None), ["founding_host"])

    db.query.assert_not_called()


@pytest.mark.asyncio
async def test_notification_is_a_noop_when_bot_chat_or_badge_is_missing():
    db = MagicMock()
    telegram_query = MagicMock()
    telegram_query.filter.return_value.first.return_value = None
    db.query.return_value = telegram_query

    await notify_badge_awards(db, _alumni(), ["founding_host"])

    db.query.assert_called_once()

    telegram_query = MagicMock()
    telegram_query.filter.return_value.first.return_value = MagicMock(chat_id=42)
    badge_query = MagicMock()
    badge_query.filter.return_value.all.return_value = []
    db.query.side_effect = [telegram_query, badge_query]
    await notify_badge_awards(db, _alumni(), ["founding_host"])


@pytest.mark.asyncio
async def test_notification_sends_one_message_for_all_awards(mocker):
    db = MagicMock()
    telegram_query = MagicMock()
    telegram_query.filter.return_value.first.return_value = MagicMock(chat_id=42)
    badge_query = MagicMock()
    badge_query.filter.return_value.all.return_value = [
        MagicMock(name="Founding Host"),
        MagicMock(name="Open Source Contributor"),
    ]
    db.query.side_effect = [telegram_query, badge_query]
    send = mocker.patch(
        "app.services.badge_notifications.telegram_service.send_message",
        new_callable=AsyncMock,
    )

    await notify_badge_awards(db, _alumni(), ["founding_host", "open_source"])

    send.assert_awaited_once()
    assert send.call_args.kwargs["chat_id"] == 42
    assert "Founding Host" in send.call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_notification_swallows_telegram_failures(mocker):
    db = MagicMock()
    telegram_query = MagicMock()
    telegram_query.filter.return_value.first.return_value = MagicMock(chat_id=42)
    badge_query = MagicMock()
    badge_query.filter.return_value.all.return_value = [MagicMock(name="Founding Host")]
    db.query.side_effect = [telegram_query, badge_query]
    mocker.patch(
        "app.services.badge_notifications.telegram_service.send_message",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Telegram unavailable"),
    )

    await notify_badge_awards(db, _alumni(), ["founding_host"])
