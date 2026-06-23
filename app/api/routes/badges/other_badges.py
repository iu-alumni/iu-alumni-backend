from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.badge import UserBadgesResponse
from app.services.badges import list_for_user


router = APIRouter()


@router.get("/users/{alumni_id}", response_model=UserBadgesResponse)
def get_user_badges(alumni_id: str, db: Session = Depends(get_db)):
    """Public view of someone else's earned badges. No auth required."""
    data = list_for_user(db, alumni_id)
    return UserBadgesResponse(earned=data["earned"])
