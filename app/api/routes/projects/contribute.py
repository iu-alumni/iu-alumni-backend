from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.projects import Project
from app.models.users import Admin, Alumni


router = APIRouter()


@router.post("/{project_id}/contributors", status_code=status.HTTP_200_OK)
async def contribute(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Mark the current user as a contributor. Approved projects only."""
    if isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins cannot contribute to projects",
        )

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.approved is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot contribute to a project that hasn't been approved yet",
        )
    if current_user.id in project.contributors_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a contributor to this project",
        )

    project.contributors_ids = [*project.contributors_ids, current_user.id]
    db.commit()
    return {"message": "Contribution recorded"}


@router.post(
    "/{project_id}/contributors/remove", status_code=status.HTTP_200_OK
)
async def retract_contribution(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Remove the current user from the contributor list."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if current_user.id not in project.contributors_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not a contributor to this project",
        )

    project.contributors_ids = [
        cid for cid in project.contributors_ids if cid != current_user.id
    ]
    db.commit()
    return {"message": "Contribution retracted"}
