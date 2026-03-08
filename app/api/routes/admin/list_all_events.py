from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.schemas.event import EventListItem


router = APIRouter()


@router.get("/events", response_model=list[EventListItem])
async def list_events(
    search: str | None = Query(None, description="Search by event title"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """List all events (admin). Supports title search and pagination."""
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=403, detail="You are not authorized to access this resource"
        )

    query = db.query(Event)
    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
    events = query.order_by(Event.datetime.desc()).offset(skip).limit(limit).all()
    return events
