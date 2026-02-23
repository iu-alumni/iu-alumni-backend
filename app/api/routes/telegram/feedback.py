"""Feedback collection and retrieval endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.telegram import NotifyAdminsRequest
from app.services.feedback_service import FeedbackService
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/feedback")
async def get_feedback(db: Session = Depends(get_db)):
    """Get all collected feedback responses.
    
    Returns:
        List of feedback records ordered by creation date (newest first)
    """
    feedback = FeedbackService.get_all_feedback(db)
    return {"statusCode": 200, "data": feedback}


@router.post("/notify/admins")
async def notify_admins(request: NotifyAdminsRequest):
    """Send notification to admin group.
    
    Args:
        text: Message text to send to admins
    """
    result = await NotificationService.send_admin_notification(request.text)

    if result.get("status") == "ok":
        return {"statusCode": 200, "body": result}
    else:
        return {"statusCode": 502, "body": result}
