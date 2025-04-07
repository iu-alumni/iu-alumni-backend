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

@router.get("/owner", response_model=List[EventResponse])
async def list_owner_events(db: Session = Depends(get_db), current_user: Union[Admin, Alumni] = Depends(get_current_user)):
    """List all events owned by the current user (by access token)"""
    current_time = datetime.now()
    events = db.query(Event).filter(Event.owner_id == current_user.id).filter(Event.datetime >= current_time).order_by(Event.datetime.asc()).all()
    return events
