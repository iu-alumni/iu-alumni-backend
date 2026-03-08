from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.login_code import LoginCode
from app.schemas.auth import LoginVerifyRequest, TokenResponse


router = APIRouter()


@router.post("/login/verify", response_model=TokenResponse)
def login_verify(request: LoginVerifyRequest, db: Session = Depends(get_db)):
    """
    Step 2 of login: submit the session_token and 6-digit code received by
    email. Returns the full JWT on success.
    """
    login_code = (
        db.query(LoginCode)
        .filter(LoginCode.session_token == request.session_token)
        .first()
    )

    if not login_code or login_code.used:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if login_code.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification code has expired",
        )

    if login_code.code != request.code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect verification code",
        )

    # Mark code as used
    login_code.used = True
    db.commit()

    user = login_code.alumni
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "user_type": "alumni"}
    )
    return TokenResponse(access_token=access_token, token_type="bearer")
