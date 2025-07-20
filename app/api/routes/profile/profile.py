from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Alumni
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest


router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
def get_profile(
    current_user: Alumni = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get the current user's profile information.
    """
    if not isinstance(current_user, Alumni):
        raise HTTPException(
            status_code=403, detail="Your account is not an alumni account"
        )
    return current_user


@router.put("/me", response_model=ProfileResponse)
def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: Alumni = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the current user's profile information.
    """
    if not isinstance(current_user, Alumni):
        raise HTTPException(
            status_code=403, detail="Your account is not an alumni account"
        )
    # Update fields if provided
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name

    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name

    if profile_data.graduation_year is not None:
        current_user.graduation_year = profile_data.graduation_year

    if profile_data.location is not None:
        current_user.location = profile_data.location

    if profile_data.show_location is not None:
        current_user.show_location = profile_data.show_location

    if profile_data.biography is not None:
        current_user.biography = profile_data.biography

    if profile_data.telegram_alias is not None:
        current_user.telegram_alias = profile_data.telegram_alias

    if profile_data.avatar is not None:
        current_user.avatar = profile_data.avatar

    db.commit()
    db.refresh(current_user)

    return current_user
