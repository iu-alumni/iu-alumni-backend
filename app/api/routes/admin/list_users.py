from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.user import Alumni as AlumniSchema


router = APIRouter()


@router.get("/users", response_model=list[AlumniSchema])
def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    banned: bool | None = Query(None, description="Filter by banned status"),
    verified: bool | None = Query(None, description="Filter by verified status"),
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """
    Admin endpoint to list users with optional filters and pagination.

    Query parameters:
    - skip: Number of records to skip (default 0)
    - limit: Max records to return (default 50, max 100)
    - banned: Filter by banned status (true/false)
    - verified: Filter by verified status (true/false)
    """
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=403, detail="You are not authorized to list users"
        )

    query = db.query(Alumni)

    if banned is not None:
        query = query.filter(Alumni.is_banned == banned)

    if verified is not None:
        query = query.filter(Alumni.is_verified == verified)

    users = query.offset(skip).limit(limit).all()
    return users
