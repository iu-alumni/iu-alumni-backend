from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Union, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.core.security import get_current_user
from app.schemas.event import UpdateEventRequest, Event as EventResponse

router = APIRouter()

@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_data: UpdateEventRequest,
    db: Session = Depends(get_db),
    current_user: Union[Admin, Alumni] = Depends(get_current_user)
):
    """
    Update an event. Only the event owner or an admin can update an event.
    """
    # Retrieve the event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if user is authorized (event owner or admin)
    is_admin = isinstance(current_user, Admin)
    is_owner = event.owner_id == current_user.id
    
    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this event"
        )
    
    # Update fields if provided
    if event_data.title is not None:
        event.title = event_data.title
    
    if event_data.description is not None:
        event.description = event_data.description
    
    if event_data.location is not None:
        event.location = event_data.location
    
    if event_data.datetime is not None:
        event.datetime = event_data.datetime
    
    if event_data.cost is not None:
        event.cost = event_data.cost
    
    if event_data.is_online is not None:
        event.is_online = event_data.is_online
    
    if event_data.cover is not None:
        event.cover = event_data.cover
    
    # Commit changes
    db.commit()
    db.refresh(event)
    
    return event
