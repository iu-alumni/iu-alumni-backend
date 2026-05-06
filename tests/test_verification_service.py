"""Unit tests for verification service."""


from datetime import datetime, timedelta

from app.services.verification_service import (
    create_link_verification_record,
    create_verification_record,
    generate_verification_code,
)


class TestVerificationService:
    """Test cases for verification service functions."""

    def test_generate_verification_code(self):
        """Test that verification code is 6 digits."""
        code = generate_verification_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_create_link_verification_record_new(self, db_session, mocker):
        """Test creating a new link verification record."""
        mocker.patch("app.services.verification_service.get_random_token", return_value="test_alumni_id")
        fixed_now = datetime.utcnow()
        mock_datetime = mocker.patch("app.services.verification_service.datetime")
        mock_datetime.utcnow.return_value = fixed_now

        record, token = create_link_verification_record(db_session, "test_alumni_id")

        expected_expires = fixed_now + timedelta(hours=24)
        assert record.alumni_id == "test_alumni_id"
        assert record.verification_token == token
        assert record.verification_token_expires == expected_expires

    def test_create_link_verification_record_existing(self, db_session, mocker):
        """Test updating an existing link verification record."""
        from app.models.email_verification import EmailVerification

        existing = EmailVerification(
            id="existing_id",
            alumni_id="test_alumni_id",
            verification_token="old_token",
            verification_token_expires=None,
            verification_requested_at=datetime.utcnow(),
            manual_verification_requested=False,
        )
        db_session.add(existing)
        db_session.commit()

        fixed_now = datetime.utcnow()
        mock_datetime = mocker.patch("app.services.verification_service.datetime")
        mock_datetime.utcnow.return_value = fixed_now

        record, token = create_link_verification_record(db_session, "test_alumni_id")

        expected_expires = fixed_now + timedelta(hours=24)
        assert record.alumni_id == "test_alumni_id"
        assert record.verification_token == token
        assert record.verification_token != "old_token"  # Token should be replaced
        assert record.verification_token_expires == expected_expires

    def test_create_verification_record(self, db_session, mocker):
        """Test creating a verification record with code."""
        mocker.patch(
            "app.services.verification_service.generate_verification_code",
            return_value="123456",
        )
        fixed_now = datetime.utcnow()
        mock_datetime = mocker.patch("app.services.verification_service.datetime")
        mock_datetime.utcnow.return_value = fixed_now

        record = create_verification_record(db_session, "test_alumni_id")

        expected_expires = fixed_now + timedelta(hours=1)
        assert record.alumni_id == "test_alumni_id"
        assert record.verification_code == "123456"
        assert record.verification_code_expires == expected_expires

    def test_create_link_verification_record_alumni_not_found(self, db_session, mocker):
        """Test create_link_verification_record when alumni does not exist."""
        # This test verifies that the function still works even if alumni doesn't exist
        # (since the function doesn't validate alumni existence)
        mocker.patch("app.services.verification_service.get_random_token", return_value="nonexistent_alumni_id")
        fixed_now = datetime.utcnow()
        mock_datetime = mocker.patch("app.services.verification_service.datetime")
        mock_datetime.utcnow.return_value = fixed_now

        record, token = create_link_verification_record(db_session, "nonexistent_alumni_id")

        expected_expires = fixed_now + timedelta(hours=24)
        assert record.alumni_id == "nonexistent_alumni_id"
        assert record.verification_token == token
        assert record.verification_token_expires == expected_expires

