from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.profile import ProfileListItem


router = APIRouter()


@router.get("/all", response_model=list[ProfileListItem])
def get_profiles(
    search: str | None = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """
    Get the list of all profiles. Supports name search and pagination.
    """
    query = db.query(Alumni)

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Alumni.first_name.ilike(term),
                Alumni.last_name.ilike(term),
            )
        )

    users = query.offset(skip).limit(limit).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users
