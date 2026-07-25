from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.projects import Project
from app.models.users import Admin, Alumni
from app.schemas.project import DonateRequest, Project as ProjectResponse


router = APIRouter()


@router.post("/{project_id}/donations", response_model=ProjectResponse)
async def donate(
    project_id: str,
    body: DonateRequest,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Log a self-reported donation.

    Called after the user comes back from the external payment URL and
    tells us how much they gave. Bumps `raised_amount` by the supplied
    ruble amount and also flags the user as a contributor if they weren't
    already (donating implies supporting).

    v1 is honour-based — no payment verification. Real integration lands
    with FR24-b, at which point this endpoint likely becomes a webhook
    handler instead of a user-facing action.
    """
    if isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins cannot donate to projects",
        )

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.approved is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot donate to a project that hasn't been approved yet",
        )

    # Bump the running total. amount > 0 already validated by the schema.
    project.raised_amount = (project.raised_amount or 0) + body.amount

    # Donating implies supporting — add to contributors if not there.
    if current_user.id not in (project.contributors_ids or []):
        project.contributors_ids = [
            *(project.contributors_ids or []),
            current_user.id,
        ]

    db.commit()
    db.refresh(project)
    return project
