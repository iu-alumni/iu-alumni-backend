from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.pagination import Paginated, decode_cursor, encode_cursor
from app.schemas.user import AlumniListItem


router = APIRouter()


@router.get("/users", response_model=Paginated[AlumniListItem])
def list_users(
    search: str | None = Query(None, description="Search by name or email"),
    banned: bool | None = Query(None, description="Filter by banned status"),
    verified: bool | None = Query(None, description="Filter by verified status"),
    cursor: str | None = Query(None, description="Pagination cursor from previous response"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """
    Admin endpoint to list users with optional filters, search, and cursor-based pagination.

    Query parameters:
    - search: Filter by name or email (case-insensitive)
    - banned: Filter by banned status (true/false)
    - verified: Filter by verified status (true/false)
    - cursor: Opaque cursor returned by previous response for pagination
    - limit: Page size (default 50, max 100)
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
