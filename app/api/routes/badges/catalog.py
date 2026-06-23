from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.badge import Badge
from app.schemas.badge import BadgeBase


router = APIRouter()


@router.get("/", response_model=list[BadgeBase])
def get_catalog(db: Session = Depends(get_db)):
    """Public catalog of all badges. No per-user state."""
    return [
        BadgeBase(
            code=b.code,
            name=b.name,
            description=b.description,
            tier=b.tier,
            icon_key=b.icon_key,
        )
        for b in db.query(Badge).all()
    ]
