from datetime import datetime, timedelta, timezone
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

    if user:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

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
            # Still return 200 — don't reveal whether email exists or is rate-limited
            return {"message": "If that email is registered, a reset link has been sent"}

        # Invalidate any existing unused tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.alumni_id == user.id,
            PasswordResetToken.used.is_(False),
        ).delete()

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

        reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
        background_tasks.add_task(
            send_password_reset_email,
            email=user.email,
            first_name=user.first_name,
            reset_link=reset_link,
            expiry_minutes=PASSWORD_RESET_EXPIRY_MINUTES,
        )

    return {"message": "If that email is registered, a reset link has been sent"}
