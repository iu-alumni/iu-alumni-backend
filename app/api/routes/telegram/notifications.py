"""Notification endpoints for event join and reminders."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.telegram import NotifyJoinRequest, NotifyUpcomingRequest, NotifyUserRequest
from app.services.notification_service import NotificationService

router = APIRouter()


@router.post("/notify/join")
async def notify_join(
    request: NotifyJoinRequest,
    db: Session = Depends(get_db),
):
    """Send notification when user joins an event.
    
    Args:
        event_name: Name of the event
        owner_alias: Telegram alias of event owner
        user_alias: Telegram alias of user joining
    """
    result = await NotificationService.send_join_notification(
        db, request.event_name, request.owner_alias, request.user_alias
    )

    if result.get("status") == "ok":
        return {"statusCode": 200, "body": result}
    else:
        return {"statusCode": 404, "body": result}


@router.post("/notify/upcoming")
async def notify_upcoming(
    request: NotifyUpcomingRequest,
    db: Session = Depends(get_db),
):
    """Send reminder notification for upcoming event.
    
    Args:
        event_name: Name of the event
        user_alias: Telegram alias of user
    """
    result = await NotificationService.send_upcoming_reminder(
        db, request.event_name, request.user_alias
    )

    if result.get("status") == "ok":
        return {"statusCode": 200, "body": result}
    else:
        return {"statusCode": 404, "body": result}


@router.post("/notify/user")
async def notify_user(
    request: NotifyUserRequest,
    db: Session = Depends(get_db),
):
    """Send custom notification to a user.
    
    Args:
        user_alias: Telegram alias of user
        text: Custom text message to send
        event_name: (optional) Name of related event
    """
    result = await NotificationService.send_custom_notification(
        db, request.user_alias, request.text
    )

    if result.get("status") == "ok":
        return {"statusCode": 200, "body": result}
    else:
        return {"statusCode": 404, "body": result}
