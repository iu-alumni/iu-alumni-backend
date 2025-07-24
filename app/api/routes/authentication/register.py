import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.utils.notifications import notify_admin_manual_verification
from app.core.database import get_db
from app.core.security import get_password_hash, get_random_token
from app.models.users import Admin, Alumni
from app.schemas.auth import RegisterRequest
from app.services.email_hash_service import is_email_allowed
from app.services.email_service import (
    send_manual_verification_notification,
    send_verification_email,
)
from app.services.verification_service import create_verification_record


# Get logger for this module
logger = logging.getLogger("iu_alumni.auth.register")


router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Register a new alumni user with email verification.

    Logic:
    Case 1 - Email is in allowed list:
    - If manual_verification=False: send verification code to email
    - If manual_verification=True: request manual verification from admin

    Case 2 - Email is NOT in allowed list:
    - Regardless of manual_verification choice: request manual verification from admin
    - Admin is notified that user is not a graduate (email not in list)
    - No verification code is sent

    User must verify email with code OR get admin approval to complete registration
    """
    # Check if email already exists
    existing_user = db.query(Alumni).filter(Alumni.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new alumni user (unverified)
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

    # Check if email is in the allowed list
    logger.info(f"Checking if email {request.email} is in the allowed list")
    email_allowed = is_email_allowed(db, request.email)

    # Create verification record
    logger.info(f"Creating verification record for {new_user.email}")
    verification = create_verification_record(
        db=db,
        alumni_id=new_user.id,
        manual_verification=request.manual_verification or not email_allowed,
    )
    logger.info(f"Verification record created: {verification}")

    # Case 1: Email is in allowed list
    if email_allowed:
        if request.manual_verification:
            # User requested manual verification even though email is allowed
            logger.info(
                f"User {request.email} requested manual verification (email is in allowed list)"
            )

            # Send Telegram notification to admins
            background_tasks.add_task(
                notify_admin_manual_verification,
                new_user.email,
                f"{new_user.first_name} {new_user.last_name}",
                new_user.telegram_alias,
            )

            # Also send email notifications to admins as backup
            admins = db.query(Admin).all()
            for admin in admins:
                background_tasks.add_task(
                    send_manual_verification_notification,
                    admin.email,
                    new_user.email,
                    f"{new_user.first_name} {new_user.last_name}",
                )

            return {
                "message": "Registration successful. Your account is pending manual verification by an administrator.",
                "email": new_user.email,
            }
        # Send verification code to email
        logger.info(
            f"Sending verification email to {new_user.email} (email is in allowed list)"
        )
        await send_verification_email(
            new_user.email, new_user.first_name, verification.verification_code
        )
        logger.info(f"Verification email sent to {new_user.email}")
        return {
            "message": "Registration successful. Please check your email for verification code.",
            "email": new_user.email,
        }

    # Case 2: Email is NOT in allowed list
    logger.info(
        f"Email {request.email} is NOT in allowed list - requesting manual verification"
    )

    # Send Telegram notification to admins with note about non-graduate status
    background_tasks.add_task(
        notify_admin_manual_verification,
        new_user.email,
        f"{new_user.first_name} {new_user.last_name} (NOT A GRADUATE - email not in allowed list)",
        new_user.telegram_alias,
    )

    # Also send email notifications to admins as backup
    admins = db.query(Admin).all()
    for admin in admins:
        background_tasks.add_task(
            send_manual_verification_notification,
            admin.email,
            new_user.email,
            f"{new_user.first_name} {new_user.last_name} (NOT A GRADUATE - email not in allowed list)",
        )

    return {
        "message": "Registration successful. Your email is not in our graduates list. Your account is pending manual verification by an administrator.",
        "email": new_user.email,
    }
