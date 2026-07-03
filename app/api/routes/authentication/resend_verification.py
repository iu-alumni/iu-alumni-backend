import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.url_utils import build_absolute_url
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
    http_request: Request,
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
    verify_url = build_absolute_url(
        f"/api/v1/auth/verify?token={token}",
        request=http_request,
        configured_base=BACKEND_URL,
    )
    logger.info(
        "Resend verification token issued: user_id=%s email=%s verification_url_base=%s",
        user.id,
        user.email,
        BACKEND_URL,
    )

    email_sent = await send_verification_link_email(
        user.email,
        user.first_name,
        verify_url,
    )
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later.",
        )
    logger.info(
        "Resend verification email sent: user_id=%s email=%s",
        user.id,
        user.email,
    )

    return {"message": "A new verification link has been sent to your email", "email": user.email}
