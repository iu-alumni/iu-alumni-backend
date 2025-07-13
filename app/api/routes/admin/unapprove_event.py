from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.events import Event
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from typing import Union

router = APIRouter()

@router.post("/events/unapprove/{event_id}")
async def unapprove_event(event_id: str, db: Session = Depends(get_db), current_user: Union[Admin, Alumni] = Depends(get_current_user)):
    """Set an event back to pending (unapproved) state"""
    if not isinstance(current_user, Admin):
        raise HTTPException(status_code=403, detail="You are not authorized to access this resource")

    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Set event to pending state (None)
    event.approved = None
    db.commit()
    db.refresh(event)
    return {"message": "Event set to pending state", "event": event}