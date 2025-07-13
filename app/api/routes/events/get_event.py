from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.events import Event
from app.models.users import Alumni, Admin
from app.schemas.event import Event as EventResponse
from app.core.security import get_current_user
from typing import Union

router = APIRouter()

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Union[Alumni, Admin] = Depends(get_current_user)
):
    """
    Get a single event by ID.
    Returns full event details including owner_id.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Only return approved events to non-authenticated users
    # For now, we return all events since authentication is optional
    # You may want to add logic here to check if user is owner/admin
    
    return event