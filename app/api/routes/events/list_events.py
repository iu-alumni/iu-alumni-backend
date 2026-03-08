from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.schemas.event import Event as EventResponse


router = APIRouter()


@router.get("/", response_model=list[EventResponse])
async def list_events(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """List approved events with pagination."""
    events = (
        db.query(Event)
        .filter(Event.approved == True)
        .order_by(Event.datetime.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return events
