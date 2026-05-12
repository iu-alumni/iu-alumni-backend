"""Unit tests for security functions."""

from datetime import datetime

from app.core.security import (
    create_access_token,
    get_password_hash,
    get_random_token,
    verify_password,
)


class TestSecurity:
    """Test cases for security functions."""

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_create_access_token(self, mocker):
        """Test JWT token creation."""
        # Mock jwt.encode
        mock_jwt_encode = mocker.patch("app.core.security.jwt.encode")
        mock_jwt_encode.return_value = "test_token"

        data = {"sub": "test@example.com"}
        token = create_access_token(data)

        assert token == "test_token"
        # Verify jwt.encode was called once
        assert mock_jwt_encode.call_count == 1
        call_args, call_kwargs = mock_jwt_encode.call_args
        payload = call_args[0]
        secret = call_args[1]
        algorithm = call_kwargs["algorithm"]

        # Check payload contains original data
        assert payload["sub"] == "test@example.com"
        # Check exp is set and is a datetime
        assert "exp" in payload
        assert isinstance(payload["exp"], datetime)

        # Check secret and algorithm
        assert secret == "test-secret-key-for-testing-purposes-only-32c"
        assert algorithm == "HS256"

    def test_create_access_token_different_data(self, mocker):
        """Test JWT token creation with different data."""
        # Mock jwt.encode
        mock_jwt_encode = mocker.patch("app.core.security.jwt.encode")
        mock_jwt_encode.return_value = "test_token"

        data = {"user_id": "123", "role": "admin"}
        token = create_access_token(data)

        assert token == "test_token"
        # Verify jwt.encode was called once
        assert mock_jwt_encode.call_count == 1
        call_args, call_kwargs = mock_jwt_encode.call_args
        payload = call_args[0]
        secret = call_args[1]
        algorithm = call_kwargs["algorithm"]

        # Check payload contains original data
        assert payload["user_id"] == "123"
        assert payload["role"] == "admin"
        # Check exp is set and is a datetime
        assert "exp" in payload
        assert isinstance(payload["exp"], datetime)

        # Check secret and algorithm
        assert secret == "test-secret-key-for-testing-purposes-only-32c"
        assert algorithm == "HS256"

    def test_get_random_token_uniqueness(self):
        """Test that get_random_token generates unique tokens."""
        tokens = [get_random_token() for _ in range(10)]
        assert len(set(tokens)) == 10  # All unique

    def test_get_random_token_length(self):
        """Test that get_random_token generates tokens of expected length."""
        token = get_random_token()
        # get_random_token uses secrets.token_urlsafe(32) which gives ~43 characters
        assert len(token) > 30
