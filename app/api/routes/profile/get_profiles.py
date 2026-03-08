from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.pagination import Paginated, decode_cursor, encode_cursor
from app.schemas.profile import ProfileListItem


router = APIRouter()


@router.get("/all", response_model=Paginated[ProfileListItem])
def get_profiles(
    search: str | None = Query(None, description="Search by name"),
    cursor: str | None = Query(None, description="Pagination cursor from previous response"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """
    Get the list of all profiles. Supports name search and cursor-based pagination.
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

    if cursor:
        c = decode_cursor(cursor)
        query = query.filter(Alumni.id > c["id"])

    users = query.order_by(Alumni.id.asc()).limit(limit + 1).all()

    next_cursor = None
    if len(users) > limit:
        last = users[limit - 1]
        next_cursor = encode_cursor({"id": last.id})
        users = users[:limit]

    return Paginated(items=users, next_cursor=next_cursor)
