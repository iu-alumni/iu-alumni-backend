from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.projects import Project
from app.models.users import Admin, Alumni
from app.schemas.project import Project as ProjectResponse


router = APIRouter()


@router.get("/contributed", response_model=list[ProjectResponse])
async def list_my_contributed_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Approved projects the current user has contributed to."""
    return (
        db.query(Project)
        .filter(
            Project.approved.is_(True),
            Project.contributors_ids.any(current_user.id),
        )
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/contributed/{alumni_id}", response_model=list[ProjectResponse]
)
async def list_user_contributed_projects(
    alumni_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Public view of another alumnus's contributions — approved projects only."""
    target = db.query(Alumni).filter(Alumni.id == alumni_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alumni not found"
        )
    return (
        db.query(Project)
        .filter(
            Project.approved.is_(True),
            Project.contributors_ids.any(alumni_id),
        )
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
