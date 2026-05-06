"""Unit tests for notification service."""

from unittest.mock import AsyncMock

import pytest

from app.services.notification_service import NotificationService


class TestNotificationService:
    """Test cases for notification service."""

    @pytest.mark.asyncio
    async def test_send_greeting_success(self, db_session, mocker):
        """Test successful send_greeting."""
        mock_telegram = mocker.patch("app.services.notification_service.telegram_service")
        mock_telegram.send_message = AsyncMock()

        result = await NotificationService.send_greeting(db_session, "testuser", 12345)

        assert result is True
        mock_telegram.send_message.assert_called_once_with(
            chat_id=12345,
            text=NotificationService.GREETING_MESSAGE.format(alias="testuser")
        )

    @pytest.mark.asyncio
    async def test_send_greeting_failure(self, db_session, mocker):
        """Test send_greeting with failure."""
        mock_telegram = mocker.patch("app.services.notification_service.telegram_service")
        mock_telegram.send_message = AsyncMock(side_effect=Exception("Telegram error"))

        result = await NotificationService.send_greeting(db_session, "testuser", 12345)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_join_notification_success(self, db_session, mocker):
        """Test successful send_join_notification."""
        # Create mock TelegramUser objects
        from app.models.telegram import TelegramUser
        owner = TelegramUser(alias="owner_success", chat_id=111)
        user = TelegramUser(alias="user_success", chat_id=222)

        db_session.add(owner)
        db_session.add(user)
        db_session.commit()

        mock_telegram = mocker.patch("app.services.notification_service.telegram_service")
        mock_telegram.send_message = AsyncMock()

        result = await NotificationService.send_join_notification(
            db_session, "Test Event", "owner_success", "user_success"
        )

        assert result == {"status": "ok"}
        assert mock_telegram.send_message.call_count == 2
        # Check message to user
        mock_telegram.send_message.assert_any_call(
            chat_id=222,
            text="You successfully joined this event: Test Event"
        )
        # Check message to owner
        mock_telegram.send_message.assert_any_call(
            chat_id=111,
            text="@user_success joined your event Test Event!"
        )

    @pytest.mark.asyncio
    async def test_send_join_notification_chat_id_none(self, db_session, mocker):
        """Test send_join_notification when owner's chat_id is None."""
        owner = type("TelegramUserStub", (), {"alias": "owner_chat_none", "chat_id": None})()
        user = type("TelegramUserStub", (), {"alias": "user_chat_none", "chat_id": 222})()

        class FakeQuery:
            def __init__(self):
                self.condition = None

            def filter(self, condition):
                self.condition = condition
                return self

            def first(self):
                if "owner_chat_none" in str(self.condition):
                    return owner
                return user

        fake_query = FakeQuery()

        def query_fn(model):
            return fake_query

        mocker.patch.object(db_session, "query", side_effect=query_fn)

        mock_telegram = mocker.patch("app.services.notification_service.telegram_service")
        mock_telegram.send_message = AsyncMock(side_effect=Exception("Telegram error"))

        result = await NotificationService.send_join_notification(
            db_session, "Test Event", "owner_chat_none", "user_chat_none"
        )

        assert result["status"] == "error"
        assert "Telegram error" in result["message"]
        assert mock_telegram.send_message.call_count == 1
        mock_telegram.send_message.assert_called_once_with(
            chat_id=222,
            text="You successfully joined this event: Test Event"
        )

    @pytest.mark.asyncio
    async def test_send_join_notification_owner_not_found(self, db_session):
        """Test send_join_notification when user not found."""
        from app.models.telegram import TelegramUser
        user = TelegramUser(alias="user_owner_not_found", chat_id=222)
        db_session.add(user)
        db_session.commit()

        result = await NotificationService.send_join_notification(
            db_session, "Test Event", "owner_not_found", "user_owner_not_found"
        )

        assert result == {
            "status": "error",
            "error": "Alias not found",
            "missing": ["owner_not_found"]
        }

    @pytest.mark.asyncio
    async def test_send_join_notification_both_missing(self, db_session):
        """Test send_join_notification when both users not found."""
        result = await NotificationService.send_join_notification(
            db_session, "Test Event", "owner_both_missing", "user_both_missing"
        )

        assert result == {
            "status": "error",
            "error": "Alias not found",
            "missing": ["owner_both_missing", "user_both_missing"]
        }

    @pytest.mark.asyncio
    async def test_send_join_notification_exception(self, db_session, mocker):
        """Test send_join_notification with exception."""
        from app.models.telegram import TelegramUser
        owner = TelegramUser(alias="owner_exception", chat_id=111)
        user = TelegramUser(alias="user_exception", chat_id=222)
        db_session.add(owner)
        db_session.add(user)
        db_session.commit()

        mock_telegram = mocker.patch("app.services.notification_service.telegram_service")
        mock_telegram.send_message = AsyncMock(side_effect=Exception("Telegram error"))

        result = await NotificationService.send_join_notification(
            db_session, "Test Event", "owner_exception", "user_exception"
        )

        assert result["status"] == "error"
        assert "Telegram error" in result["message"]

    @pytest.mark.asyncio
    async def test_send_upcoming_reminder_success(self, db_session, mocker):
        """Test successful send_upcoming_reminder."""
        from app.models.telegram import TelegramUser
        user = TelegramUser(alias="user_reminder_success", chat_id=222)
        db_session.add(user)
        db_session.commit()

        mock_telegram = mocker.patch("app.services.notification_service.telegram_service")
        mock_telegram.send_message = AsyncMock()

        result = await NotificationService.send_upcoming_reminder(
            db_session, "Test Event", "user_reminder_success"
        )

        assert result == {"status": "ok"}
        mock_telegram.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_upcoming_reminder_user_not_found(self, db_session):
        """Test send_upcoming_reminder when user not found."""
        result = await NotificationService.send_upcoming_reminder(
            db_session, "Test Event", "user_reminder_not_found"
        )

        assert result == {
            "status": "error",
            "error": "Alias not found",
            "missing": ["user_reminder_not_found"],
        }

    @pytest.mark.asyncio
    async def test_send_upcoming_reminder_exception(self, db_session, mocker):
        """Test send_upcoming_reminder with exception."""
        from app.models.telegram import TelegramUser
        user = TelegramUser(alias="user_reminder_exception", chat_id=222)
        db_session.add(user)
        db_session.commit()

        mock_telegram = mocker.patch("app.services.notification_service.telegram_service")
        mock_telegram.send_message = AsyncMock(side_effect=Exception("Telegram error"))

        result = await NotificationService.send_upcoming_reminder(
            db_session, "Test Event", "user_reminder_exception"
        )

        assert result["status"] == "error"
        assert "Telegram error" in result["message"]
