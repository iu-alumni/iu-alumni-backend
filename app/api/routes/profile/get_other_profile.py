from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.users import Alumni
from app.schemas.profile import ProfileResponse

router = APIRouter()

@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile_by_id(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the profile information of a user by their ID.
    """
    user = db.query(Alumni).filter(Alumni.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=list[ProfileResponse])
def get_profiles_by_ids(
    user_ids: list[str] = Query(..., description="List of user IDs to fetch"),
    db: Session = Depends(get_db)
):
    """
    Get the profile information of multiple users by their IDs.
    """
    users = db.query(Alumni).filter(Alumni.id.in_(user_ids)).all()
    if not users:
        raise HTTPException(status_code=404, detail="Users not found")
    return users