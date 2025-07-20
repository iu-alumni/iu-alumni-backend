from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.utils.notifications import notify_join_event
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni


router = APIRouter()


@router.post("/{event_id}/participants", status_code=status.HTTP_200_OK)
async def add_participant(
    event_id: str,
    participant_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Add a participant to an event, either by themselves (by access token) or by an admin"""
    # Find the event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    if not participant_id:
        participant_id = current_user.id

    # Verify participant exists
    participant = db.query(Alumni).filter(Alumni.id == participant_id).first()
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found"
        )

    # Make sure the user is either adding themselves or is an admin
    is_admin = isinstance(current_user, Admin)
    is_self = not participant_id or current_user.id == participant_id

    if not (is_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add yourself as a participant",
        )

    # Check if participant is already added
    if participant_id in event.participants_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a participant in this event",
        )

    new_participants_ids = [*event.participants_ids, participant_id]

    event.participants_ids = new_participants_ids

    # Commit changes
    try:
        db.commit()
        db.refresh(event)

        # Get the event owner for notification
        owner = db.query(Alumni).filter(Alumni.id == event.owner_id).first()

        # Send notification if both owner and participant have telegram aliases
        if owner and owner.telegram_alias and participant.telegram_alias:
            notify_join_event(
                event_name=event.title,
                owner_alias=owner.telegram_alias,
                user_alias=participant.telegram_alias,
            )

        return {"message": "Successfully joined the event"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join event: {e!s}",
        )
