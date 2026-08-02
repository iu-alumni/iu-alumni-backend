"""Unit tests for Pydantic schemas."""

from pydantic import ValidationError
import pytest

from app.schemas.auth import (
    LoginRequest,
    LoginVerifyRequest,
    PasswordResetConfirmSchema,
    RegisterRequest,
)
from app.schemas.event import (
    AdminEventListItem,
    CreateEventRequest,
    EventListItem,
    UpdateEventRequest,
)


class TestAuthSchemas:
    """Test cases for authentication schemas."""

    def test_register_request_valid(self):
        """Test valid RegisterRequest."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "johndoe",
            "password": "password123"
        }

        request = RegisterRequest(**data)
        assert request.first_name == "John"
        assert request.email == "john.doe@innopolis.university"

    def test_register_request_invalid_email(self):
        """Test RegisterRequest with invalid email."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "invalid-email",
            "telegram_alias": "johndoe",
            "password": "password123"
        }

        with pytest.raises(ValidationError):
            RegisterRequest(**data)

    def test_register_request_short_password(self):
        """Test RegisterRequest with too short password."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "johndoe",
            "password": "123"  # Too short
        }

        with pytest.raises(ValidationError):
            RegisterRequest(**data)

    def test_login_request_valid(self):
        """Test valid LoginRequest."""
        data = {
            "email": "john.doe@example.com",
            "password": "password123"
        }

        request = LoginRequest(**data)
        assert request.email == "john.doe@example.com"
        assert request.password == "password123"

    def test_login_verify_request_valid(self):
        """Test valid LoginVerifyRequest."""
        data = {
            "session_token": "abc123",
            "code": "123456"
        }

        request = LoginVerifyRequest(**data)
        assert request.session_token == "abc123"
        assert request.code == "123456"

    def test_login_verify_request_invalid_code(self):
        """Test LoginVerifyRequest with invalid code."""
        data = {
            "session_token": "abc123",
            "code": "12345"  # Too short
        }

        with pytest.raises(ValidationError):
            LoginVerifyRequest(**data)

    def test_password_reset_confirm_valid(self):
        """Test valid PasswordResetConfirmSchema."""
        data = {
            "token": "reset_token_123",
            "new_password": "newpassword123"
        }

        schema = PasswordResetConfirmSchema(**data)
        assert schema.token == "reset_token_123"
        assert schema.new_password == "newpassword123"

    def test_register_request_first_name_too_short(self):
        """Test RegisterRequest with first_name too short."""
        data = {
            "first_name": "",  # Empty
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "johndoe",
            "password": "password123"
        }

        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)
        assert "first_name" in str(exc_info.value)

    def test_register_request_first_name_too_long(self):
        """Test RegisterRequest with first_name too long."""
        data = {
            "first_name": "A" * 101,  # 101 characters
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "johndoe",
            "password": "password123"
        }

        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)
        assert "first_name" in str(exc_info.value)

    def test_register_request_last_name_too_short(self):
        """Test RegisterRequest with last_name too short."""
        data = {
            "first_name": "John",
            "last_name": "",  # Empty
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "johndoe",
            "password": "password123"
        }

        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)
        assert "last_name" in str(exc_info.value)

    def test_register_request_last_name_too_long(self):
        """Test RegisterRequest with last_name too long."""
        data = {
            "first_name": "John",
            "last_name": "D" * 101,  # 101 characters
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "johndoe",
            "password": "password123"
        }

        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)
        assert "last_name" in str(exc_info.value)

    def test_register_request_telegram_alias_too_short(self):
        """Test RegisterRequest with telegram_alias too short."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "ab",  # 2 characters
            "password": "password123"
        }

        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)
        assert "telegram_alias" in str(exc_info.value)

    def test_register_request_telegram_alias_too_long(self):
        """Test RegisterRequest with telegram_alias too long."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "a" * 51,  # 51 characters
            "password": "password123"
        }

        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)
        assert "telegram_alias" in str(exc_info.value)

    def test_register_request_invalid_email_domain(self):
        """Test RegisterRequest with invalid email domain."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "john.doe@gmail.com",  # Invalid domain
            "telegram_alias": "johndoe",
            "password": "password123"
        }

        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)
        assert "Email must be an Innopolis email" in str(exc_info.value)

    def test_register_request_valid_email_domains(self):
        """Test RegisterRequest with valid email domains."""
        valid_emails = [
            "john.doe@innopolis.university",
            "jane.smith@innopolis.ru"
        ]

        for email in valid_emails:
            data = {
                "first_name": "John",
                "last_name": "Doe",
                "graduation_year": "2020",
                "email": email,
                "telegram_alias": "johndoe",
                "password": "password123"
            }
            request = RegisterRequest(**data)
            assert request.email == email

    def test_register_request_manual_verification_true(self):
        """Test RegisterRequest with manual_verification set to True."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "johndoe",
            "password": "password123",
            "manual_verification": True
        }

        request = RegisterRequest(**data)
        assert request.manual_verification is True

    def test_login_request_invalid_email(self):
        """Test LoginRequest with invalid email format."""
        data = {
            "email": "invalid-email",
            "password": "password123"
        }

        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(**data)
        assert "email" in str(exc_info.value)

    def test_login_verify_request_invalid_code_length(self):
        """Test LoginVerifyRequest with invalid code length."""
        data = {
            "session_token": "abc123",
            "code": "12345"  # 5 digits instead of 6
        }

        with pytest.raises(ValidationError) as exc_info:
            LoginVerifyRequest(**data)
        assert "code" in str(exc_info.value)

    def test_login_verify_request_invalid_code_format(self):
        """Test LoginVerifyRequest with non-digit code."""
        data = {
            "session_token": "abc123",
            "code": "12a456"  # Contains letter
        }

        with pytest.raises(ValidationError) as exc_info:
            LoginVerifyRequest(**data)
        assert "code" in str(exc_info.value)

    def test_password_reset_request_valid(self):
        """Test valid PasswordResetRequestSchema."""
        data = {
            "email": "john.doe@innopolis.university"
        }

        from app.schemas.auth import PasswordResetRequestSchema
        schema = PasswordResetRequestSchema(**data)
        assert schema.email == "john.doe@innopolis.university"

    def test_password_reset_confirm_password_too_short(self):
        """Test PasswordResetConfirmSchema with password too short."""
        data = {
            "token": "reset_token_123",
            "new_password": "123"  # Too short
        }

        with pytest.raises(ValidationError) as exc_info:
            PasswordResetConfirmSchema(**data)
        assert "new_password" in str(exc_info.value)

    def test_admin_create_request_valid(self):
        """Test valid AdminCreateRequest."""
        data = {
            "email": "admin@innopolis.university",
            "password": "adminpass123"
        }

        from app.schemas.auth import AdminCreateRequest
        request = AdminCreateRequest(**data)
        assert request.email == "admin@innopolis.university"
        assert request.password == "adminpass123"

    def test_token_response_valid(self):
        """Test valid TokenResponse."""
        data = {
            "access_token": "token123",
            "token_type": "bearer"
        }

        from app.schemas.auth import TokenResponse
        response = TokenResponse(**data)
        assert response.access_token == "token123"
        assert response.token_type == "bearer"


class TestEventSchemas:
    """Test cases for event schemas."""

    @pytest.mark.parametrize("schema", [EventListItem, AdminEventListItem])
    def test_event_lists_do_not_embed_base64_covers(self, schema):
        item = schema(
            id="event-1",
            owner_id="owner-1",
            participants_ids=[],
            title="Meetup",
            description="Description",
            location="Innopolis",
            datetime="2026-08-01T12:00:00",
            cost=0,
            is_online=False,
            approved=True,
        )

        assert "cover" not in item.model_dump()

    def test_create_event_rejects_blank_required_text(self):
        """Test CreateEventRequest rejects whitespace-only text fields."""
        data = {
            "title": "   ",
            "description": "Description",
            "location": "Room 101",
            "datetime": "2025-01-01T10:00:00",
            "cost": 0,
            "is_online": False,
        }

        with pytest.raises(ValidationError) as exc_info:
            CreateEventRequest(**data)
        assert "title" in str(exc_info.value)

    def test_create_event_trims_text_and_normalizes_empty_cover(self):
        """Test CreateEventRequest trims text fields and treats blank cover as absent."""
        request = CreateEventRequest(
            title="  Workshop  ",
            description="  Learn things  ",
            location="  Room 101  ",
            datetime="2025-01-01T10:00:00",
            cost=0,
            is_online=False,
            cover="",
        )

        assert request.title == "Workshop"
        assert request.description == "Learn things"
        assert request.location == "Room 101"
        assert request.cover is None

    def test_update_event_rejects_blank_required_text_when_present(self):
        """Test UpdateEventRequest rejects blank editable text fields."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateEventRequest(description="  ")
        assert "description" in str(exc_info.value)

    def test_update_event_normalizes_empty_cover(self):
        """Test UpdateEventRequest uses blank cover as an explicit clear request."""
        request = UpdateEventRequest(cover="")

        assert request.cover is None
        assert "cover" in request.model_fields_set
