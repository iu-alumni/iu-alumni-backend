from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.settings import EventSettingsResponse
from app.services.settings import get_event_settings, update_auto_approve_setting


router = APIRouter()


@router.get("/settings/events", response_model=EventSettingsResponse)
async def get_event_approval_settings(
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Get event approval settings"""
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=403, detail="You are not authorized to access this resource"
        )

    settings = get_event_settings(db)
    return {"auto_approve": settings.get("auto_approve", True)}


@router.post(
    "/settings/events/toggle-auto-approve", response_model=EventSettingsResponse
)
async def toggle_auto_approve_setting(
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Toggle the auto_approve setting"""
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=403, detail="You are not authorized to access this resource"
        )

    # Get current setting
    settings = get_event_settings(db)
    current_value = settings.get("auto_approve", True)
    # Toggle the value
    updated_settings = update_auto_approve_setting(db, not current_value)
    return {"auto_approve": updated_settings.get("auto_approve", True)}
