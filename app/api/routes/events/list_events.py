from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.schemas.event import EventListItem
from app.schemas.pagination import Paginated, decode_cursor, encode_cursor


router = APIRouter()


@router.get("/", response_model=Paginated[EventListItem])
async def list_events(
    search: str | None = Query(None, description="Search by event title"),
    cursor: str | None = Query(None, description="Pagination cursor from previous response"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """List all approved events with optional title search and cursor-based pagination."""
    query = db.query(Event).filter(Event.approved == True)

    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))

    if cursor:
        c = decode_cursor(cursor)
        query = query.filter(
            or_(
                Event.datetime < c["dt"],
                and_(Event.datetime == c["dt"], Event.id > c["id"]),
            )
        )

    events = query.order_by(Event.datetime.desc(), Event.id.asc()).limit(limit + 1).all()

    next_cursor = None
    if len(events) > limit:
        last = events[limit - 1]
        next_cursor = encode_cursor({"id": last.id, "dt": last.datetime.isoformat()})
        events = events[:limit]

    return Paginated(items=events, next_cursor=next_cursor)
