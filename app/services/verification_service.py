from datetime import datetime, timedelta
import os
import random
import secrets
import string

from sqlalchemy.orm import Session

from app.core.security import get_random_token
from app.models.email_verification import EmailVerification
from app.models.users import Alumni


VERIFICATION_LINK_EXPIRY_HOURS = int(os.getenv("VERIFICATION_LINK_EXPIRY_HOURS", "24"))


def generate_verification_code() -> str:
    """Generate a 6-digit verification code"""
    return "".join(random.choices(string.digits, k=6))


def create_link_verification_record(
    db: Session, alumni_id: str
) -> tuple[EmailVerification, str]:
    """
    Create or update a link-based email verification record.

    Returns:
        tuple: (EmailVerification record, raw token string)
    """
    token = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    expires = now + timedelta(hours=VERIFICATION_LINK_EXPIRY_HOURS)

    existing = (
        db.query(EmailVerification)
        .filter(EmailVerification.alumni_id == alumni_id)
        .first()
    )

    if existing:
        existing.verification_token = token
        existing.verification_token_expires = expires
        existing.verification_requested_at = now
        existing.verified_at = None
        db.commit()
        db.refresh(existing)
        return existing, token

    record = EmailVerification(
        id=get_random_token(),
        alumni_id=alumni_id,
        verification_token=token,
        verification_token_expires=expires,
        verification_requested_at=now,
        manual_verification_requested=False,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, token


def verify_by_token(db: Session, token: str) -> tuple[bool, str, Alumni | None]:
    """
    Verify a user via their email verification token.

    Returns:
        tuple: (success, message, alumni_or_None)
    """
    record = (
        db.query(EmailVerification)
        .filter(EmailVerification.verification_token == token)
        .first()
    )

    if not record:
        return False, "Invalid or expired verification link", None

    if record.verified_at is not None:
        return False, "Account already verified", None

    if record.verification_token_expires is None or datetime.utcnow() > record.verification_token_expires:
        return False, "Verification link has expired. Please request a new one.", None

    alumni = db.query(Alumni).filter(Alumni.id == record.alumni_id).first()
    if not alumni:
        return False, "User not found", None

    alumni.is_verified = True
    record.verified_at = datetime.utcnow()
    record.verification_token = None  # invalidate
    db.commit()

    return True, "Email verified successfully", alumni


def create_verification_record(
    db: Session, alumni_id: str, manual_verification: bool = False
) -> EmailVerification:
    """
    Create a new email verification record (legacy code path used for manual verification).
    """
    existing = (
        db.query(EmailVerification)
        .filter(EmailVerification.alumni_id == alumni_id)
        .first()
    )

    now = datetime.utcnow()
    if existing:
        existing.verification_code = generate_verification_code()
        existing.verification_code_expires = now + timedelta(hours=1)
        existing.verification_requested_at = now
        existing.manual_verification_requested = manual_verification
        existing.verified_at = None
        db.commit()
        db.refresh(existing)
        return existing

    verification = EmailVerification(
        id=get_random_token(),
        alumni_id=alumni_id,
        verification_code=generate_verification_code(),
        verification_code_expires=now + timedelta(hours=1),
        verification_requested_at=now,
        manual_verification_requested=manual_verification,
    )

    db.add(verification)
    db.commit()
    db.refresh(verification)

    return verification


def verify_code(db: Session, email: str, code: str) -> tuple[bool, str]:
    """
    Verify the provided verification code (used by admin-verify path).
    """
    alumni = db.query(Alumni).filter(Alumni.email == email).first()
    if not alumni:
        return False, "User not found"

    if alumni.is_verified:
        return False, "User already verified"

    verification = (
        db.query(EmailVerification)
        .filter(EmailVerification.alumni_id == alumni.id)
        .first()
    )

    if not verification:
        return False, "No verification record found"

    if not verification.verification_code:
        return False, "No verification code issued for this account"

    if verification.verification_code != code:
        return False, "Invalid verification code"

    if verification.verification_code_expires and datetime.utcnow() > verification.verification_code_expires:
        return False, "Verification code has expired"

    alumni.is_verified = True
    verification.verified_at = datetime.utcnow()
    db.commit()

    return True, "Email verified successfully"


def admin_verify_user(db: Session, email: str) -> tuple[bool, str]:
    """Admin manual verification of a user."""
    alumni = db.query(Alumni).filter(Alumni.email == email).first()
    if not alumni:
        return False, "User not found"

    if alumni.is_verified:
        return False, "User already verified"

    alumni.is_verified = True

    verification = (
        db.query(EmailVerification)
        .filter(EmailVerification.alumni_id == alumni.id)
        .first()
    )
    if verification:
        verification.verified_at = datetime.utcnow()

    db.commit()
    return True, "User verified successfully"


def can_resend_verification(db: Session, email: str) -> tuple[bool, str, str | None]:
    """Check if user can request a new verification link."""
    alumni = db.query(Alumni).filter(Alumni.email == email).first()
    if not alumni:
        return False, "User not found", None

    if alumni.is_verified:
        return False, "User already verified", None

    verification = (
        db.query(EmailVerification)
        .filter(EmailVerification.alumni_id == alumni.id)
        .first()
    )

    if verification:
        time_since_last_request = datetime.utcnow() - verification.verification_requested_at
        if time_since_last_request < timedelta(seconds=60):
            seconds_to_wait = 60 - time_since_last_request.total_seconds()
            return (
                False,
                f"Please wait {int(seconds_to_wait)} seconds before requesting a new link",
                None,
            )

    return True, "Can resend", alumni.id


def admin_unverify_user(db: Session, email: str) -> tuple[bool, str]:
    """Admin unverification of a user."""
    alumni = db.query(Alumni).filter(Alumni.email == email).first()
    if not alumni:
        return False, "User not found"

    if not alumni.is_verified:
        return False, "User is not verified"

    alumni.is_verified = False

    verification = (
        db.query(EmailVerification)
        .filter(EmailVerification.alumni_id == alumni.id)
        .first()
    )
    if verification:
        verification.verified_at = None

    db.commit()
    return True, "User unverified successfully"

