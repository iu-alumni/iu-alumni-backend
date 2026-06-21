"""Extended tests for notification service error paths."""
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.orm import Session

from app.models.telegram import TelegramUser
from app.services.notification_service import NotificationService


@pytest.mark.asyncio
class TestNotificationServiceErrorPaths:
    """Test NotificationService error/exception paths for coverage."""

    async def test_send_custom_notification_alias_not_found(self, db_session: Session):
        """Test send_custom_notification when alias not found."""
        result = await NotificationService.send_custom_notification(
            user_alias="nonexistent",
            text="Test message",
            db=db_session
        )
        assert result["status"] == "error"
        assert result["error"] == "Alias not found"
        assert "nonexistent" in result["missing"]

    async def test_send_custom_notification_exception(self, db_session: Session, mocker):
        """Test send_custom_notification when telegram service raises exception."""
        # Create a telegram user in db
        user = TelegramUser(alias="testuser", chat_id=12345)
        db_session.add(user)
        db_session.commit()

        # Mock telegram_service.send_message to raise exception
        mocker.patch(
            "app.services.notification_service.telegram_service.send_message",
            side_effect=Exception("Connection error")
        )

        result = await NotificationService.send_custom_notification(
            user_alias="testuser",
            text="Test message",
            db=db_session
        )
        assert result["status"] == "error"
        assert "Connection error" in result["message"]

    async def test_send_admin_notification_success(self, mocker):
        """Test send_admin_notification success path."""
        mock_send = mocker.patch(
            "app.services.notification_service.telegram_service.send_message",
            new_callable=AsyncMock
        )
        result = await NotificationService.send_admin_notification(text="Admin test")
        assert result["status"] == "ok"
        mock_send.assert_called_once()

    async def test_send_admin_notification_exception(self, mocker):
        """Test send_admin_notification when exception occurs."""
        mocker.patch(
            "app.services.notification_service.telegram_service.send_message",
            side_effect=Exception("Admin error")
        )

        result = await NotificationService.send_admin_notification(text="Admin test")
        assert result["status"] == "error"
        assert "Admin error" in result["message"]

    async def test_send_mini_app_button_success(self, mocker):
        """Test send_mini_app_button success path."""
        mock_send = mocker.patch(
            "app.services.notification_service.telegram_service.send_message",
            new_callable=AsyncMock
        )
        result = await NotificationService.send_mini_app_button(chat_id=12345)
        assert result is True
        mock_send.assert_called_once()

    async def test_send_mini_app_button_exception(self, mocker):
        """Test send_mini_app_button when exception occurs."""
        mocker.patch(
            "app.services.notification_service.telegram_service.send_message",
            side_effect=Exception("Mini app error")
        )

        result = await NotificationService.send_mini_app_button(chat_id=12345)
        assert result is False

