import os
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_random_token
from app.models.telegram import TelegramUser
from app.models.telegram_verify_token import TelegramVerifyToken
from app.models.users import Alumni
from app.schemas.auth import TelegramVerifyRequestResponse
from app.services.email_service import send_telegram_verification_email


router = APIRouter()

BACKEND_URL = os.getenv("BACKEND_URL", "")
TELEGRAM_VERIFY_EXPIRY_HOURS = int(os.getenv("TELEGRAM_VERIFY_EXPIRY_HOURS", "24"))
MINI_APP_URL = os.getenv("MINI_APP_URL", "")


@router.post("/telegram/verify/request", response_model=TelegramVerifyRequestResponse)
async def telegram_verify_request(
    db: Session = Depends(get_db),
    current_user: Alumni = Depends(get_current_user),
):
    """
    Request Telegram account verification (profile page).

    Checks that:
    - User has a telegram_alias set.
    - The alias has started the bot (TelegramUser record exists).

    Sends a verification link to the user's email. When clicked, sets is_telegram_verified=True.
    """
    if not isinstance(current_user, Alumni):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only alumni accounts can verify Telegram",
        )

    if not current_user.telegram_alias:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please set a Telegram alias in your profile first",
        )

    tg_user = (
        db.query(TelegramUser)
        .filter(TelegramUser.alias == current_user.telegram_alias)
        .first()
    )
    if not tg_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Telegram bot not started. Please open @IU_Alumni_Notification_Bot "
                f"and send /start, then try again."
            ),
        )

    now = datetime.now(UTC).replace(tzinfo=None)

    # Invalidate any previous unused tokens for this user
    db.query(TelegramVerifyToken).filter(
        TelegramVerifyToken.alumni_id == current_user.id,
        TelegramVerifyToken.used.is_(False),
    ).delete()

    token = secrets.token_urlsafe(32)
    db.add(TelegramVerifyToken(
        id=get_random_token(),
        alumni_id=current_user.id,
        token=token,
        expires_at=now + timedelta(hours=TELEGRAM_VERIFY_EXPIRY_HOURS),
        used=False,
        created_at=now,
    ))
    db.commit()

    verify_url = f"{BACKEND_URL}/auth/telegram/verify?token={token}"
    email_sent = await send_telegram_verification_email(
        email=current_user.email,
        first_name=current_user.first_name,
        telegram_alias=current_user.telegram_alias,
        verify_link=verify_url,
        expiry_hours=TELEGRAM_VERIFY_EXPIRY_HOURS,
    )

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later.",
        )

    return TelegramVerifyRequestResponse(
        message="A verification link has been sent to your email. Click it to confirm your Telegram account."
    )


@router.get("/telegram/verify", response_class=HTMLResponse)
def telegram_verify_confirm(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Confirm Telegram account via link (opened in browser from email).
    Sets is_telegram_verified=True on the user's account.
    """
    record = (
        db.query(TelegramVerifyToken)
        .filter(TelegramVerifyToken.token == token)
        .first()
    )

    if not record or record.used:
        return HTMLResponse(
            content=_render_page(False, "Invalid or already used verification link."),
            status_code=400,
        )

    now = datetime.now(UTC).replace(tzinfo=None)
    if record.expires_at < now:
        return HTMLResponse(
            content=_render_page(False, "This verification link has expired. Please request a new one from the app."),
            status_code=400,
        )

    user = db.query(Alumni).filter(Alumni.id == record.alumni_id).first()
    if not user:
        return HTMLResponse(
            content=_render_page(False, "User not found."),
            status_code=404,
        )

    user.is_telegram_verified = True
    record.used = True
    db.commit()

    alias = f"@{user.telegram_alias}" if user.telegram_alias else ""
    return HTMLResponse(
        content=_render_page(
            True,
            f"Telegram {alias} has been verified for your account, {user.first_name}! "
            f"You can now use Telegram to log in to IU Alumni.",
        )
    )


def _render_page(success: bool, message: str) -> str:
    color = "#2CA5E0" if success else "#ef4444"
    icon = "✅" if success else "❌"
    title = "Telegram Verified" if success else "Verification Failed"
    app_link = f'<p style="margin-top:20px"><a href="{MINI_APP_URL}" style="color:#2CA5E0;font-weight:600;">Open the IU Alumni App</a></p>' if success and MINI_APP_URL else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{title} — IU Alumni</title>
  <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
         background:#f9fafb;display:flex;align-items:center;justify-content:center;
         min-height:100vh;margin:0;padding:20px;box-sizing:border-box;}}
    .card{{background:#fff;border-radius:16px;padding:48px 40px;max-width:420px;
           width:100%;text-align:center;box-shadow:0 4px 24px rgba(0,0,0,.08);}}
    .icon{{font-size:56px;margin-bottom:16px;}}
    h1{{font-size:24px;font-weight:700;color:#111827;margin:0 0 12px;}}
    p{{color:#6b7280;font-size:15px;line-height:1.6;margin:0;}}
    .badge{{display:inline-block;margin-top:24px;padding:8px 20px;border-radius:8px;
            background:{color};color:#fff;font-weight:600;font-size:14px;}}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">{icon}</div>
    <h1>{title}</h1>
    <p>{message}</p>
    <div class="badge">IU Alumni Platform</div>
    {app_link}
  </div>
</body>
</html>"""
