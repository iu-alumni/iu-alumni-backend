"""Admin approval endpoints for projects. Mirror of the event admin flow."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.projects import Project
from app.models.users import Admin, Alumni
from app.schemas.project import Project as ProjectResponse


router = APIRouter()


def _require_admin(current_user: Admin | Alumni) -> None:
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )


@router.post("/projects/approve/{project_id}", response_model=ProjectResponse)
async def approve_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    _require_admin(current_user)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.approved is True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is already approved",
        )
    project.approved = True
    db.commit()
    db.refresh(project)
    return project


@router.post("/projects/decline/{project_id}", response_model=ProjectResponse)
async def decline_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    _require_admin(current_user)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    project.approved = False
    db.commit()
    db.refresh(project)
    return project


@router.post(
    "/projects/unapprove/{project_id}", response_model=ProjectResponse
)
async def unapprove_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Send an already-decided project back to the pending queue."""
    _require_admin(current_user)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    project.approved = None
    db.commit()
    db.refresh(project)
    return project
