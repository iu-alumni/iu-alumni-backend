"""Telegram bot long-polling service.

Replaces the webhook approach by continuously calling getUpdates so the bot
works without a publicly reachable endpoint.
"""

import asyncio
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import app_logger
from app.models.telegram import TelegramUser
from app.services.feedback_service import FeedbackService
from app.services.notification_service import NotificationService
from app.services.telegram_bot import telegram_service


async def _handle_update(update: dict[str, Any], db: Session) -> None:
    """Dispatch a single Telegram update to the appropriate handler."""

    # Handle poll answers (feedback submission)
    if "poll_answer" in update:
        poll_answer = update["poll_answer"]
        poll_id = poll_answer.get("poll_id")
        option_ids = poll_answer.get("option_ids", [])
        user = poll_answer.get("user", {})
        alias = user.get("username")
        chat_id = user.get("id")

        if not alias:
            return

        result = FeedbackService.process_poll_answer(db, poll_id, option_ids, alias)

        if result.get("status") == "timeout":
            try:
                await NotificationService.send_custom_notification(
                    db,
                    alias,
                    "⏰ Feedback session timed out. Please re-submit your feedback.",
                )
                await FeedbackService.send_feedback_polls(db, chat_id)
            except Exception as e:
                app_logger.error(f"Error handling poll timeout: {e}")
        return

    # Handle text commands
    if "message" in update:
        msg = update["message"]
        msg_text = msg.get("text", "")
        from_user = msg.get("from", {})
        alias = from_user.get("username")
        chat_id = msg.get("chat", {}).get("id")

        if not alias:
            return

        if msg_text in ["/start", "/help"]:
            try:
                existing_user = (
                    db.query(TelegramUser)
                    .filter(TelegramUser.alias == alias)
                    .first()
                )
                if not existing_user:
                    db.add(TelegramUser(alias=alias, chat_id=chat_id))
                else:
                    existing_user.chat_id = chat_id
                db.commit()
                await NotificationService.send_greeting(db, alias, chat_id)
            except Exception as e:
                app_logger.error(f"Error in /start handler: {e}")
                db.rollback()

        elif msg_text == "/leave_feedback":
            try:
                await FeedbackService.send_feedback_polls(db, chat_id)
            except Exception as e:
                app_logger.error(f"Error sending feedback polls: {e}")

        elif msg_text == "/launch_app":
            try:
                await NotificationService.send_mini_app_button(chat_id)
            except Exception as e:
                app_logger.error(f"Error sending mini app button: {e}")


async def start_polling(stop_event: asyncio.Event) -> None:
    """Long-poll Telegram for updates until stop_event is set.

    Uses getUpdates with a 30-second server-side timeout so the loop stays
    idle without burning CPU or connections.
    """
    offset: int | None = None
    api_url = telegram_service._get_api_url("getUpdates")

    app_logger.info("Telegram polling started")

    async with httpx.AsyncClient() as client:
        while not stop_event.is_set():
            params: dict[str, Any] = {"timeout": 30, "allowed_updates": ["message", "poll_answer"]}
            if offset is not None:
                params["offset"] = offset

            try:
                response = await asyncio.wait_for(
                    client.get(api_url, params=params, timeout=40.0),
                    timeout=45.0,
                )
                data = response.json()
            except asyncio.CancelledError:
                break
            except Exception as e:
                app_logger.error(f"Telegram polling error: {e}")
                await asyncio.sleep(5)
                continue

            if not data.get("ok"):
                app_logger.error(f"getUpdates error: {data.get('description')}")
                await asyncio.sleep(5)
                continue

            updates: list[dict] = data.get("result", [])
            if updates:
                offset = updates[-1]["update_id"] + 1

            db: Session = SessionLocal()
            try:
                for update in updates:
                    try:
                        await _handle_update(update, db)
                    except Exception as e:
                        app_logger.error(f"Error handling update {update.get('update_id')}: {e}")
            finally:
                db.close()

    app_logger.info("Telegram polling stopped")
