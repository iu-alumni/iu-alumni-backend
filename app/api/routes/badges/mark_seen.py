from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Alumni
from app.schemas.badge import MarkSeenResponse
from app.services.badges import mark_seen


router = APIRouter()


@router.post("/me/{badge_code}/seen", response_model=MarkSeenResponse)
def mark_badge_seen(
    badge_code: str,
    current_user: Alumni = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a newly-earned badge as seen so the popup doesn't reappear."""
    if not isinstance(current_user, Alumni):
        raise HTTPException(
            status_code=403, detail="Your account is not an alumni account"
        )
    return MarkSeenResponse(success=mark_seen(db, current_user, badge_code))
