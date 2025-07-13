from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Union

from app.core.database import get_db
from app.models.users import Alumni, Admin
from app.schemas.profile import ProfileResponse
from app.core.security import get_current_user

router = APIRouter()

@router.get("/all", response_model=list[ProfileResponse])
def get_profiles(
    db: Session = Depends(get_db),
    current_user: Union[Alumni, Admin] = Depends(get_current_user)
):
    """
    Get the list of all profiles.
    """
    users = db.query(Alumni).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users