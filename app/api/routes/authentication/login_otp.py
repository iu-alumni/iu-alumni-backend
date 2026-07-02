from datetime import UTC, datetime, timedelta
import logging
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.login_code import LoginCode
from app.models.users import Alumni
from app.schemas.auth import (
    LoginInitResponse,
    LoginOTPRequest,
    LoginVerifyRequest,
    TokenResponse,
)
from app.services.email_service import send_login_code_email
from app.services.verification_service import generate_verification_code


router = APIRouter()
logger = logging.getLogger("iu_alumni.auth.login_otp")

LOGIN_CODE_EXPIRY_MINUTES = int(os.getenv("LOGIN_CODE_EXPIRY_MINUTES", "10"))
OTP_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5


@router.post("/login/otp/request", response_model=LoginInitResponse)
async def login_otp_request(request: LoginOTPRequest, db: Session = Depends(get_db)):
    """OTP login step 1: validate email, send a 6-digit code to the university email.

    Returns a session_token for use in /login/otp/verify.
    Rate-limited: one code per 60 seconds per account.
    """
    user = db.query(Alumni).filter(Alumni.email == request.email).first()

    if not user:
        logger.warning("OTP request rejected: account not found for email=%s", request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email",
        )

    if not user.is_verified:
        logger.warning(
            "OTP request rejected: account not verified for user_id=%s email=%s",
            user.id,
            user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not verified"
        )

    if user.is_banned:
        logger.warning(
            "OTP request rejected: account banned for user_id=%s email=%s",
            user.id,
            user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is banned"
        )

    now = datetime.now(UTC).replace(tzinfo=None)

    # Cooldown: reject if a code was issued less than 60 seconds ago
    recent = (
        db.query(LoginCode)
        .filter(LoginCode.alumni_id == user.id, LoginCode.used.is_(False))
        .order_by(LoginCode.created_at.desc())
        .first()
    )
    if recent and (now - recent.created_at) < timedelta(seconds=OTP_COOLDOWN_SECONDS):
        seconds_left = OTP_COOLDOWN_SECONDS - int((now - recent.created_at).total_seconds())
        logger.info(
            "OTP request rate-limited: user_id=%s email=%s seconds_left=%s last_created_at=%s",
            user.id,
            user.email,
            seconds_left,
            recent.created_at,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {seconds_left} seconds before requesting a new code",
        )

    # Invalidate previous unused codes
    invalidated_count = db.query(LoginCode).filter(
        LoginCode.alumni_id == user.id, LoginCode.used.is_(False)
    ).delete()
    logger.info(
        "OTP request cleanup: user_id=%s email=%s invalidated_unused_codes=%s",
        user.id,
        user.email,
        invalidated_count,
    )

    code = generate_verification_code()
    session_token = str(uuid.uuid4())

    db.add(LoginCode(
        id=str(uuid.uuid4()),
        alumni_id=user.id,
        session_token=session_token,
        code=code,
        expires_at=now + timedelta(minutes=LOGIN_CODE_EXPIRY_MINUTES),
        created_at=now,
        used=False,
        attempts=0,
    ))
    db.commit()
    logger.info(
        "OTP code persisted: user_id=%s email=%s session_token=%s expires_at=%s",
        user.id,
        user.email,
        session_token,
        now + timedelta(minutes=LOGIN_CODE_EXPIRY_MINUTES),
    )

    email_sent = await send_login_code_email(
        email=user.email,
        first_name=user.first_name,
        code=code,
        expiry_minutes=LOGIN_CODE_EXPIRY_MINUTES,
    )

    if not email_sent:
        logger.error(
            "OTP email send failed: user_id=%s email=%s session_token=%s",
            user.id,
            user.email,
            session_token,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send login code. Please try again later.",
        )
    logger.info(
        "OTP email send succeeded: user_id=%s email=%s session_token=%s",
        user.id,
        user.email,
        session_token,
    )

    return LoginInitResponse(
        session_token=session_token,
        message=f"A verification code has been sent to {request.email}",
    )


@router.post("/login/otp/verify", response_model=TokenResponse)
def login_otp_verify(request: LoginVerifyRequest, db: Session = Depends(get_db)):
    """OTP login step 2: submit session_token + 6-digit code.

    Invalidated after 5 wrong attempts or expiry.
    """
    login_code = (
        db.query(LoginCode)
        .filter(LoginCode.session_token == request.session_token)
        .first()
    )

    if not login_code or login_code.used:
        logger.warning(
            "OTP verify rejected: invalid/used session_token=%s", request.session_token
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    now = datetime.now(UTC).replace(tzinfo=None)
    if login_code.expires_at < now:
        logger.warning(
            "OTP verify rejected: expired session_token=%s alumni_id=%s expires_at=%s now=%s",
            request.session_token,
            login_code.alumni_id,
            login_code.expires_at,
            now,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification code has expired",
        )

    if login_code.attempts >= OTP_MAX_ATTEMPTS:
        login_code.used = True
        db.commit()
        logger.warning(
            "OTP verify blocked: max attempts reached session_token=%s alumni_id=%s attempts=%s",
            request.session_token,
            login_code.alumni_id,
            login_code.attempts,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Please request a new code",
        )

    if login_code.code != request.code:
        login_code.attempts += 1
        db.commit()
        remaining = OTP_MAX_ATTEMPTS - login_code.attempts
        logger.warning(
            "OTP verify failed: wrong code session_token=%s alumni_id=%s attempts=%s remaining=%s",
            request.session_token,
            login_code.alumni_id,
            login_code.attempts,
            remaining,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect verification code. {remaining} attempt(s) remaining",
        )

    login_code.used = True
    db.commit()
    logger.info(
        "OTP verify succeeded: session_token=%s alumni_id=%s",
        request.session_token,
        login_code.alumni_id,
    )

    user = login_code.alumni
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "user_type": "alumni"}
    )
    return TokenResponse(access_token=access_token, token_type="bearer")
