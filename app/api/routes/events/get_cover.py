from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.schemas.event import CoverResponse


router = APIRouter()

_IMAGE_CACHE_SECONDS = 3600


@router.get("/{event_id}/cover", response_model=CoverResponse)
def get_event_cover(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """
    Get just the cover image of an event by its ID.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return JSONResponse(
        content={"cover": event.cover},
        headers={"Cache-Control": f"private, max-age={_IMAGE_CACHE_SECONDS}"},
    )
