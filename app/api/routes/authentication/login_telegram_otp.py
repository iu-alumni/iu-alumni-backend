from datetime import UTC, datetime, timedelta
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.login_code import LoginCode
from app.models.telegram import TelegramUser
from app.models.users import Alumni
from app.schemas.auth import LoginInitResponse, TelegramLoginRequest, TelegramVerifyRequest, TokenResponse
from app.services.telegram_bot import telegram_service
from app.services.verification_service import generate_verification_code


router = APIRouter()

LOGIN_CODE_EXPIRY_MINUTES = int(os.getenv("LOGIN_CODE_EXPIRY_MINUTES", "10"))
OTP_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5


@router.post("/login/telegram/request", response_model=LoginInitResponse)
async def login_telegram_request(request: TelegramLoginRequest, db: Session = Depends(get_db)):
    """Telegram OTP login step 1: validate email, check telegram is verified, send 6-digit code via bot.

    Requires the user to have verified their Telegram account via the profile page.
    Returns a session_token for use in /login/telegram/verify.
    """
    user = db.query(Alumni).filter(Alumni.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not verified"
        )

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is banned"
        )

    if not user.is_telegram_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Telegram not verified for this account. Please verify your Telegram account via your profile settings.",
        )

    tg_user = (
        db.query(TelegramUser)
        .filter(TelegramUser.alias == user.telegram_alias)
        .first()
    )
    if not tg_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram bot not started. Please open the bot and send /start first.",
        )

    now = datetime.now(UTC).replace(tzinfo=None)

    recent = (
        db.query(LoginCode)
        .filter(LoginCode.alumni_id == user.id, LoginCode.used.is_(False))
        .order_by(LoginCode.created_at.desc())
        .first()
    )
    if recent and (now - recent.created_at) < timedelta(seconds=OTP_COOLDOWN_SECONDS):
        seconds_left = OTP_COOLDOWN_SECONDS - int((now - recent.created_at).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {seconds_left} seconds before requesting a new code",
        )

    db.query(LoginCode).filter(
        LoginCode.alumni_id == user.id, LoginCode.used.is_(False)
    ).delete()

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

    sent = await telegram_service.send_login_code(
        chat_id=tg_user.chat_id,
        first_name=user.first_name,
        code=code,
        expiry_minutes=LOGIN_CODE_EXPIRY_MINUTES,
    )

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send Telegram code. Please try again later.",
        )

    return LoginInitResponse(
        session_token=session_token,
        message="A verification code has been sent to your Telegram account",
    )


@router.post("/login/telegram/verify", response_model=TokenResponse)
def login_telegram_verify(request: TelegramVerifyRequest, db: Session = Depends(get_db)):
    """Telegram OTP login step 2: submit session_token + 6-digit code."""
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

    now = datetime.now(UTC).replace(tzinfo=None)
    if login_code.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification code has expired",
        )

    if login_code.attempts >= OTP_MAX_ATTEMPTS:
        login_code.used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Please request a new code",
        )

    if login_code.code != request.code:
        login_code.attempts += 1
        db.commit()
        remaining = OTP_MAX_ATTEMPTS - login_code.attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect verification code. {remaining} attempt(s) remaining",
        )

    login_code.used = True
    db.commit()

    user = login_code.alumni
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "user_type": "alumni"}
    )
    return TokenResponse(access_token=access_token, token_type="bearer")
