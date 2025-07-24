from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.utils.notifications import notify_event_deleted
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni


router = APIRouter()


@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
async def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Delete an event"""
    # Find the event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # Check if user is authorized (event owner or admin)
    is_admin = isinstance(current_user, Admin)
    is_owner = event.owner_id == current_user.id

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this event",
        )

    # Send notifications before deletion if event is approved
    if event.approved:
        event_datetime_str = event.datetime.strftime("%Y-%m-%d %H:%M")

        # Get event owner
        owner = db.query(Alumni).filter(Alumni.id == event.owner_id).first()

        # Get all users to notify (participants + owner)
        users_to_notify = (
            set(event.participants_ids) if event.participants_ids else set()
        )
        if owner:
            users_to_notify.add(owner.id)

        # Send notifications to all users
        for user_id in users_to_notify:
            user = db.query(Alumni).filter(Alumni.id == user_id).first()
            if user and user.telegram_alias:
                notify_event_deleted(
                    event_name=event.title,
                    user_alias=user.telegram_alias,
                    event_datetime=event_datetime_str,
                )

    # Delete the event
    db.query(Event).filter(Event.id == event_id).delete()
    db.commit()

    return {"message": "Event deleted successfully"}
