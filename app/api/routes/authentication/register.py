import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash, get_random_token
from app.models.users import Admin, Alumni
from app.schemas.auth import RegisterRequest
from app.services.email_hash_service import is_email_allowed
from app.services.email_service import (
    send_manual_verification_notification,
    send_verification_link_email,
)
from app.services.notification_service import NotificationService
from app.services.verification_service import create_link_verification_record, create_verification_record


# Get logger for this module
logger = logging.getLogger("iu_alumni.auth.register")

BACKEND_URL = __import__("os").getenv("BACKEND_URL", "")

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Register a new alumni user.

    - Email in allowed list + auto verify: send a confirmation link to the user's email.
    - Email in allowed list + manual_verification: notify admins, pending approval.
    - Email NOT in allowed list: always route to manual verification regardless of flag.
    """
    existing_user = db.query(Alumni).filter(Alumni.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    new_user = Alumni(
        id=get_random_token(),
        email=request.email,
        hashed_password=get_password_hash(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        graduation_year=request.graduation_year,
        telegram_alias=request.telegram_alias,
        is_verified=False,
        is_banned=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"Checking if email {request.email} is in the allowed list")
    email_allowed = is_email_allowed(db, request.email)

    alias_display = f"@{new_user.telegram_alias.lstrip('@')}" if new_user.telegram_alias else "Not provided"

    if email_allowed and not request.manual_verification:
        # Auto verification: send confirmation link
        _, token = create_link_verification_record(db, new_user.id)
        verify_url = f"{BACKEND_URL}/auth/verify?token={token}"
        logger.info(f"Sending verification link to {new_user.email}")
        email_sent = await send_verification_link_email(
            new_user.email, new_user.first_name, verify_url
        )
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email. Please try again later.",
            )
        return {
            "message": "Registration successful. Please check your email for a confirmation link.",
            "email": new_user.email,
        }

    # Manual verification path (user requested it, or email not in allowed list)
    create_verification_record(
        db=db,
        alumni_id=new_user.id,
        manual_verification=True,
    )

    not_graduate_note = "" if email_allowed else " (NOT A GRADUATE - email not in allowed list)"
    admin_message = (
        f"🔔 Manual Verification Request\n\n"
        f"Name: {new_user.first_name} {new_user.last_name}{not_graduate_note}\n"
        f"Email: {new_user.email}\n"
        f"Telegram Alias: {alias_display}\n\n"
        f"You can verify this account via the admin dashboard."
    )
    background_tasks.add_task(NotificationService.send_admin_notification, admin_message)

    admins = db.query(Admin).all()
    for admin in admins:
        background_tasks.add_task(
            send_manual_verification_notification,
            admin.email,
            new_user.email,
            f"{new_user.first_name} {new_user.last_name}{not_graduate_note}",
        )

    if not email_allowed:
        return {
            "message": "Registration successful. Your email is not in our graduates list. Your account is pending manual verification by an administrator.",
            "email": new_user.email,
        }

    return {
        "message": "Registration successful. Your account is pending manual verification by an administrator.",
        "email": new_user.email,
    }

