"""Unit tests for authentication register endpoint."""

from unittest.mock import MagicMock

from fastapi import HTTPException
import pytest

from app.api.routes.authentication.register import register
from app.schemas.auth import RegisterRequest


def _http_request(base_url: str = "https://api.example.test/"):
    request = MagicMock()
    request.base_url = base_url
    return request


class TestRegister:
    """Test cases for user registration."""

    @pytest.mark.asyncio
    async def test_register_success(self, db_session, mocker):
        """Test successful user registration."""
        mocker.patch("app.api.routes.authentication.register.get_random_token", return_value="test_user_id")
        mocker.patch("app.api.routes.authentication.register.get_password_hash", return_value="hashed_password")
        mocker.patch("app.api.routes.authentication.register.is_email_allowed", return_value=True)

        mock_create_link_verification_record = mocker.patch(
            "app.api.routes.authentication.register.create_link_verification_record"
        )
        mock_record = MagicMock()
        mock_create_link_verification_record.return_value = (mock_record, "test_token")

        mock_send_verification_link_email = mocker.patch(
            "app.api.routes.authentication.register.send_verification_link_email",
            return_value=True,
        )

        request = RegisterRequest(
            first_name="John",
            last_name="Doe",
            graduation_year="2020",
            email="john.doe@innopolis.university",
            telegram_alias="johndoe",
            password="password123",
        )

        background_tasks = MagicMock()
        result = await register(
            request,
            background_tasks,
            _http_request(),
            db_session,
        )

        assert result["message"] == "Registration successful. Please check your email for a confirmation link."
        assert result["email"] == "john.doe@innopolis.university"

        from app.models.users import Alumni

        user = db_session.query(Alumni).filter(Alumni.email == "john.doe@innopolis.university").first()
        assert user is not None
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.email == "john.doe@innopolis.university"
        assert user.graduation_year == "2020"
        assert user.telegram_alias == "johndoe"
        assert user.is_verified is False
        assert user.is_banned is False
        assert user.hashed_password == "hashed_password"
        assert user.is_verified is False
        mock_send_verification_link_email.assert_awaited_once_with(
            "john.doe@innopolis.university",
            "John",
            "https://api.example.test/api/v1/auth/verify?token=test_token",
        )

    @pytest.mark.asyncio
    async def test_register_email_already_exists(self, db_session):
        """Test registration with existing email."""
        from app.models.users import Alumni

        existing_user = Alumni(
            id="existing_id",
            email="existing@innopolis.university",
            hashed_password="hash",
            first_name="Existing",
            last_name="User",
            graduation_year="2020",
        )
        db_session.add(existing_user)
        db_session.commit()

        request = RegisterRequest(
            first_name="John",
            last_name="Doe",
            graduation_year="2020",
            email="existing@innopolis.university",
            telegram_alias="johndoe",
            password="password123",
        )

        background_tasks = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await register(
                request,
                background_tasks,
                _http_request(),
                db_session,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Email already registered"

    @pytest.mark.asyncio
    async def test_register_manual_verification(self, db_session, mocker):
        """Test registration requiring manual verification."""
        mocker.patch("app.api.routes.authentication.register.is_email_allowed", return_value=False)
        mocker.patch("app.api.routes.authentication.register.get_random_token", return_value="test_user_id")
        mocker.patch("app.api.routes.authentication.register.get_password_hash", return_value="hashed_password")
        mocker.patch(
            "app.api.routes.authentication.register.create_verification_record",
            return_value=MagicMock(),
        )
        mocker.patch(
            "app.api.routes.authentication.register.send_manual_verification_notification",
            return_value=True,
        )

        request = RegisterRequest(
            first_name="John",
            last_name="Doe",
            graduation_year="2020",
            email="john.doe@innopolis.university",
            telegram_alias="johndoe",
            password="password123",
        )

        background_tasks = MagicMock()
        result = await register(
            request,
            background_tasks,
            _http_request(),
            db_session,
        )

        assert result["message"] == (
            "Registration successful. Your email is not in our graduates list. "
            "Your account is pending manual verification by an administrator."
        )
        assert result["email"] == "john.doe@innopolis.university"

        from app.models.users import Alumni

        user = db_session.query(Alumni).filter(Alumni.email == "john.doe@innopolis.university").first()
        assert user is not None
        assert user.is_verified is False
