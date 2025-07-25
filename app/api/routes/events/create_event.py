from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_random_token
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.schemas.event import CreateEventRequest, CreateEventResponse
from app.services.settings import get_event_settings


router = APIRouter()


@router.post("/", response_model=CreateEventResponse)
async def create_event(
    event: CreateEventRequest,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    if isinstance(current_user, Admin):
        raise HTTPException(status_code=403, detail="Admins cannot create events")

    """Create a new event"""
    settings = get_event_settings(db)
    auto_approve = settings.get("auto_approve", True)

    new_event = Event(
        id=get_random_token(),
        owner_id=current_user.id,
        participants_ids=[current_user.id],
        title=event.title,
        description=event.description,
        location=event.location,
        datetime=event.datetime,
        cost=event.cost,
        is_online=event.is_online,
        cover=event.cover,
        approved=True if auto_approve else None,
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return CreateEventResponse(id=new_event.id)
