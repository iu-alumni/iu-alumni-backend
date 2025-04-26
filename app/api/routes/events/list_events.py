from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.event import Event as EventResponse
from typing import List
from app.models.events import Event

router = APIRouter()

@router.get("/", response_model=List[EventResponse])
async def list_events(db: Session = Depends(get_db)):
    """List all events"""
    events = db.query(Event).filter(Event.approved == True).order_by(Event.datetime.desc()).all()
    return events
