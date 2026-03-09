import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.users import Alumni
from app.schemas.auth import TokenResponse, VerifyEmailRequest
from app.services.email_service import send_verification_success_email
from app.services.verification_service import verify_by_token, verify_code

MINI_APP_URL = os.getenv("MINI_APP_URL", "")

router = APIRouter()


@router.get("/verify", response_class=HTMLResponse)
async def verify_email_link(
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Verify email via a link token (sent during registration).
    Opened in the user's browser from the email confirmation link.
    """
    success, message, alumni = verify_by_token(db, token)

    if not success:
        return HTMLResponse(
            content=_render_result_page(success=False, message=message),
            status_code=400,
        )

    background_tasks.add_task(
        send_verification_success_email, alumni.email, alumni.first_name
    )

    return HTMLResponse(
        content=_render_result_page(
            success=True,
            message=f"Your email has been verified, {alumni.first_name}! You can now log in to the IU Alumni app.",
        )
    )


@router.post("/verify", response_model=TokenResponse)
async def verify_email_code(
    request: VerifyEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Verify email with a verification code (legacy / admin-path only).
    """
    success, message = verify_code(db, request.email, request.verification_code)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    user = db.query(Alumni).filter(Alumni.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    background_tasks.add_task(
        send_verification_success_email, user.email, user.first_name
    )

    user_data = {"sub": user.email, "user_id": user.id, "user_type": "alumni"}
    access_token = create_access_token(data=user_data)

    return {"access_token": access_token, "token_type": "bearer"}


def _render_result_page(success: bool, message: str) -> str:
    color = "#40BA21" if success else "#ef4444"
    icon = "✅" if success else "❌"
    title = "Email Verified" if success else "Verification Failed"
    app_link = f'<p style="margin-top:20px"><a href="{MINI_APP_URL}" style="color:#40BA21;font-weight:600;">Open the IU Alumni App</a></p>' if success and MINI_APP_URL else ""
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
