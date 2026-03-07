"""Service for sending various notifications to users."""

import os

from sqlalchemy.orm import Session

from app.core.logging import app_logger
from app.models.telegram import TelegramUser
from app.services.telegram_bot import telegram_service


class NotificationService:
    """Service for sending notifications via Telegram."""

    GREETING_MESSAGE = """👋 Hello, {alias}
🎓 Welcome to IU Alumap — we're glad to have you here!
🔔 You will receive your app notifications through this bot

Here's what you can do:
➡️ <b>Launch Mini App:</b> /launch_app
💬 <b>Leave feedback:</b> /leave_feedback

🛡️ When you create an event, please wait for <b>admin verification</b> before it becomes visible to others

🪲 Found a bug? <a href="https://forms.yandex.ru/u/68809ed302848f0f982a1ba0">Bug report form</a>

📲 To contact the app team, send a message to our project manager: @VittoryAlice

🚀 <a href="https://www.rustore.ru/catalog/app/com.innopolis.alumni">Download for Android from RuStore!</a>

- - - - - -

👋 Привет, {alias}
🎓 Добро пожаловать в IU Alumap — рады тебя видеть!
🔔 Уведомления от приложения будут приходить в этот бот

Вот что можно сделать:
➡️ <b>Запустить Mini App:</b> /launch_app
💬 <b>Дать обратную связь:</b> /leave_feedback

🛡️ После создания события, пожалуйста, подожди <b>подтверждения от администратора</b> перед тем, как оно станет доступным для других пользователей

🪲 Нашли баг? <a href="https://forms.yandex.ru/u/68809ed302848f0f982a1ba0">Форма для отчёта о баге</a>

📲 Чтобы связаться с командой приложения, напишите нашему менеджеру проекта: @VittoryAlice

🚀 <a href="https://www.rustore.ru/catalog/app/com.innopolis.alumni">Мы есть на RuStore!</a>
"""

    MINI_APP_URL = os.getenv("MINI_APP_URL", "https://iualumni.netlify.app/")

    @staticmethod
    async def send_greeting(_db: Session, alias: str, chat_id: int) -> bool:
        """Send welcome greeting to a new user.

        Args:
            db: Database session
            alias: User's Telegram alias
            chat_id: User's Telegram chat ID

        Returns:
            True if successful, False otherwise
        """
        try:
            await telegram_service.send_message(
                chat_id=chat_id, text=NotificationService.GREETING_MESSAGE.format(alias=alias)
            )
            return True
        except Exception as e:
            app_logger.error(f"Error sending greeting to {alias}: {e}")
            return False

    @staticmethod
    async def send_join_notification(
        db: Session, event_name: str, owner_alias: str, user_alias: str
    ) -> dict:
        """Notify user and owner when user joins event.

        Args:
            db: Database session
            event_name: Name of the event
            owner_alias: Owner's Telegram alias
            user_alias: User's Telegram alias

        Returns:
            Status dictionary
        """
        try:
            # Get chat IDs from database
            owner = (
                db.query(TelegramUser)
                .filter(TelegramUser.alias == owner_alias)
                .first()
            )
            user = (
                db.query(TelegramUser)
                .filter(TelegramUser.alias == user_alias)
                .first()
            )

            if not owner or not user:
                missing = []
                if not owner:
                    missing.append(owner_alias)
                if not user:
                    missing.append(user_alias)
                return {
                    "status": "error",
                    "error": "Alias not found",
                    "missing": missing,
                }

            # Send messages
            await telegram_service.send_message(
                chat_id=user.chat_id,
                text=f"You successfully joined this event: {event_name}",
            )
            await telegram_service.send_message(
                chat_id=owner.chat_id,
                text=f"@{user_alias} joined your event {event_name}!",
            )

            return {"status": "ok"}
        except Exception as e:
            app_logger.error(f"Error sending join notification: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def send_upcoming_reminder(
        db: Session, event_name: str, user_alias: str
    ) -> dict:
        """Send reminder about upcoming event.

        Args:
            db: Database session
            event_name: Name of the event
            user_alias: User's Telegram alias

        Returns:
            Status dictionary
        """
        try:
            user = (
                db.query(TelegramUser)
                .filter(TelegramUser.alias == user_alias)
                .first()
            )

            if not user:
                return {
                    "status": "error",
                    "error": "Alias not found",
                    "missing": [user_alias],
                }

            await telegram_service.send_message(
                chat_id=user.chat_id,
                text=f'⏰ Reminder: your event "{event_name}" is starting soon!',
            )

            return {"status": "ok"}
        except Exception as e:
            app_logger.error(f"Error sending upcoming reminder: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def send_custom_notification(
        db: Session, user_alias: str, text: str
    ) -> dict:
        """Send custom message to user.

        Args:
            db: Database session
            user_alias: User's Telegram alias
            text: Message text to send

        Returns:
            Status dictionary
        """
        try:
            user = (
                db.query(TelegramUser)
                .filter(TelegramUser.alias == user_alias)
                .first()
            )

            if not user:
                return {
                    "status": "error",
                    "error": "Alias not found",
                    "missing": [user_alias],
                }

            await telegram_service.send_message(
                chat_id=user.chat_id,
                text=text,
            )

            return {"status": "ok"}
        except Exception as e:
            app_logger.error(f"Error sending custom notification: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def send_admin_notification(text: str) -> dict:
        """Send notification to admin group.

        Args:
            text: Message text to send

        Returns:
            Status dictionary
        """
        try:
            await telegram_service.send_message(
                chat_id=telegram_service.ADMIN_CHAT_ID, text=text
            )
            return {"status": "ok"}
        except Exception as e:
            app_logger.error(f"Error sending admin notification: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def send_mini_app_button(chat_id: int) -> bool:
        """Send mini app button to user.

        Args:
            chat_id: User's Telegram chat ID

        Returns:
            True if successful, False otherwise
        """
        try:
            await telegram_service.send_message(
                chat_id=chat_id,
                text="📱 Кнопка для перехода к Mini App:",
                reply_markup={
                    "inline_keyboard": [
                        [{"text": "Перейти", "web_app": {"url": NotificationService.MINI_APP_URL}}]
                    ]
                },
            )
            return True
        except Exception as e:
            app_logger.error(f"Error sending mini app button: {e}")
            return False
