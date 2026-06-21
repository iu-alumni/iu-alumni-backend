"""Unit tests for verification service."""


from datetime import datetime, timedelta

from app.models.email_verification import EmailVerification
from app.models.users import Alumni
from app.services.verification_service import (
    admin_unverify_user,
    admin_verify_user,
    can_resend_verification,
    create_link_verification_record,
    create_verification_record,
    generate_verification_code,
    verify_by_token,
    verify_code,
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
        assert record.verification_token != "old_token"
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

    def test_create_verification_record_existing(self, db_session, mocker):
        """Test updating an existing verification record."""
        existing = EmailVerification(
            id="existing_id",
            alumni_id="test_alumni_id",
            verification_code="000000",
            verification_code_expires=datetime.utcnow() + timedelta(hours=1),
            verification_requested_at=datetime.utcnow(),
            manual_verification_requested=False,
        )
        db_session.add(existing)
        db_session.commit()

        mocker.patch(
            "app.services.verification_service.generate_verification_code",
            return_value="123456",
        )
        fixed_now = datetime.utcnow()
        mock_datetime = mocker.patch("app.services.verification_service.datetime")
        mock_datetime.utcnow.return_value = fixed_now

        record = create_verification_record(db_session, "test_alumni_id", manual_verification=True)

        expected_expires = fixed_now + timedelta(hours=1)
        assert record.alumni_id == "test_alumni_id"
        assert record.verification_code == "123456"
        assert record.verification_code_expires == expected_expires
        assert record.manual_verification_requested is True

    def test_verify_by_token_invalid_token(self, db_session):
        """Test verify_by_token returns false for unknown token."""
        success, message, alumni = verify_by_token(db_session, "invalid-token")

        assert success is False
        assert message == "Invalid or expired verification link"
        assert alumni is None

    def test_verify_by_token_already_verified(self, db_session):
        """Test verify_by_token returns false when token already used."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
        )
        db_session.add(alumni)
        fixed_now = datetime.utcnow()
        record = EmailVerification(
            id="verification123",
            alumni_id=alumni.id,
            verification_token="token123",
            verification_token_expires=fixed_now + timedelta(hours=24),
            verification_requested_at=fixed_now,
            verified_at=fixed_now,
        )
        db_session.add(record)
        db_session.commit()

        success, message, returned_alumni = verify_by_token(db_session, "token123")

        assert success is False
        assert message == "Account already verified"
        assert returned_alumni is None

    def test_verify_by_token_expired_link(self, db_session):
        """Test verify_by_token returns false for expired link."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
        )
        db_session.add(alumni)
        old_time = datetime.utcnow() - timedelta(days=1)
        record = EmailVerification(
            id="verification123",
            alumni_id=alumni.id,
            verification_token="token123",
            verification_token_expires=old_time,
            verification_requested_at=old_time,
        )
        db_session.add(record)
        db_session.commit()

        success, message, returned_alumni = verify_by_token(db_session, "token123")

        assert success is False
        assert message == "Verification link has expired. Please request a new one."
        assert returned_alumni is None

    def test_verify_by_token_user_not_found(self, db_session):
        """Test verify_by_token returns false when the user record is missing."""
        fixed_now = datetime.utcnow()
        record = EmailVerification(
            id="verification123",
            alumni_id="missing_user",
            verification_token="token123",
            verification_token_expires=fixed_now + timedelta(hours=24),
            verification_requested_at=fixed_now,
        )
        db_session.add(record)
        db_session.commit()

        success, message, returned_alumni = verify_by_token(db_session, "token123")

        assert success is False
        assert message == "User not found"
        assert returned_alumni is None

    def test_verify_by_token_success(self, db_session):
        """Test verify_by_token successfully verifies an email."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
        )
        db_session.add(alumni)
        fixed_now = datetime.utcnow()
        record = EmailVerification(
            id="verification123",
            alumni_id=alumni.id,
            verification_token="token123",
            verification_token_expires=fixed_now + timedelta(hours=24),
            verification_requested_at=fixed_now,
        )
        db_session.add(record)
        db_session.commit()

        success, message, returned_alumni = verify_by_token(db_session, "token123")

        assert success is True
        assert message == "Email verified successfully"
        assert returned_alumni is not None
        assert returned_alumni.is_verified is True
        db_session.refresh(record)
        assert record.verification_token is None
        assert record.verified_at is not None

    def test_verify_code_user_not_found(self, db_session):
        """Test verify_code returns false for unknown email."""
        success, message = verify_code(db_session, "unknown@example.com", "123456")

        assert success is False
        assert message == "User not found"

    def test_verify_code_already_verified(self, db_session):
        """Test verify_code returns false when user is already verified."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
            is_verified=True,
        )
        db_session.add(alumni)
        db_session.commit()

        success, message = verify_code(db_session, alumni.email, "123456")

        assert success is False
        assert message == "User already verified"

    def test_verify_code_record_not_found(self, db_session):
        """Test verify_code returns false when no verification record exists."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
        )
        db_session.add(alumni)
        db_session.commit()

        success, message = verify_code(db_session, alumni.email, "123456")

        assert success is False
        assert message == "No verification record found"

    def test_verify_code_no_code_issued(self, db_session):
        """Test verify_code returns false when no code was issued."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
        )
        record = EmailVerification(
            id="verification123",
            alumni_id="user123",
            verification_requested_at=datetime.utcnow(),
        )
        db_session.add(alumni)
        db_session.add(record)
        db_session.commit()

        success, message = verify_code(db_session, alumni.email, "123456")

        assert success is False
        assert message == "No verification code issued for this account"

    def test_verify_code_invalid_code(self, db_session):
        """Test verify_code returns false for incorrect code."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
        )
        record = EmailVerification(
            id="verification123",
            alumni_id=alumni.id,
            verification_code="123456",
            verification_code_expires=datetime.utcnow() + timedelta(hours=1),
            verification_requested_at=datetime.utcnow(),
        )
        db_session.add(alumni)
        db_session.add(record)
        db_session.commit()

        success, message = verify_code(db_session, alumni.email, "654321")

        assert success is False
        assert message == "Invalid verification code"

    def test_verify_code_expired_code(self, db_session):
        """Test verify_code returns false for an expired code."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
        )
        old_time = datetime.utcnow() - timedelta(hours=2)
        record = EmailVerification(
            id="verification123",
            alumni_id=alumni.id,
            verification_code="123456",
            verification_code_expires=old_time,
            verification_requested_at=old_time,
        )
        db_session.add(alumni)
        db_session.add(record)
        db_session.commit()

        success, message = verify_code(db_session, alumni.email, "123456")

        assert success is False
        assert message == "Verification code has expired"

    def test_verify_code_success(self, db_session):
        """Test verify_code successfully verifies a user."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
        )
        record = EmailVerification(
            id="verification123",
            alumni_id=alumni.id,
            verification_code="123456",
            verification_code_expires=datetime.utcnow() + timedelta(hours=1),
            verification_requested_at=datetime.utcnow(),
        )
        db_session.add(alumni)
        db_session.add(record)
        db_session.commit()

        success, message = verify_code(db_session, alumni.email, "123456")

        assert success is True
        assert message == "Email verified successfully"
        db_session.refresh(alumni)
        db_session.refresh(record)
        assert alumni.is_verified is True
        assert record.verified_at is not None

    def test_admin_verify_user_not_found(self, db_session):
        """Test admin_verify_user returns false when the email is missing."""
        success, message = admin_verify_user(db_session, "missing@example.com")

        assert success is False
        assert message == "User not found"

    def test_admin_verify_user_already_verified(self, db_session):
        """Test admin_verify_user does not verify an already verified user."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
            is_verified=True,
        )
        db_session.add(alumni)
        db_session.commit()

        success, message = admin_verify_user(db_session, alumni.email)

        assert success is False
        assert message == "User already verified"

    def test_admin_verify_user_success(self, db_session):
        """Test admin_verify_user successfully verifies a user."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
            is_verified=False,
        )
        record = EmailVerification(
            id="verification123",
            alumni_id=alumni.id,
            verification_requested_at=datetime.utcnow(),
            verified_at=None,
        )
        db_session.add(alumni)
        db_session.add(record)
        db_session.commit()

        success, message = admin_verify_user(db_session, alumni.email)

        assert success is True
        assert message == "User verified successfully"
        db_session.refresh(alumni)
        db_session.refresh(record)
        assert alumni.is_verified is True
        assert record.verified_at is not None

    def test_can_resend_verification_user_not_found(self, db_session):
        """Test can_resend_verification returns false when user is missing."""
        success, message, token = can_resend_verification(db_session, "missing@example.com")

        assert success is False
        assert message == "User not found"
        assert token is None

    def test_can_resend_verification_user_already_verified(self, db_session):
        """Test can_resend_verification returns false for verified user."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
            is_verified=True,
        )
        db_session.add(alumni)
        db_session.commit()

        success, message, token = can_resend_verification(db_session, alumni.email)

        assert success is False
        assert message == "User already verified"
        assert token is None

    def test_can_resend_verification_no_prior_request(self, db_session):
        """Test can_resend_verification allows resend when no prior request exists."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
        )
        db_session.add(alumni)
        db_session.commit()

        success, message, token = can_resend_verification(db_session, alumni.email)

        assert success is True
        assert message == "Can resend"
        assert token == alumni.id

    def test_can_resend_verification_too_soon(self, db_session, mocker):
        """Test can_resend_verification blocks resend too soon."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
            is_verified=False,
        )
        request_time = datetime.utcnow() - timedelta(seconds=30)
        record = EmailVerification(
            id="verification123",
            alumni_id=alumni.id,
            verification_requested_at=request_time,
        )
        db_session.add(alumni)
        db_session.add(record)
        db_session.commit()

        fixed_now = datetime.utcnow()
        mock_datetime = mocker.patch("app.services.verification_service.datetime")
        mock_datetime.utcnow.return_value = fixed_now

        success, message, token = can_resend_verification(db_session, alumni.email)

        assert success is False
        assert "Please wait" in message
        assert token is None

    def test_can_resend_verification_after_wait(self, db_session, mocker):
        """Test can_resend_verification allows resend after waiting enough time."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
            is_verified=False,
        )
        request_time = datetime.utcnow() - timedelta(seconds=120)
        record = EmailVerification(
            id="verification123",
            alumni_id=alumni.id,
            verification_requested_at=request_time,
        )
        db_session.add(alumni)
        db_session.add(record)
        db_session.commit()

        fixed_now = datetime.utcnow()
        mock_datetime = mocker.patch("app.services.verification_service.datetime")
        mock_datetime.utcnow.return_value = fixed_now

        success, message, token = can_resend_verification(db_session, alumni.email)

        assert success is True
        assert message == "Can resend"
        assert token == alumni.id

    def test_admin_unverify_user_not_found(self, db_session):
        """Test admin_unverify_user returns false when the user does not exist."""
        success, message = admin_unverify_user(db_session, "missing@example.com")

        assert success is False
        assert message == "User not found"

    def test_admin_unverify_user_not_verified(self, db_session):
        """Test admin_unverify_user returns false when the user is already unverified."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
            is_verified=False,
        )
        db_session.add(alumni)
        db_session.commit()

        success, message = admin_unverify_user(db_session, alumni.email)

        assert success is False
        assert message == "User is not verified"

    def test_admin_unverify_user_success(self, db_session):
        """Test admin_unverify_user successfully unverifies a user."""
        alumni = Alumni(
            id="user123",
            email="user@example.com",
            hashed_password="hash",
            first_name="First",
            last_name="Last",
            graduation_year="2025",
            is_verified=True,
        )
        record = EmailVerification(
            id="verification123",
            alumni_id=alumni.id,
            verification_requested_at=datetime.utcnow(),
            verified_at=datetime.utcnow(),
        )
        db_session.add(alumni)
        db_session.add(record)
        db_session.commit()

        success, message = admin_unverify_user(db_session, alumni.email)

        assert success is True
        assert message == "User unverified successfully"
        db_session.refresh(alumni)
        db_session.refresh(record)
        assert alumni.is_verified is False
        assert record.verified_at is None

    def test_create_link_verification_record_alumni_not_found(self, db_session, mocker):
        """Test create_link_verification_record when alumni does not exist."""
        mocker.patch("app.services.verification_service.get_random_token", return_value="nonexistent_alumni_id")
        fixed_now = datetime.utcnow()
        mock_datetime = mocker.patch("app.services.verification_service.datetime")
        mock_datetime.utcnow.return_value = fixed_now

        record, token = create_link_verification_record(db_session, "nonexistent_alumni_id")

        expected_expires = fixed_now + timedelta(hours=24)
        assert record.alumni_id == "nonexistent_alumni_id"
        assert record.verification_token == token
        assert record.verification_token_expires == expected_expires

