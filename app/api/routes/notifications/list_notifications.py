from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.notification import NotificationItem
from app.schemas.pagination import Paginated
from app.services.notifications import find_nearby_upcoming_events, is_read, mark_seen


router = APIRouter()

# Bounded by design — the ~24h-wide 7-day window practically never holds
# more than a handful of events — so this is a safety cap, not real paging.
MAX_ITEMS = 200


@router.get("/", response_model=Paginated[NotificationItem])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """Lists events matching the current user right now (upcoming, near them).

    No real pagination — next_cursor is always null; the envelope is kept
    for API stability.

    Viewing this list marks every currently-matching event as read for this
    user (advances the read cursor) — an event is unread only the first
    time it's viewed after entering the ~7-day window.
    """
    if not isinstance(current_user, Alumni):
        return Paginated(items=[], next_cursor=None)

    events = find_nearby_upcoming_events(db, current_user)[:MAX_ITEMS]

    items = [
        NotificationItem(
            id=e.id,
            event_id=e.id,
            title=e.title,
            location=e.location,
            datetime=e.datetime,
            read=is_read(current_user, e),
        )
        for e in events
    ]

    mark_seen(db, current_user)

    return Paginated(items=items, next_cursor=None)
