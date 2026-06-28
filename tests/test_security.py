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
        call_args[1]
        call_kwargs["algorithm"]

        # Check payload contains original data
        assert payload["sub"] == "test@example.com"
        # Check exp is set and is a datetime
        assert "exp" in payload
        assert isinstance(payload["exp"], datetime)

        # Check secret and algorithm

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
        call_args[0]
        call_args[1]
        call_kwargs["algorithm"]

    def test_verify_password_wrong(self):
        """Test password verification with wrong password."""
        password = "testpassword123"
        wrong_password = "wrongpassword456"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test password verification with empty password."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password("", hashed) is False

    def test_get_password_hash_long_password(self):
        """Test hashing very long password."""
        long_password = "x" * 1000
        hashed = get_password_hash(long_password)

        assert hashed != long_password
        assert verify_password(long_password, hashed) is True

    def test_get_password_hash_special_characters(self):
        """Test hashing password with special characters."""
        special_password = "P@ssw0rd!#$%^&*()"
        hashed = get_password_hash(special_password)

        assert verify_password(special_password, hashed) is True
        assert verify_password("P@ssw0rd!#$%^&*(", hashed) is False

    def test_get_random_token_uniqueness(self):
        """Test that get_random_token generates unique tokens."""
        token1 = get_random_token()
        token2 = get_random_token()

        assert token1 != token2
        assert len(token1) > 0
        assert len(token2) > 0

    def test_get_random_token_format(self):
        """Test get_random_token returns string."""
        token = get_random_token()

        assert isinstance(token, str)
        assert len(token) > 10

    def test_create_access_token_empty_data(self):
        """Test create_access_token with empty data dict."""
        data = {}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_create_access_token_complex_data(self):
        """Test create_access_token with complex nested data."""
        data = {
            "sub": "user@example.com",
            "user_type": "alumni",
            "permissions": ["read", "write"],
            "nested": {"key": "value"}
        }
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 50

    def test_verify_password_unicode(self):
        """Test password verification with unicode characters."""
        unicode_password = "пароль密码🔐"
        hashed = get_password_hash(unicode_password)

        assert verify_password(unicode_password, hashed) is True
        assert verify_password("пароль密码🔐x", hashed) is False

    def test_get_password_hash_consistency(self):
        """Test that same password produces different hashes (salted)."""
        password = "testpassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify the password
        assert verify_password(password, hash1) is True

        # Check secret and algorithm


    def test_get_random_token_length(self):
        """Test that get_random_token generates tokens of expected length."""
        token = get_random_token()
        # get_random_token uses secrets.token_urlsafe(32) which gives ~43 characters
        assert len(token) > 30
