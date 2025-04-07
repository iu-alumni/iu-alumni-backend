from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.event import Event as EventResponse
from typing import List
from app.models.events import Event
from datetime import datetime
router = APIRouter()

@router.get("/", response_model=List[EventResponse])
async def list_events(db: Session = Depends(get_db)):
    """List all events"""
    current_time = datetime.now()
    events = db.query(Event).filter(Event.datetime >= current_time).order_by(Event.datetime.asc()).all()
    return events
