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
    type: Optional[str] = Query(None, description="Filter events by time: 'past' or 'upcoming'"),
    includeCreated: Optional[bool] = Query(False, description="Include events created by the user"),
    current_user: Union[Alumni, Admin] = Depends(get_current_user)
):
    """List all events that the current user is a participant of (not by access token)"""
    # Base query for events where user is a participant
    participant_query = db.query(Event).filter(Event.approved == True).filter(Event.participants_ids.any(participant_id))
    
    if includeCreated:
        # Query for events created by the user
        created_query = db.query(Event).filter(Event.approved == True).filter(Event.owner_id == participant_id)
        # Combine both queries using union
        query = participant_query.union(created_query)
    else:
        query = participant_query
    
    # Apply time filter if type parameter is provided
    if type == "past":
        query = query.filter(Event.datetime < datetime.now())
    elif type == "upcoming":
        query = query.filter(Event.datetime >= datetime.now())
    
    events = query.order_by(Event.datetime.desc()).all()
    return events
