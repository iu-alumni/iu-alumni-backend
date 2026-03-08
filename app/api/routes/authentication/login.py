import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.login_code import LoginCode
from app.models.users import Admin, Alumni
from app.schemas.auth import LoginInitResponse, LoginRequest, TokenResponse
from app.services.email_service import send_login_code_email
from app.services.verification_service import generate_verification_code


router = APIRouter()

LOGIN_CODE_EXPIRY_MINUTES = int(os.getenv("LOGIN_CODE_EXPIRY_MINUTES", "10"))


@router.post("/login", response_model=LoginInitResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Step 1 of login: validate credentials and send a 6-digit code to the
    university email. Returns a session_token to be used in /login/verify.
    Admins bypass 2FA and receive a JWT directly via /login/admin.
    """
    # Check alumni users only — admins use /login/admin
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

    # Generate 2FA code and session token
    code = generate_verification_code()
    session_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        minutes=LOGIN_CODE_EXPIRY_MINUTES
    )

    # Invalidate any previous unused codes for this user
    db.query(LoginCode).filter(
        LoginCode.alumni_id == user.id, LoginCode.used.is_(False)
    ).delete()

    login_code = LoginCode(
        id=str(uuid.uuid4()),
        alumni_id=user.id,
        session_token=session_token,
        code=code,
        expires_at=expires_at,
        used=False,
    )
    db.add(login_code)
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


@router.post("/login/admin", response_model=TokenResponse)
def login_admin(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Admin login — no 2FA, returns JWT directly.
    """
    user = db.query(Admin).filter(Admin.email == request.email).first()

    if (
        not user
        or not user.hashed_password
        or not verify_password(request.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "user_type": "admin"}
    )
    return TokenResponse(access_token=access_token, token_type="bearer")
