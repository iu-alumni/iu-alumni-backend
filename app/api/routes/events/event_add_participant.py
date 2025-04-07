from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Union

from app.core.database import get_db
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.core.security import get_current_user

router = APIRouter()

@router.post("/{event_id}/participants", status_code=status.HTTP_200_OK)
async def add_participant(
    event_id: str, 
    participant_id: str | None = None, 
    db: Session = Depends(get_db),
    current_user: Union[Admin, Alumni] = Depends(get_current_user)
):
    """Add a participant to an event, either by themselves (by access token) or by an admin"""
    # Find the event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Verify participant exists
    participant = db.query(Alumni).filter(Alumni.id == participant_id).first()
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )
    
    # Make sure the user is either adding themselves or is an admin
    is_admin = isinstance(current_user, Admin)
    is_self = not participant_id or current_user.id == participant_id
    
    if not (is_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add yourself as a participant"
        )
    
    # Check if participant is already added
    if participant_id in event.participants_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a participant in this event"
        )
    
    # Add participant ID to the list
    event.participants_ids.append(participant_id)
    
    # Commit changes
    try:
        db.commit()
        db.refresh(event)
        return {"message": "Successfully joined the event"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join event: {str(e)}"
        )