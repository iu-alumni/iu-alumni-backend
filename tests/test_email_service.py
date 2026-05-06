"""Unit tests for email service."""

from unittest.mock import AsyncMock

from fastapi_mail import MessageSchema, MessageType
import pytest

from app.services.email_service import (
    send_login_code_email,
    send_manual_verification_notification,
    send_password_reset_email,
    send_verification_email,
)


class TestEmailService:
    """Test cases for email service functions."""

    @pytest.mark.asyncio
    async def test_send_login_code_email_success(self, mocker):
        """Test successful send_login_code_email."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock()

        result = await send_login_code_email(
            email="test@example.com",
            first_name="John",
            code="123456",
            expiry_minutes=10
        )

        assert result is True
        mock_fm.send_message.assert_called_once_with(
            MessageSchema(
                subject="IU Alumni — Your login code",
                recipients=["test@example.com"],
                template_body={
                    "first_name": "John",
                    "code": "123456",
                    "expiry_minutes": 10,
                },
                subtype=MessageType.html,
            ),
            template_name="login_code.html"
        )

    @pytest.mark.asyncio
    async def test_send_login_code_email_failure(self, mocker):
        """Test send_login_code_email with failure."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_login_code_email(
            email="test@example.com",
            first_name="John",
            code="123456"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_password_reset_email_success(self, mocker):
        """Test successful send_password_reset_email."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock()

        result = await send_password_reset_email(
            email="test@example.com",
            first_name="John",
            reset_link="http://example.com/reset",
            expiry_minutes=30
        )

        assert result is True
        mock_fm.send_message.assert_called_once_with(
            MessageSchema(
                subject="IU Alumni — Reset your password",
                recipients=["test@example.com"],
                template_body={
                    "first_name": "John",
                    "reset_link": "http://example.com/reset",
                    "expiry_minutes": 30,
                },
                subtype=MessageType.html,
            ),
            template_name="password_reset.html"
        )

    @pytest.mark.asyncio
    async def test_send_password_reset_email_failure(self, mocker):
        """Test send_password_reset_email with failure."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_password_reset_email(
            email="test@example.com",
            first_name="John",
            reset_link="http://example.com/reset"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, mocker):
        """Test successful send_verification_email."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock()

        result = await send_verification_email(
            email="test@example.com",
            first_name="John",
            verification_code="123456"
        )

        assert result is True
        mock_fm.send_message.assert_called_once_with(
            MessageSchema(
                subject="Verify your IU Alumni account",
                recipients=["test@example.com"],
                template_body={
                    "first_name": "John",
                    "verification_code": "123456",
                },
                subtype=MessageType.html,
            ),
            template_name="verification.html"
        )

    @pytest.mark.asyncio
    async def test_send_verification_email_failure(self, mocker):
        """Test send_verification_email with failure."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_verification_email(
            email="test@example.com",
            first_name="John",
            verification_code="123456"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_manual_verification_notification_success(self, mocker):
        """Test successful send_manual_verification_notification."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock()

        result = await send_manual_verification_notification(
            admin_email="admin@example.com",
            user_email="user@example.com",
            user_name="John Doe"
        )

        assert result is True
        mock_fm.send_message.assert_called_once_with(
            MessageSchema(
                subject="Manual Verification Request — IU Alumni",
                recipients=["admin@example.com"],
                template_body={
                    "user_email": "user@example.com",
                    "user_name": "John Doe",
                },
                subtype=MessageType.html,
            ),
            template_name="manual_verification.html"
        )

    @pytest.mark.asyncio
    async def test_send_manual_verification_notification_failure(self, mocker):
        """Test send_manual_verification_notification with failure."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_manual_verification_notification(
            admin_email="admin@example.com",
            user_email="user@example.com",
            user_name="John Doe"
        )

        assert result is False
