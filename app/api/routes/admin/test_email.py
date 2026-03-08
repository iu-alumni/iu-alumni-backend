import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_mail import MessageSchema, MessageType
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.services.email_service import fm


logger = logging.getLogger("iu_alumni.admin.test_email")

router = APIRouter()


class TestEmailRequest(BaseModel):
    recipient: EmailStr


@router.post("/test-email")
async def test_email(
    request: TestEmailRequest,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """
    Admin endpoint to verify SMTP configuration by sending a test email.

    Returns the actual error message if delivery fails, making it easy to
    diagnose credential or connectivity issues (e.g. missing Gmail App Password).
    """
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this endpoint",
        )

    message = MessageSchema(
        subject="IU Alumni — SMTP Test",
        recipients=[request.recipient],
        body="<p>This is a test email from the IU Alumni Platform. If you received this, SMTP is configured correctly.</p>",
        subtype=MessageType.html,
    )

    try:
        await fm.send_message(message)
        logger.info("Test email sent successfully to %s", request.recipient)
        return {"success": True, "error": None}
    except Exception as e:
        logger.exception("Test email failed for recipient %s", request.recipient)
        return {"success": False, "error": str(e)}
