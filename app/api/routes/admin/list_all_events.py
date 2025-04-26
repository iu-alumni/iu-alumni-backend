from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.event import Event as EventResponse
from typing import List
from app.models.events import Event
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from typing import Union

router = APIRouter()

@router.get("/events", response_model=List[EventResponse])
async def list_events(db: Session = Depends(get_db), current_user: Union[Admin, Alumni] = Depends(get_current_user)):
    """List all events"""
    if not isinstance(current_user, Admin):
        raise HTTPException(status_code=403, detail="You are not authorized to access this resource")

    events = db.query(Event).order_by(Event.datetime.desc()).all()
    return events
