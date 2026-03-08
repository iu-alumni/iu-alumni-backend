from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.user import AlumniListItem


router = APIRouter()


@router.get("/users", response_model=list[AlumniListItem])
def list_users(
    search: str | None = Query(None, description="Search by name or email"),
    banned: bool | None = Query(None, description="Filter by banned status"),
    verified: bool | None = Query(None, description="Filter by verified status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """
    Admin endpoint to list users with optional filters and search.

    Query parameters:
    - search: Filter by name or email (case-insensitive)
    - banned: Filter by banned status (true/false)
    - verified: Filter by verified status (true/false)
    - skip/limit: Pagination (default 0/50, max limit 100)
    """
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=403, detail="You are not authorized to list users"
        )

    query = db.query(Alumni)

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Alumni.first_name.ilike(term),
                Alumni.last_name.ilike(term),
                Alumni.email.ilike(term),
            )
        )

    if banned is not None:
        query = query.filter(Alumni.is_banned == banned)

    if verified is not None:
        query = query.filter(Alumni.is_verified == verified)

    return query.offset(skip).limit(limit).all()
