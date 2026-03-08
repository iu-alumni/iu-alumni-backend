import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.login_code import LoginCode
from app.models.users import Alumni
from app.schemas.auth import LoginInitResponse, LoginOTPRequest, LoginVerifyRequest, TokenResponse
from app.services.email_service import send_login_code_email
from app.services.verification_service import generate_verification_code


router = APIRouter()

LOGIN_CODE_EXPIRY_MINUTES = int(os.getenv("LOGIN_CODE_EXPIRY_MINUTES", "10"))


@router.post("/login/otp/request", response_model=LoginInitResponse)
async def login_otp_request(request: LoginOTPRequest, db: Session = Depends(get_db)):
    """
    OTP login step 1: validate email + password, then send a 6-digit code to
    the university email. Returns a session_token for use in /login/otp/verify.
    This is an alternative to the standard /login endpoint.
    """
    user = db.query(Alumni).filter(Alumni.email == request.email).first()

    if (
        not user
        or not user.hashed_password
        or not verify_password(request.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not verified"
        )

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is banned"
        )

    # Invalidate any previous unused codes for this user
    db.query(LoginCode).filter(
        LoginCode.alumni_id == user.id, LoginCode.used.is_(False)
    ).delete()

    code = generate_verification_code()
    session_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        minutes=LOGIN_CODE_EXPIRY_MINUTES
    )

    db.add(LoginCode(
        id=str(uuid.uuid4()),
        alumni_id=user.id,
        session_token=session_token,
        code=code,
        expires_at=expires_at,
        used=False,
    ))
    db.commit()

    await send_login_code_email(
        email=user.email,
        first_name=user.first_name,
        code=code,
        expiry_minutes=LOGIN_CODE_EXPIRY_MINUTES,
    )

    return LoginInitResponse(
        session_token=session_token,
        message=f"A verification code has been sent to {request.email}",
    )


@router.post("/login/otp/verify", response_model=TokenResponse)
def login_otp_verify(request: LoginVerifyRequest, db: Session = Depends(get_db)):
    """
    OTP login step 2: submit the session_token and 6-digit code received by
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

    login_code.used = True
    db.commit()

    user = login_code.alumni
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "user_type": "alumni"}
    )
    return TokenResponse(access_token=access_token, token_type="bearer")
