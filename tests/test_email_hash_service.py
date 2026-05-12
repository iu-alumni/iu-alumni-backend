"""Unit tests for email hash service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.email_hash_service import (
    _check_email_hash_secret,
    hash_email,
    is_email_allowed,
    process_excel_file,
)


class TestEmailHashService:
    """Test cases for email hash service functions."""

    def test_check_email_hash_secret_configured(self, monkeypatch):
        """Test _check_email_hash_secret when configured."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", "test_secret")
        assert _check_email_hash_secret() is True

    def test_check_email_hash_secret_not_configured(self, monkeypatch):
        """Test _check_email_hash_secret when not configured."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", None)
        assert _check_email_hash_secret() is False

    def test_hash_email_success(self, monkeypatch):
        """Test hash_email with valid secret."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", "test_secret")
        email = "test@example.com"
        hashed = hash_email(email)
        assert isinstance(hashed, str)
        assert len(hashed) == 64

    def test_hash_email_no_secret(self, monkeypatch):
        """Test hash_email without secret."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", None)
        with pytest.raises(ValueError, match="EMAIL_HASH_SECRET not configured"):
            hash_email("test@example.com")

    def test_hash_email_normalization(self, monkeypatch):
        """Test email normalization in hash_email."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", "test_secret")
        email1 = "Test@Example.Com"
        email2 = "test@example.com"
        hashed1 = hash_email(email1)
        hashed2 = hash_email(email2)
        assert hashed1 == hashed2

    def test_is_email_allowed_allowed(self, monkeypatch, db_session):
        """Test is_email_allowed when email is allowed."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", "test_secret")

        with patch("app.services.email_hash_service.hash_email", return_value="test_hash"):
            from app.models.allowed_emails import AllowedEmail

            allowed = AllowedEmail(id="allowed_id", hashed_email="test_hash")
            db_session.add(allowed)
            db_session.commit()

            result = is_email_allowed(db_session, "test@example.com")
            assert result is True

    def test_is_email_allowed_not_allowed(self, monkeypatch, db_session):
        """Test is_email_allowed when email is not allowed."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", "test_secret")

        with patch("app.services.email_hash_service.hash_email", return_value="test_hash"):
            result = is_email_allowed(db_session, "test@example.com")
            assert result is False

    def test_is_email_allowed_no_secret(self, monkeypatch, db_session):
        """Test is_email_allowed without secret."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", None)

        result = is_email_allowed(db_session, "test@example.com")
        assert result is False

    def test_is_email_allowed_exception(self, monkeypatch, db_session):
        """Test is_email_allowed with exception."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", "test_secret")

        with patch("app.services.email_hash_service.hash_email", side_effect=Exception("Test error")):
            result = is_email_allowed(db_session, "test@example.com")
            assert result is False

    def test_process_excel_file_success(self, monkeypatch, db_session, mocker):
        """Test process_excel_file with valid data."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", "test_secret")

        mock_df = MagicMock()
        mock_df.shape = (2, 1)
        mock_df.iloc.__getitem__.return_value.tolist.return_value = ["test1@example.com", "test2@example.com"]

        mock_pd = mocker.patch("app.services.email_hash_service.pd")
        mock_pd.read_excel.return_value = mock_df

        mock_hash = mocker.patch("app.services.email_hash_service.hash_email")
        mock_hash.side_effect = ["hash1", "hash2"]

        result = process_excel_file(db_session, b"fake_excel_data")

        assert result["success"] is True
        assert "Successfully processed 2 emails" in result["message"]

    def test_process_excel_file_no_secret(self, monkeypatch, db_session):
        """Test process_excel_file without secret."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", None)

        result = process_excel_file(db_session, b"fake_excel_data")

        assert result["success"] is False
        assert "EMAIL_HASH_SECRET not configured" in result["message"]

    def test_process_excel_file_invalid_excel(self, monkeypatch, db_session, mocker):
        """Test process_excel_file with invalid Excel."""
        monkeypatch.setattr("app.services.email_hash_service.EMAIL_HASH_SECRET", "test_secret")

        mock_pd = mocker.patch("app.services.email_hash_service.pd")
        mock_pd.read_excel.side_effect = Exception("Invalid Excel")

        result = process_excel_file(db_session, b"invalid_excel_data")

        assert result["success"] is False
        assert "Invalid Excel" in result["message"]
