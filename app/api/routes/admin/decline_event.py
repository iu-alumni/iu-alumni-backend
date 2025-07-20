from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni


router = APIRouter()


@router.post("/events/decline/{event_id}")
async def decline_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Decline an event"""
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=403, detail="You are not authorized to access this resource"
        )

    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Allow changing approval status even if already set
    if event.approved == False:
        raise HTTPException(status_code=400, detail="Event is already declined")

    event.approved = False
    db.commit()
    db.refresh(event)
    return event
