from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.events import Event
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from typing import Union
from app.schemas.event import Event as EventResponse
from typing import List
from datetime import datetime
router = APIRouter()

@router.get("/participant/{participant_id}", response_model=List[EventResponse])
async def list_participant_events(participant_id: str, db: Session = Depends(get_db)):
    """List all events that the current user is a participant of (not by access token)"""
    events = db.query(Event).filter(Event.participants_ids.any(participant_id)).order_by(Event.datetime.desc()).all()
    return events
