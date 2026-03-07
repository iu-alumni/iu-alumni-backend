import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.email_verification import EmailVerification
from app.models.users import Admin, Alumni
from app.schemas.auth import ResendVerificationRequest
from app.services.email_service import send_manual_verification_notification
from app.services.notification_service import NotificationService


# Get logger for this module
logger = logging.getLogger("iu_alumni.auth.manual_verification")


router = APIRouter()


@router.post("/request-manual-verification", status_code=status.HTTP_200_OK)
async def request_manual_verification(
    request: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Request manual verification for a user who already registered but can't access their email.

    This is for users who initially tried to get email verification code but then realized
    they don't have access to their email.
    """
    # Check if user exists
    user = db.query(Alumni).filter(Alumni.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if user is already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already verified"
        )

    # Check if there's an existing verification record
    verification = (
        db.query(EmailVerification)
        .filter(EmailVerification.alumni_id == user.id)
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No verification record found"
        )

    # Update verification record to manual verification
    verification.manual_verification = True
    db.commit()

    logger.info(
        f"User {request.email} requested manual verification after initial registration"
    )

    # Send Telegram notification to admins
    alias_display = f"@{user.telegram_alias.lstrip('@')}" if user.telegram_alias else "Not provided"
    admin_message = (
        f"🔔 Manual Verification Request\n\n"
        f"Name: {user.first_name} {user.last_name} (REQUESTED MANUAL VERIFICATION - no email access)\n"
        f"Email: {user.email}\n"
        f"Telegram Alias: {alias_display}\n\n"
        f"You can verify this account via the admin dashboard."
    )
    background_tasks.add_task(NotificationService.send_admin_notification, admin_message)

    # Also send email notifications to admins as backup
    admins = db.query(Admin).all()
    for admin in admins:
        background_tasks.add_task(
            send_manual_verification_notification,
            admin.email,
            user.email,
            f"{user.first_name} {user.last_name} (REQUESTED MANUAL VERIFICATION - no email access)",
        )

    return {
        "message": "Manual verification request submitted. An administrator will review your account.",
        "email": user.email,
    }
