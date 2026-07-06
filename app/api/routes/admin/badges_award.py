from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.services.badge_notifications import notify_badge_awards
from app.services.badges import ManualAwardError, manual_award


router = APIRouter()


class AwardRequest(BaseModel):
    alumni_id: str
    badge_code: str
    metadata: dict | None = None


@router.post("/badges/award", status_code=status.HTTP_201_CREATED)
async def admin_award_badge(
    body: AwardRequest,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Manually award a badge to a user.

    Used for Open Source Contributor, Suggestion Box, or one-off admin
    corrections.
    """
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    alumni = db.query(Alumni).filter(Alumni.id == body.alumni_id).first()
    if alumni is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alumni not found"
        )

    try:
        row = manual_award(
            db,
            alumni,
            body.badge_code,
            admin_id=current_user.id,
            metadata=body.metadata,
        )
    except ManualAwardError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    # Best-effort Telegram DM. Never blocks the response.
    await notify_badge_awards(db, alumni, [body.badge_code])

    return {
        "id": row.id,
        "alumni_id": alumni.id,
        "badge_code": body.badge_code,
        "awarded_at": row.awarded_at.isoformat() if row.awarded_at else None,
        "awarded_by": row.awarded_by,
        "extra": row.extra,
    }
