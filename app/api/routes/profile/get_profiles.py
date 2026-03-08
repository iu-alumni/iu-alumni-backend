from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.profile import ProfileResponse


router = APIRouter()


@router.get("/all", response_model=list[ProfileResponse])
def get_profiles(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """
    Get the list of all profiles with pagination.
    """
    users = db.query(Alumni).offset(skip).limit(limit).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users
