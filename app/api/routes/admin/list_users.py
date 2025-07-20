from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.user import Alumni as AlumniSchema


router = APIRouter()


@router.get("/users", response_model=list[AlumniSchema])
def list_users(
    banned: bool | None = Query(None, description="Filter by banned status"),
    verified: bool | None = Query(None, description="Filter by verified status"),
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """
    Admin endpoint to list users with optional filters

    Query parameters:
    - banned: Filter by banned status (true/false)
    - verified: Filter by verified status (true/false)

    Examples:
    - /admin/users - List all users
    - /admin/users?banned=true - List only banned users
    - /admin/users?verified=false - List only unverified users
    - /admin/users?banned=false&verified=true - List verified, non-banned users
    """
    # Check if current user is admin
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=403, detail="You are not authorized to list users"
        )

    # Build query
    query = db.query(Alumni)

    # Apply filters
    if banned is not None:
        query = query.filter(Alumni.is_banned == banned)

    if verified is not None:
        query = query.filter(Alumni.is_verified == verified)

    # Execute query and return results
    users = query.all()
    return users
