from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.schemas.event import Event as EventResponse


router = APIRouter()


@router.get("/owner", response_model=list[EventResponse])
async def list_owner_events(
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """List all events owned by the current user (by access token)"""
    events = (
        db.query(Event)
        .filter(Event.approved != None)
        .filter(Event.owner_id == current_user.id)
        .order_by(Event.datetime.desc())
        .all()
    )
    return events


@router.get("/owner/pending", response_model=list[EventResponse])
async def list_owner_pending_events(
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """List all pending events owned by the current user (by access token)"""
    events = (
        db.query(Event)
        .filter(Event.approved == None)
        .filter(Event.owner_id == current_user.id)
        .order_by(Event.datetime.desc())
        .all()
    )
    return events
