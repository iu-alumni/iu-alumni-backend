from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.schemas.event import Event as EventResponse


router = APIRouter()


@router.get("/", response_model=list[EventResponse])
async def list_events(
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """List all events"""
    events = (
        db.query(Event)
        .filter(Event.approved == True)
        .order_by(Event.datetime.desc())
        .all()
    )
    return events
