from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.projects import Project
from app.models.users import Admin, Alumni
from app.schemas.pagination import Paginated, decode_cursor, encode_cursor
from app.schemas.project import ProjectListItem


router = APIRouter()

_STATUS_FILTERS = {
    "pending": lambda q: q.filter(Project.approved.is_(None)),
    "approved": lambda q: q.filter(Project.approved.is_(True)),
    "declined": lambda q: q.filter(Project.approved.is_(False)),
    "all": lambda q: q,
}


@router.get("/projects", response_model=Paginated[ProjectListItem])
async def admin_list_projects(
    status_filter: str = Query(
        "all",
        alias="status",
        description="pending, approved, declined, or all (default)",
    ),
    search: str | None = Query(None, description="Search by project title"),
    cursor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    if status_filter not in _STATUS_FILTERS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="status must be one of: pending, approved, declined, all",
        )

    query = _STATUS_FILTERS[status_filter](db.query(Project))
    if search:
        query = query.filter(Project.title.ilike(f"%{search}%"))
    if cursor:
        c = decode_cursor(cursor)
        query = query.filter(Project.created_at < c["dt"])

    projects = (
        query.order_by(Project.created_at.desc(), Project.id.asc())
        .limit(limit + 1)
        .all()
    )

    next_cursor = None
    if len(projects) > limit:
        last = projects[limit - 1]
        next_cursor = encode_cursor(
            {"id": last.id, "dt": last.created_at.isoformat()}
        )
        projects = projects[:limit]

    return Paginated(items=projects, next_cursor=next_cursor)
