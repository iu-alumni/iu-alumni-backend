from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.schemas.event import EventListItem


router = APIRouter()


@router.get("/", response_model=list[EventListItem])
async def list_events(
    search: str | None = Query(None, description="Search by event title"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """List all approved events with optional title search and pagination."""
    query = db.query(Event).filter(Event.approved == True)
    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
    events = query.order_by(Event.datetime.desc()).offset(skip).limit(limit).all()
    return events
