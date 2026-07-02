import logging
import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.users import Alumni
from app.schemas.auth import ResendVerificationRequest
from app.services.email_service import send_verification_link_email
from app.services.verification_service import (
    can_resend_verification,
    create_link_verification_record,
)


BACKEND_URL = os.getenv("BACKEND_URL", "")
logger = logging.getLogger("iu_alumni.auth.resend_verification")

router = APIRouter()


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification_link(
    request: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Resend email verification link. Rate-limited to once per 60 seconds.
    """
    logger.info("Resend verification requested for email=%s", request.email)
    can_resend, message, _alumni_id = can_resend_verification(db, request.email)

    if not can_resend:
        logger.warning(
            "Resend verification denied for email=%s reason=%s", request.email, message
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    user = db.query(Alumni).filter(Alumni.email == request.email).first()
    if not user:
        logger.warning(
            "Resend verification failed: user not found after can_resend check email=%s",
            request.email,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    _, token = create_link_verification_record(db, user.id)
    verify_url = f"{BACKEND_URL}/api/v1/auth/verify?token={token}"
    logger.info(
        "Resend verification token issued: user_id=%s email=%s verification_url_base=%s",
        user.id,
        user.email,
        BACKEND_URL,
    )

    background_tasks.add_task(
        send_verification_link_email,
        user.email,
        user.first_name,
        verify_url,
    )
    logger.info(
        "Resend verification email scheduled in background: user_id=%s email=%s",
        user.id,
        user.email,
    )

    return {"message": "A new verification link has been sent to your email", "email": user.email}
