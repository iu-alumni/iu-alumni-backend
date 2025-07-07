from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.events import Event
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from typing import Union, Optional
from app.schemas.event import Event as EventResponse
from typing import List
from datetime import datetime
router = APIRouter()

@router.get("/participant/{participant_id}", response_model=List[EventResponse])
async def list_participant_events(
    participant_id: str, 
    db: Session = Depends(get_db),
    type: Optional[str] = Query(None, description="Filter events by time: 'past' or 'upcoming'")
):
    """List all events that the current user is a participant of (not by access token)"""
    query = db.query(Event).filter(Event.approved == True).filter(Event.participants_ids.any(participant_id))
    
    # Apply time filter if type parameter is provided
    if type == "past":
        query = query.filter(Event.datetime < datetime.now())
    elif type == "upcoming":
        query = query.filter(Event.datetime >= datetime.now())
    
    events = query.order_by(Event.datetime.desc()).all()
    return events
