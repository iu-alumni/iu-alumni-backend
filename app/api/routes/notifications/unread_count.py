from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.notification import UnreadCountResponse
from app.services.notifications import find_nearby_upcoming_events, is_read


router = APIRouter()


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """Count of currently-matching events not yet seen. Does not mark read —
    used to drive the bell icon's badge without opening the list."""
    if not isinstance(current_user, Alumni):
        return UnreadCountResponse(count=0)

    events = find_nearby_upcoming_events(db, current_user)
    count = sum(1 for e in events if not is_read(current_user, e))
    return UnreadCountResponse(count=count)
