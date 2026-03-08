from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.password_reset_token import PasswordResetToken
from app.schemas.auth import PasswordResetConfirmSchema


router = APIRouter()

PASSWORD_RESET_MAX_ATTEMPTS = 5


@router.post("/password-reset/confirm", status_code=200)
def password_reset_confirm(
    request: PasswordResetConfirmSchema,
    db: Session = Depends(get_db),
):
    """Confirm password reset using the token from the emailed link.

    Invalidated after 5 wrong attempts or expiry.
    """
    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == request.token)
        .first()
    )

    if not reset_token or reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used reset token",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if reset_token.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    if reset_token.attempts >= PASSWORD_RESET_MAX_ATTEMPTS:
        reset_token.used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Please request a new reset link",
        )

    # Token is valid — update password
    user = reset_token.alumni
    user.hashed_password = get_password_hash(request.new_password)
    reset_token.used = True
    db.commit()

    return {"message": "Password updated successfully"}
