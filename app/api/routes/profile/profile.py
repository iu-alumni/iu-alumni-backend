from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Alumni
from app.models.enums import GraduationCourse
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest

router = APIRouter()

@router.get("/me", response_model=ProfileResponse)
def get_profile(
    current_user: Alumni = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's profile information.
    """
    
    return current_user

@router.put("/me", response_model=ProfileResponse)
def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: Alumni = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile information.
    """

    # Update fields if provided
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name
    
    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name
    
    if profile_data.course is not None:
        current_user.course = profile_data.course
    
    if profile_data.location is not None:
        current_user.location = profile_data.location
    
    if profile_data.show_location is not None:
        current_user.show_location = profile_data.show_location
    
    if profile_data.biography is not None:
        current_user.biography = profile_data.biography
    
    db.commit()
    db.refresh(current_user)
    
    return current_user
