import random
import string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.email_verification import EmailVerification
from app.models.users import Alumni
from app.core.security import get_random_token

def generate_verification_code() -> str:
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def create_verification_record(
    db: Session,
    alumni_id: str,
    manual_verification: bool = False
) -> EmailVerification:
    """
    Create a new email verification record
    
    Args:
        db: Database session
        alumni_id: ID of the alumni user
        manual_verification: Whether manual verification was requested
        
    Returns:
        EmailVerification: Created verification record
    """
    # Check if verification record already exists
    existing = db.query(EmailVerification).filter(
        EmailVerification.alumni_id == alumni_id
    ).first()
    
    if existing:
        # Update existing record with new code
        existing.verification_code = generate_verification_code()
        existing.verification_code_expires = datetime.utcnow() + timedelta(hours=1)
        existing.verification_requested_at = datetime.utcnow()
        existing.manual_verification_requested = manual_verification
        existing.verified_at = None
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new verification record
    verification = EmailVerification(
        id=get_random_token(),
        alumni_id=alumni_id,
        verification_code=generate_verification_code(),
        verification_code_expires=datetime.utcnow() + timedelta(hours=1),
        verification_requested_at=datetime.utcnow(),
        manual_verification_requested=manual_verification
    )
    
    db.add(verification)
    db.commit()
    db.refresh(verification)
    
    return verification

def verify_code(
    db: Session,
    email: str,
    code: str
) -> tuple[bool, str]:
    """
    Verify the provided verification code
    
    Args:
        db: Database session
        email: User's email
        code: Verification code to check
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Get the alumni record
    alumni = db.query(Alumni).filter(Alumni.email == email).first()
    if not alumni:
        return False, "User not found"
    
    if alumni.is_verified:
        return False, "User already verified"
    
    # Get verification record
    verification = db.query(EmailVerification).filter(
        EmailVerification.alumni_id == alumni.id
    ).first()
    
    if not verification:
        return False, "No verification record found"
    
    # Check if code matches
    if verification.verification_code != code:
        return False, "Invalid verification code"
    
    # Check if code has expired
    if datetime.utcnow() > verification.verification_code_expires:
        return False, "Verification code has expired"
    
    # Mark as verified
    alumni.is_verified = True
    verification.verified_at = datetime.utcnow()
    
    db.commit()
    
    return True, "Email verified successfully"

def admin_verify_user(
    db: Session,
    email: str
) -> tuple[bool, str]:
    """
    Admin manual verification of a user
    
    Args:
        db: Database session
        email: User's email to verify
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Get the alumni record
    alumni = db.query(Alumni).filter(Alumni.email == email).first()
    if not alumni:
        return False, "User not found"
    
    if alumni.is_verified:
        return False, "User already verified"
    
    # Mark as verified
    alumni.is_verified = True
    
    # Update verification record if exists
    verification = db.query(EmailVerification).filter(
        EmailVerification.alumni_id == alumni.id
    ).first()
    
    if verification:
        verification.verified_at = datetime.utcnow()
    
    db.commit()
    
    return True, "User verified successfully"

def can_resend_verification(
    db: Session,
    email: str
) -> tuple[bool, str, Optional[str]]:
    """
    Check if user can request a new verification code
    
    Args:
        db: Database session
        email: User's email
        
    Returns:
        tuple: (can_resend: bool, message: str, alumni_id: Optional[str])
    """
    # Get the alumni record
    alumni = db.query(Alumni).filter(Alumni.email == email).first()
    if not alumni:
        return False, "User not found", None
    
    if alumni.is_verified:
        return False, "User already verified", None
    
    # Check if verification record exists
    verification = db.query(EmailVerification).filter(
        EmailVerification.alumni_id == alumni.id
    ).first()
    
    if verification:
        # Check rate limiting - allow resend after 60 seconds
        time_since_last_request = datetime.utcnow() - verification.verification_requested_at
        if time_since_last_request < timedelta(seconds=60):
            seconds_to_wait = 60 - time_since_last_request.total_seconds()
            return False, f"Please wait {int(seconds_to_wait)} seconds before requesting a new code", None
    
    return True, "Can resend", alumni.id

def admin_unverify_user(
    db: Session,
    email: str
) -> tuple[bool, str]:
    """
    Admin unverification of a user
    
    Args:
        db: Database session
        email: User's email to unverify
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Get the alumni record
    alumni = db.query(Alumni).filter(Alumni.email == email).first()
    if not alumni:
        return False, "User not found"
    
    if not alumni.is_verified:
        return False, "User is not verified"
    
    # Mark as unverified
    alumni.is_verified = False
    
    # Update verification record if exists
    verification = db.query(EmailVerification).filter(
        EmailVerification.alumni_id == alumni.id
    ).first()
    
    if verification:
        verification.verified_at = None
    
    db.commit()
    
    return True, "User unverified successfully"