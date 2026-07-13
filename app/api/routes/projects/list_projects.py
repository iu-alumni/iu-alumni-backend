from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.projects import Project
from app.models.users import Admin, Alumni
from app.schemas.pagination import Paginated, decode_cursor, encode_cursor
from app.schemas.project import ProjectListItem


router = APIRouter()


@router.get("/", response_model=Paginated[ProjectListItem])
async def list_projects(
    search: str | None = Query(None, description="Search by project title"),
    cursor: str | None = Query(None, description="Pagination cursor from previous response"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """Public list. Approved projects only, newest first, cursor-paginated."""
    query = db.query(Project).filter(Project.approved.is_(True))

    if search:
        query = query.filter(Project.title.ilike(f"%{search}%"))

    if cursor:
        c = decode_cursor(cursor)
        query = query.filter(
            or_(
                Project.created_at < c["dt"],
                and_(Project.created_at == c["dt"], Project.id > c["id"]),
            )
        )

    projects = (
        query.order_by(Project.created_at.desc(), Project.id.asc())
        .limit(limit + 1)
        .all()
    )

    next_cursor = None
    if len(projects) > limit:
        last = projects[limit - 1]
        next_cursor = encode_cursor({"id": last.id, "dt": last.created_at.isoformat()})
        projects = projects[:limit]

    return Paginated(items=projects, next_cursor=next_cursor)
