from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.services.badges import ManualAwardError, manual_revoke


router = APIRouter()


class RevokeRequest(BaseModel):
    alumni_id: str
    badge_code: str
    metadata: dict | None = None


@router.post("/badges/revoke", status_code=status.HTTP_200_OK)
async def admin_revoke_badge(
    body: RevokeRequest,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Manually revoke a badge from a user.

    No Telegram notification is sent — revocations are a corrective action,
    not something to celebrate.
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
        badge = manual_revoke(db, alumni, body.badge_code, metadata=body.metadata)
    except ManualAwardError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    return {
        "alumni_id": alumni.id,
        "badge_code": badge.code,
        "metadata": body.metadata,
    }
