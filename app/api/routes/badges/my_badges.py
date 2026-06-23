from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Alumni
from app.schemas.badge import MyBadgesResponse
from app.services.badges import evaluate_for_user, list_my_badges


router = APIRouter()


@router.get("/me", response_model=MyBadgesResponse)
def get_my_badges(
    current_user: Alumni = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Current user's earned + locked badges, with progress on locked ones."""
    if not isinstance(current_user, Alumni):
        raise HTTPException(
            status_code=403, detail="Your account is not an alumni account"
        )
    # Re-evaluate every trigger on read so the user always sees current
    # state, even if a trigger hook missed for any reason. Cheap — bounded
    # by catalog size and the per-trigger lookup is indexed.
    for trigger in (
        "profile_updated",
        "event_attended",
        "event_approved",
        "badge_awarded",
    ):
        evaluate_for_user(db, current_user, trigger)
    return list_my_badges(db, current_user)
