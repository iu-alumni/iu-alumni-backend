"""Telegram webhook handler for bot messages and poll answers."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import app_logger
from app.models.telegram import TelegramUser
from app.services.feedback_service import FeedbackService
from app.services.notification_service import NotificationService

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle incoming Telegram webhook updates.
    
    Handles:
    - /start and /help commands for user registration
    - /launch_app command to show mini app button
    - /leave_feedback command to send feedback polls
    - poll_answer callbacks for feedback submission
    """
    try:
        update = await request.json()
    except Exception as e:
        app_logger.error(f"Error parsing webhook request: {e}")
        return {"statusCode": 400, "body": "Bad Request"}

    # Handle poll answer (feedback submission)
    if "poll_answer" in update:
        poll_answer = update["poll_answer"]
        poll_id = poll_answer.get("poll_id")
        option_ids = poll_answer.get("option_ids", [])
        user = poll_answer.get("user", {})
        alias = user.get("username")
        chat_id = user.get("id")

        if not alias:
            return {"statusCode": 200, "body": "No username, skipping"}

        # Check if poll timeout
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

        return {"statusCode": 200, "body": result}

    # Handle message commands
    if "message" in update:
        msg = update["message"]
        msg_text = msg.get("text", "")
        from_user = msg.get("from", {})
        alias = from_user.get("username")
        chat_id = msg.get("chat", {}).get("id")

        if not alias:
            return {"statusCode": 200, "body": "No username, skipping"}

        # /start or /help - register user and send greeting
        if msg_text in ["/start", "/help"]:
            try:
                # Register or update user
                existing_user = (
                    db.query(TelegramUser)
                    .filter(TelegramUser.alias == alias)
                    .first()
                )

                if not existing_user:
                    user = TelegramUser(alias=alias, chat_id=chat_id)
                    db.add(user)
                else:
                    existing_user.chat_id = chat_id

                db.commit()

                # Send greeting
                await NotificationService.send_greeting(db, alias, chat_id)
                return {"statusCode": 200, "body": "ok"}
            except Exception as e:
                app_logger.error(f"Error in /start handler: {e}")
                db.rollback()
                return {"statusCode": 502, "body": f"Bad Gateway: {e}"}

        # /leave_feedback - send feedback polls
        elif msg_text == "/leave_feedback":
            try:
                await FeedbackService.send_feedback_polls(db, chat_id)
                return {"statusCode": 200, "body": "ok"}
            except Exception as e:
                app_logger.error(f"Error sending feedback polls: {e}")
                return {"statusCode": 502, "body": f"Bad Gateway: {e}"}

        # /launch_app - show mini app button
        elif msg_text == "/launch_app":
            try:
                await NotificationService.send_mini_app_button(chat_id)
                return {"statusCode": 200, "body": "ok"}
            except Exception as e:
                app_logger.error(f"Error sending mini app button: {e}")
                return {"statusCode": 502, "body": f"Bad Gateway: {e}"}

        else:
            return {"statusCode": 200, "body": "Not a recognized command, skipping"}

    return {"statusCode": 200, "body": "No handler for this update type"}
