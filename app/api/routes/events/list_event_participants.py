from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.events import Event
from app.models.users import Alumni
from app.schemas.user import Alumni as AlumniResponse

router = APIRouter()

@router.get("/events/{event_id}/participants", response_model=List[AlumniResponse])
async def list_event_participants(
    event_id: str,
    db: Session = Depends(get_db)
):
    """List all participants of an event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    participants = db.query(Alumni).filter(Alumni.id.in_(event.participants_ids)).all()
    
    return participants
