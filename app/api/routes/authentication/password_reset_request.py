from datetime import UTC, datetime, timedelta
import logging
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.password_reset_token import PasswordResetToken
from app.models.users import Alumni
from app.schemas.auth import PasswordResetRequestSchema
from app.services.email_service import send_password_reset_email


router = APIRouter()
logger = logging.getLogger("iu_alumni.auth.password_reset")

PASSWORD_RESET_EXPIRY_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRY_MINUTES", "30"))
PASSWORD_RESET_COOLDOWN_SECONDS = 60
FRONTEND_URL = os.getenv("MINI_APP_URL", "")


@router.post("/password-reset/request", status_code=200)
async def password_reset_request(
    request: PasswordResetRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Request a password reset link. Always returns 200 to prevent email enumeration.

    Rate-limited to one request per 60 seconds per account.
    """
    user = db.query(Alumni).filter(Alumni.email == request.email).first()
    logger.info(
        "Password reset requested for email=%s user_exists=%s",
        request.email,
        bool(user),
    )

    if user:
        now = datetime.now(UTC).replace(tzinfo=None)

        # Cooldown: reject if a token was issued less than 60 seconds ago
        recent = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.alumni_id == user.id,
                PasswordResetToken.used.is_(False),
            )
            .order_by(PasswordResetToken.created_at.desc())
            .first()
        )
        if recent and (now - recent.created_at) < timedelta(seconds=PASSWORD_RESET_COOLDOWN_SECONDS):
            seconds_left = PASSWORD_RESET_COOLDOWN_SECONDS - int(
                (now - recent.created_at).total_seconds()
            )
            logger.info(
                "Password reset rate-limited: user_id=%s email=%s seconds_left=%s last_created_at=%s",
                user.id,
                user.email,
                seconds_left,
                recent.created_at,
            )
            # Still return 200 — don't reveal whether email exists or is rate-limited
            return {"message": "If that email is registered, a reset link has been sent"}

        # Invalidate any existing unused tokens
        invalidated_count = db.query(PasswordResetToken).filter(
            PasswordResetToken.alumni_id == user.id,
            PasswordResetToken.used.is_(False),
        ).delete()
        logger.info(
            "Password reset cleanup: user_id=%s email=%s invalidated_unused_tokens=%s",
            user.id,
            user.email,
            invalidated_count,
        )

        token = str(uuid.uuid4())
        reset_token = PasswordResetToken(
            id=str(uuid.uuid4()),
            alumni_id=user.id,
            token=token,
            expires_at=now + timedelta(minutes=PASSWORD_RESET_EXPIRY_MINUTES),
            used=False,
            created_at=now,
            attempts=0,
        )
        db.add(reset_token)
        db.commit()
        logger.info(
            "Password reset token persisted: user_id=%s email=%s token_id=%s expires_at=%s",
            user.id,
            user.email,
            reset_token.id,
            reset_token.expires_at,
        )

        reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
        background_tasks.add_task(
            send_password_reset_email,
            email=user.email,
            first_name=user.first_name,
            reset_link=reset_link,
            expiry_minutes=PASSWORD_RESET_EXPIRY_MINUTES,
        )
        logger.info(
            "Password reset email scheduled in background: user_id=%s email=%s token_id=%s",
            user.id,
            user.email,
            reset_token.id,
        )
    else:
        logger.info(
            "Password reset completed with opaque response for non-existing email=%s",
            request.email,
        )

    return {"message": "If that email is registered, a reset link has been sent"}
