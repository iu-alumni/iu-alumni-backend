"""Extended unit tests for services to improve coverage."""

from unittest.mock import AsyncMock

import pytest

from app.core.security import create_access_token, get_password_hash, verify_password
from app.services.email_service import (
    send_login_code_email,
    send_manual_verification_notification,
    send_password_reset_email,
    send_telegram_verification_email,
    send_verification_email,
    send_verification_link_email,
    send_verification_success_email,
)


class TestEmailServiceExtended:
    """Extended tests for email service failure paths."""

    @pytest.mark.asyncio
    async def test_send_login_code_email_exception(self, mocker):
        """Test send_login_code_email handles FastMail exception."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_login_code_email("test@innopolis.university", "123456", "John")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_password_reset_email_exception(self, mocker):
        """Test send_password_reset_email handles exception."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_password_reset_email(
            "test@innopolis.university", "John", "https://example.com/reset?token=abc"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_verification_email_exception(self, mocker):
        """Test send_verification_email handles exception."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_verification_email("test@innopolis.university", "123456", "John")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_manual_verification_notification_exception(self, mocker):
        """Test send_manual_verification_notification handles exception."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_manual_verification_notification(
            "admin@innopolis.university", "user@innopolis.university", "John Doe"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_verification_success_email_exception(self, mocker):
        """Test send_verification_success_email handles exception."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_verification_success_email("test@innopolis.university", "John")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_verification_link_email_exception(self, mocker):
        """Test send_verification_link_email handles exception."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_verification_link_email(
            "test@innopolis.university", "John", "https://example.com/verify?token=abc"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_telegram_verification_email_exception(self, mocker):
        """Test send_telegram_verification_email handles exception."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        result = await send_telegram_verification_email(
            "test@innopolis.university", "John", "@telegramuser", "https://example.com/verify?token=abc"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_login_code_email_success(self, mocker):
        """Test send_login_code_email succeeds."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock()

        result = await send_login_code_email("test@innopolis.university", "123456", "John")

        assert result is True
        mock_fm.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_password_reset_email_success(self, mocker):
        """Test send_password_reset_email succeeds."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock()

        result = await send_password_reset_email(
            "test@innopolis.university", "John", "https://example.com/reset?token=abc"
        )

        assert result is True
        mock_fm.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, mocker):
        """Test send_verification_email succeeds."""
        mock_fm = mocker.patch("app.services.email_service.fm")
        mock_fm.send_message = AsyncMock()

        result = await send_verification_email("test@innopolis.university", "123456", "John")

        assert result is True
        mock_fm.send_message.assert_called_once()


class TestSecurityExtended:
    """Extended tests for security module."""

    def test_verify_password_correct(self):
        """Test verify_password with correct password."""
        plain_password = "TestPassword123!"
        hashed = get_password_hash(plain_password)

        assert verify_password(plain_password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verify_password with incorrect password."""
        plain_password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = get_password_hash(plain_password)

        assert verify_password(wrong_password, hashed) is False

    def test_get_password_hash_produces_different_hashes(self):
        """Test that get_password_hash produces different hashes for same password (due to salt)."""
        plain_password = "TestPassword123!"
        hash1 = get_password_hash(plain_password)
        hash2 = get_password_hash(plain_password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify the same password
        assert verify_password(plain_password, hash1) is True
        assert verify_password(plain_password, hash2) is True

    def test_create_access_token_returns_string(self):
        """Test create_access_token returns a valid token string."""
        data = {"sub": "test@example.com", "user_type": "alumni"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20
        # JWT token has 3 parts separated by dots
        assert token.count(".") == 2

    def test_create_access_token_with_different_data(self):
        """Test create_access_token with different payload data."""
        data1 = {"sub": "user1@example.com", "user_type": "alumni"}
        data2 = {"sub": "user2@example.com", "user_type": "admin"}

        token1 = create_access_token(data1)
        token2 = create_access_token(data2)

        # Different data should produce different tokens
        assert token1 != token2
        assert isinstance(token1, str)
        assert isinstance(token2, str)
